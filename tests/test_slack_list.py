import importlib.machinery
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "slack-list"
loader = importlib.machinery.SourceFileLoader("slack_list", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
slack_list = importlib.util.module_from_spec(spec)
loader.exec_module(slack_list)


class SlackListTest(unittest.TestCase):
    def add_schema(self):
        return {
            slack_list.COL_TITLE: {"id": "title-col"},
            slack_list.COL_DESCRIPTION: {"id": "description-col"},
            slack_list.COL_ASSIGNEE: {"id": "assignee-col"},
            slack_list.COL_DUE: {"id": "due-col"},
            slack_list.COL_COMPLETED: {"id": "completed-col"},
            slack_list.COL_STATUS: {
                "id": "status-col",
                "options": {"choices": [{
                    "label": slack_list.STATUS_READY,
                    "value": "ready-opt",
                }]},
            },
        }

    @patch.object(slack_list, "fetch_all")
    def test_assigned_matches_exact_user_id_and_keyword(self, fetch_all):
        fetch_all.return_value = [
            {"id": "RecA", "fields": [
                {"key": "todo_assignee", "user": ["U123", "U999"]},
                {"key": "name", "text": "庫存修正"},
            ]},
            {"id": "RecB", "fields": [
                {"key": "todo_assignee", "user": ["U1234"]},
                {"key": "name", "text": "庫存盤點"},
            ]},
            {"id": "RecC", "fields": [
                {"key": "todo_assignee", "user": ["U123"]},
                {"key": "name", "text": "帳務修正"},
            ]},
        ]

        output = io.StringIO()
        errors = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            slack_list.cmd_assigned(["U123", "庫存"])

        self.assertIn("[RecA]", output.getvalue())
        self.assertNotIn("RecB", output.getvalue())
        self.assertNotIn("RecC", output.getvalue())
        self.assertIn("1 列未完成（全表 3 列", errors.getvalue())

    def test_assigned_rejects_non_slack_user_id(self):
        with self.assertRaises(SystemExit), patch.object(
            slack_list, "die", side_effect=SystemExit
        ):
            slack_list.cmd_assigned(["henry"])

    @patch.object(slack_list, "print_assigned")
    @patch.object(slack_list, "my_user_id", return_value="U123")
    def test_mine_uses_local_user_id(self, my_user_id, print_assigned):
        slack_list.cmd_mine(["庫存"])

        my_user_id.assert_called_once_with()
        print_assigned.assert_called_once_with("U123", "庫存", False, False)

    @patch.object(slack_list, "print_assigned")
    @patch.object(slack_list, "my_user_id", return_value="U123")
    def test_mine_reads_all_as_a_flag_not_as_the_keyword(self, my_user_id, print_assigned):
        # 舊版直接拿 sys.argv[2] 當關鍵字，`mine --all 庫存` 會去比對「--all」這個字
        slack_list.cmd_mine(["--all", "庫存"])
        print_assigned.assert_called_once_with("U123", "庫存", True, False)

    def test_issue_mode_accepts_manual_and_rejects_other_values(self):
        with patch.object(slack_list, "load_env"), patch.dict(
            os.environ, {"WORK_HELPER_ISSUE_MODE": "manual"}
        ):
            self.assertEqual(slack_list.issue_mode(), "manual")

        with patch.object(slack_list, "load_env"), patch.dict(
            os.environ, {"WORK_HELPER_ISSUE_MODE": "automatic"}
        ), self.assertRaises(SystemExit), patch.object(
            slack_list, "die", side_effect=SystemExit
        ):
            slack_list.issue_mode()

    def test_record_id_for_thread_rejects_other_channel(self):
        with self.assertRaises(SystemExit), patch.object(slack_list, "die", side_effect=SystemExit):
            slack_list.record_id_for_thread("token", "F123", "C999", "1.2")

    @patch.object(slack_list, "item_threads")
    def test_record_id_for_thread_matches_parent_timestamp(self, item_threads):
        item_threads.return_value = {
            "RecA": {"ts": "1.1"},
            "RecB": {"ts": "2.2"},
        }
        self.assertEqual(
            slack_list.record_id_for_thread("token", "F123", "C123", "2.2"),
            "RecB",
        )

    @patch.object(slack_list, "thread_messages")
    @patch.object(slack_list, "fetch_all")
    @patch.object(slack_list, "record_id_for_thread")
    @patch.object(slack_list, "config")
    def test_context_outputs_record_and_non_parent_messages(
        self, config, record_id_for_thread, fetch_all, thread_messages
    ):
        config.return_value = ("token", "F123")
        record_id_for_thread.return_value = "RecA"
        fetch_all.return_value = [{
            "id": "RecA",
            "fields": [{"key": "name", "text": "測試需求"}],
        }]
        thread_messages.return_value = [
            {"subtype": "list_record_comment", "ts": "1.1"},
            {"ts": "1.2", "user": "U1", "text": "為什麼？"},
        ]

        output = io.StringIO()
        with redirect_stdout(output):
            slack_list.cmd_context(["--channel", "C123", "--thread-ts", "1.1"])

        body = json.loads(output.getvalue())
        self.assertEqual(body["record_id"], "RecA")
        self.assertEqual(body["record"]["name"], "測試需求")
        self.assertEqual(body["messages"], [{
            "ts": "1.2", "user": "U1", "bot_id": "", "text": "為什麼？", "files": []
        }])

    @patch.object(slack_list, "post_record_note", return_value=True)
    @patch.object(slack_list, "api")
    @patch.object(slack_list, "fetch_all", return_value=[])
    @patch.object(slack_list, "schema")
    @patch.object(slack_list, "config", return_value=("token", "F123"))
    def test_add_creates_title_description_due_and_self_assignment_atomically(
        self, config, schema, fetch_all, api, post_record_note
    ):
        schema.return_value = self.add_schema()
        api.return_value = {"item": {"id": "RecNew"}}

        output = io.StringIO()
        with patch.object(slack_list, "source_permalink", return_value="https://source"), \
                redirect_stdout(output):
            slack_list.cmd_add([
                "--title", "庫存匯出缺少批號",
                "--description", "匯出的 Excel 沒有批號欄",
                "--due", "2026-08-21",
                "--assignee", "U123",
                "--requested-by", "U123",
                "--report-to", "U999",
                "--source-channel", "C999",
                "--source-thread", "1.2",
            ])

        method, payload, token = api.call_args.args
        self.assertEqual(method, "slackLists.items.create")
        self.assertEqual(token, "token")
        self.assertEqual(payload["list_id"], "F123")
        by_column = {f["column_id"]: f for f in payload["initial_fields"]}
        self.assertEqual(by_column["assignee-col"]["user"], ["U123"])
        self.assertEqual(by_column["due-col"]["date"], ["2026-08-21"])
        self.assertEqual(
            by_column["title-col"]["rich_text"][0]["elements"][0]["elements"][0]["text"],
            "庫存匯出缺少批號",
        )
        self.assertEqual(
            by_column["description-col"]["rich_text"][0]["elements"][0]["elements"][0]["text"],
            "匯出的 Excel 沒有批號欄",
        )
        post_record_note.assert_called_once_with(
            "token", "F123", "RecNew", "U123", "U999", "https://source"
        )
        self.assertIn("已新增：庫存匯出缺少批號", output.getvalue())

    @patch.object(slack_list, "post_duplicate_note", return_value=True)
    @patch.object(slack_list, "api")
    @patch.object(slack_list, "fetch_all")
    @patch.object(slack_list, "schema")
    @patch.object(slack_list, "config", return_value=("token", "F123"))
    def test_add_appends_sender_to_active_exact_duplicate(
        self, config, schema, fetch_all, api, post_duplicate_note
    ):
        schema.return_value = self.add_schema()
        fetch_all.return_value = [{
            "id": "RecOld",
            "fields": [
                {"column_id": "title-col", "text": "  庫存  匯出缺少批號  "},
                {"column_id": "assignee-col", "user": ["U999"]},
                {"column_id": "completed-col", "checkbox": False},
                {"column_id": "status-col", "select": ["doing-opt"]},
            ],
        }]

        output = io.StringIO()
        with patch.object(slack_list, "source_permalink", return_value="https://source"), \
                redirect_stdout(output):
            slack_list.cmd_add([
                "--title", "庫存 匯出缺少批號",
                "--assignee", "U123",
                "--requested-by", "U123",
                "--report-to", "U456",
                "--source-channel", "C999",
                "--source-thread", "1.2",
            ])

        api.assert_called_once_with("slackLists.items.update", {
            "list_id": "F123",
            "id": "RecOld",
            "cells": [{
                "row_id": "RecOld",
                "column_id": "assignee-col",
                "user": ["U999", "U123"],
            }],
        }, "token")
        post_duplicate_note.assert_called_once_with(
            "token", "F123", "RecOld", "U123", "https://source"
        )
        self.assertIn("已加入既有待辦", output.getvalue())
        self.assertIn("未變更原回報對象", output.getvalue())

    @patch.object(slack_list, "post_duplicate_note")
    @patch.object(slack_list, "api")
    @patch.object(slack_list, "fetch_all")
    @patch.object(slack_list, "schema")
    @patch.object(slack_list, "config", return_value=("token", "F123"))
    def test_add_does_not_assign_duplicate_awaiting_pm_review(
        self, config, schema, fetch_all, api, post_duplicate_note
    ):
        schema.return_value = self.add_schema()
        fetch_all.return_value = [{
            "id": "RecReady",
            "fields": [
                {"column_id": "title-col", "text": "匯出缺欄位"},
                {"column_id": "assignee-col", "user": ["U999"]},
                {"column_id": "completed-col", "checkbox": False},
                {"column_id": "status-col", "select": ["ready-opt"]},
            ],
        }]

        output = io.StringIO()
        with patch.object(slack_list, "source_permalink", return_value="https://source"), \
                redirect_stdout(output):
            slack_list.cmd_add([
                "--title", "匯出缺欄位",
                "--assignee", "U123",
                "--requested-by", "U123",
                "--source-channel", "C999",
                "--source-thread", "1.2",
            ])

        api.assert_not_called()
        post_duplicate_note.assert_not_called()
        self.assertIn("正在 PM確認中", output.getvalue())
        self.assertIn("--force", output.getvalue())

    @patch.object(slack_list, "api")
    @patch.object(slack_list, "fetch_all", return_value=[])
    @patch.object(slack_list, "schema")
    @patch.object(slack_list, "config", return_value=("token", "F123"))
    def test_add_keeps_created_row_when_origin_note_fails(
        self, config, schema, fetch_all, api
    ):
        schema.return_value = self.add_schema()
        api.return_value = {"item": {"id": "RecNew"}}

        output = io.StringIO()
        with patch.object(slack_list, "source_permalink", return_value="https://source"), \
                patch.object(slack_list, "post_record_note", return_value=False), \
                redirect_stdout(output):
            slack_list.cmd_add([
                "--title", "匯出缺欄位",
                "--assignee", "U123",
                "--requested-by", "U123",
                "--source-channel", "C999",
                "--source-thread", "1.2",
            ])

        self.assertIn("待辦已建立", output.getvalue())
        self.assertIn("來源／回報設定失敗", output.getvalue())

    def test_add_rejects_invalid_date(self):
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.cmd_add([
                "--title", "匯出缺欄位",
                "--due", "明天",
                "--assignee", "U123",
                "--requested-by", "U123",
                "--source-channel", "C999",
                "--source-thread", "1.2",
            ])
        self.assertIn("YYYY-MM-DD", err.getvalue())

    @patch.object(slack_list, "api")
    @patch.object(slack_list, "fetch_all")
    @patch.object(slack_list, "item_threads", return_value={"RecA": {"ts": "1.2"}})
    @patch.object(slack_list, "schema")
    @patch.object(slack_list, "config", return_value=("token", "F123"))
    def test_add_from_item_thread_requires_explicit_force(
        self, config, schema, item_threads, fetch_all, api
    ):
        schema.return_value = self.add_schema()
        output = io.StringIO()
        with redirect_stdout(output):
            slack_list.cmd_add([
                "--title", "另一個匯出問題",
                "--assignee", "U123",
                "--requested-by", "U123",
                "--source-channel", "C123",
                "--source-thread", "1.2",
            ])

        fetch_all.assert_not_called()
        api.assert_not_called()
        self.assertIn("既有待辦列", output.getvalue())
        self.assertIn("--force", output.getvalue())

    def test_reporter_resolution_uses_latest_own_setting(self):
        rec = {"created_by": "UBOT"}
        messages = [
            {"user": "UBOT", "bot_id": "B1", "text":
             "[work-helper:origin:v1 sender=U123]\n"
             "[work-helper:reporter:v1 user=U123]", "blocks": [
                 {"block_id": "work_helper_origin_v1_U123"},
                 {"block_id": "work_helper_reporter_v1_user_U123"},
             ]},
            {"user": "U999", "text": "[work-helper:reporter:v1 user=U999]",
             "blocks": [{"block_id": "work_helper_reporter_v1_user_U999"}]},
            {"user": "UBOT", "bot_id": "B1", "text":
             "[work-helper:reporter:v1 user=U456]", "blocks": [
                 {"block_id": "work_helper_reporter_v1_user_U456"},
             ]},
        ]

        self.assertEqual(
            slack_list.record_reporter(rec, messages, "UBOT"), ("U456", True)
        )

    def test_reporter_resolution_can_disable_notifications(self):
        rec = {"created_by": "U123"}
        messages = [{
            "user": "UBOT", "bot_id": "B1",
            "text": "[work-helper:reporter:v1 none]",
            "blocks": [{"block_id": "work_helper_reporter_v1_none"}],
        }]
        self.assertEqual(
            slack_list.record_reporter(rec, messages, "UBOT"), ("", True)
        )

    def test_reporter_default_restores_bot_origin(self):
        rec = {"created_by": "UBOT"}
        messages = [
            {"user": "UBOT", "bot_id": "B1", "text":
             "[work-helper:origin:v1 sender=U123]\n"
             "[work-helper:reporter:v1 user=U123]", "blocks": [
                 {"block_id": "work_helper_origin_v1_U123"},
                 {"block_id": "work_helper_reporter_v1_user_U123"},
             ]},
            {"user": "UBOT", "bot_id": "B1", "text":
             "[work-helper:reporter:v1 user=U456]", "blocks": [
                 {"block_id": "work_helper_reporter_v1_user_U456"},
             ]},
            {"user": "UBOT", "bot_id": "B1", "text":
             "[work-helper:reporter:v1 default]", "blocks": [
                 {"block_id": "work_helper_reporter_v1_default"},
             ]},
        ]
        self.assertEqual(
            slack_list.record_reporter(rec, messages, "UBOT"), ("U123", True)
        )

    def test_reporter_resolution_falls_back_by_creator_kind(self):
        self.assertEqual(
            slack_list.record_reporter({"created_by": "U123"}, [], "UBOT"),
            ("U123", True),
        )
        self.assertEqual(
            slack_list.record_reporter({"created_by": "UBOT"}, [], "UBOT"),
            ("", False),
        )

    def test_reporter_resolution_ignores_marker_text_relayed_by_bot(self):
        rec = {"created_by": "U123"}
        messages = [{
            "user": "UBOT", "bot_id": "B1",
            "text": "進度：[work-helper:reporter:v1 none]",
        }]
        self.assertEqual(
            slack_list.record_reporter(rec, messages, "UBOT"), ("U123", True)
        )

    @patch.object(slack_list, "api")
    @patch.object(slack_list, "item_thread_ts", return_value="1.2")
    @patch.object(slack_list, "config", return_value=("token", "F123"))
    def test_reporter_command_posts_canonical_visible_setting(
        self, config, item_thread_ts, api
    ):
        slack_list.cmd_reporter(["RecA", "--user", "U456"])

        method, payload, token = api.call_args.args
        self.assertEqual(method, "chat.postMessage")
        self.assertEqual(token, "token")
        self.assertIn("[work-helper:reporter:v1 user=U456]", payload["text"])
        self.assertIn("<@U456>", payload["text"])
        self.assertEqual(
            payload["blocks"][0]["block_id"],
            "work_helper_reporter_v1_user_U456",
        )

    @patch.object(slack_list, "api")
    @patch.object(slack_list, "bot_user_id", return_value="UBOT")
    @patch.object(slack_list, "thread_messages", return_value=[])
    @patch.object(slack_list, "item_thread_ts", return_value="1.2")
    @patch.object(slack_list, "record")
    @patch.object(slack_list, "schema")
    @patch.object(slack_list, "config", return_value=("token", "F123"))
    def test_ready_quiet_does_not_include_reporter_mention(
        self, config, schema, record, item_thread_ts, thread_messages,
        bot_user_id, api
    ):
        schema.return_value = {
            slack_list.COL_TITLE: {"id": "title-col"},
            slack_list.COL_STATUS: {
                "id": "status-col",
                "options": {"choices": [{
                    "label": slack_list.STATUS_READY,
                    "value": "ready-opt",
                }]},
            },
            slack_list.COL_FILE: {"id": "file-col"},
        }
        record.return_value = {
            "created_by": "U123",
            "fields": [{"column_id": "title-col", "text": "庫存修正"}],
        }

        slack_list.cmd_ready([
            "RecA", "--changed", "修正匯出欄位",
            "--verify", "匯出後確認批號存在", "--no-url", "--quiet",
        ])

        post_payload = api.call_args_list[0].args[1]
        self.assertNotIn("<@U123>", json.dumps(post_payload, ensure_ascii=False))

    @patch.object(slack_list.urllib.request, "urlopen")
    def test_create_transport_failure_warns_not_to_retry(self, urlopen):
        urlopen.side_effect = slack_list.urllib.error.URLError("timeout")
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.api("slackLists.items.create", {"list_id": "F123"}, "token")
        self.assertIn("建立結果不明", err.getvalue())
        self.assertIn("勿直接重試", err.getvalue())

    @patch.object(slack_list.urllib.request, "urlopen")
    def test_create_truncated_response_warns_not_to_retry(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b"{"
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.api("slackLists.items.create", {"list_id": "F123"}, "token")
        self.assertIn("建立結果不明", err.getvalue())
        self.assertIn("勿直接重試", err.getvalue())

    @patch.object(slack_list.urllib.request, "urlopen")
    def test_api_get_truncated_response_fails_cleanly(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = b"{"
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.api_get("conversations.history", {"channel": "C123"}, "token")
        self.assertIn("Slack 回應無法讀取", err.getvalue())

    @patch.object(slack_list, "item_threads", side_effect=SystemExit)
    def test_post_note_turns_thread_lookup_failure_into_partial_success(self, item_threads):
        self.assertFalse(slack_list.post_note_with_retry(
            "token", "F123", "RecA", "來源註記"
        ))

    def test_github_issue_urls_include_fingerprint_and_title(self):
        search, create = slack_list.github_issue_urls(
            "ShuChenAI/teamsync-frontend", "Rec0ABC", "庫存修正"
        )
        self.assertIn("Rec0ABC", search)
        self.assertIn("title=", create)
        self.assertIn("ShuChenAI/teamsync-frontend", create)

    def test_github_issue_urls_reject_invalid_repo(self):
        with self.assertRaises(SystemExit), patch.object(slack_list, "die", side_effect=SystemExit):
            slack_list.github_issue_urls("https://github.com/x/y", "RecA", "title")

    @patch.object(slack_list, "api")
    @patch.object(slack_list, "upload_md")
    @patch.object(slack_list, "github_issue_urls")
    @patch.object(slack_list, "item_thread_ts")
    @patch.object(slack_list, "record")
    @patch.object(slack_list, "schema")
    @patch.object(slack_list, "config")
    def test_draft_uploads_markdown_and_posts_manual_issue_links(
        self, config, schema, record, item_thread_ts, github_issue_urls,
        upload_md, api
    ):
        config.return_value = ("token", "F123")
        schema.return_value = {slack_list.COL_TITLE: {"id": "title-col"}}
        record.return_value = {
            "fields": [{"column_id": "title-col", "text": "庫存修正"}]
        }
        item_thread_ts.return_value = "1.2"
        github_issue_urls.return_value = ("https://search", "https://create")

        slack_list.cmd_draft([
            "RecA", "--md", "/tmp/draft.md",
            "--repo", "ShuChenAI/teamsync-frontend",
            "--summary", "已釐清重現步驟",
            "--requested-by", "U123",
        ])

        upload_md.assert_called_once_with(
            "token", slack_list.comment_channel("F123"), "1.2", "/tmp/draft.md"
        )
        api.assert_called_once()
        method, payload, token = api.call_args.args
        self.assertEqual(method, "chat.postMessage")
        self.assertEqual(token, "token")
        self.assertEqual(payload["thread_ts"], "1.2")
        self.assertIn("<@U123>", payload["text"])
        self.assertIn("https://search", payload["text"])
        self.assertIn("https://create", payload["text"])
        self.assertIn("不會建立 GitHub issue", payload["text"])

    def test_check_url_rejects_non_http_scheme(self):
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.check_url("ftp://example.com")
        self.assertIn("http", err.getvalue())

    @patch.object(slack_list.urllib.request, "urlopen")
    def test_check_url_rejects_error_status(self, urlopen):
        # HEAD 跟 GET 都 4xx 才算死的。只有 HEAD 被擋的情況見下一個測試。
        urlopen.side_effect = slack_list.urllib.error.HTTPError(
            "https://gone.pages.dev", 403, "Forbidden", {}, None)
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.check_url("https://gone.pages.dev")
        self.assertIn("403", err.getvalue())
        self.assertIn("--no-url", err.getvalue())

    @patch.object(slack_list.urllib.request, "urlopen")
    def test_check_url_passes_on_200(self, urlopen):
        urlopen.return_value.__enter__.return_value.status = 200
        slack_list.check_url("https://fix-spc-update.teamsync-frontend.pages.dev")

    @patch.object(slack_list.urllib.request, "urlopen")
    def test_check_url_does_not_send_the_blocked_default_user_agent(self, urlopen):
        # urllib 預設送 Python-urllib/3.x，Cloudflare 的 bot 規則直接回 403，
        # 而分支預覽就掛在 Cloudflare Pages 上 —— 活著的網址會被判成死的。
        urlopen.return_value.__enter__.return_value.status = 200
        slack_list.check_url("https://fix-spc-update.teamsync-frontend.pages.dev")
        request = urlopen.call_args.args[0]
        self.assertNotIn("Python-urllib", request.get_header("User-agent"))

    @patch.object(slack_list.urllib.request, "urlopen")
    def test_check_url_retries_with_get_when_head_is_rejected(self, urlopen):
        def answer(request, timeout=None):
            if request.method == "HEAD":
                raise slack_list.urllib.error.HTTPError(
                    request.full_url, 403, "Forbidden", {}, None)
            response = MagicMock()
            response.__enter__.return_value.status = 200
            return response

        urlopen.side_effect = answer
        slack_list.check_url("https://fix-spc-update.teamsync-frontend.pages.dev")
        self.assertEqual(
            [c.args[0].method for c in urlopen.call_args_list], ["HEAD", "GET"])

    def write_report(self, body):
        path = Path(self.tmp.name) / "report.md"
        path.write_text(body, encoding="utf-8")
        return str(path)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    FULL_REPORT = (
        "# V01 庫存異常狀態顯示 — 驗收說明\n\n"
        "測試網址：https://fix-inventory.teamsync-frontend.pages.dev\n\n"
        "## 改了什麼\n\n- 判定基準改成可用數\n\n"
        "## 怎麼驗收\n\n1. 開庫存列表看 PMV 低庫存示範品\n\n"
        "## QA case（✅ = 程式自動測試已覆蓋）\n\n"
        "| 情境 | 自動測試 |\n|---|---|\n| 可用數低於門檻就是低庫存 | ✅ |\n"
    )

    def test_report_body_requires_every_fixed_section(self):
        path = self.write_report("## 改了什麼\n\n- a\n\n## 怎麼驗收\n\n1. b\n")
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.report_body(path)
        self.assertIn("## QA case", err.getvalue())

    def test_report_body_rejects_manual_mark_without_a_reason(self):
        # ⬜ 沒寫原因，PM 分不出那是漏測還是刻意不測
        path = self.write_report(
            self.FULL_REPORT + "| 列表四種顏色 | ⬜ |\n")
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.report_body(path)
        self.assertIn("⬜", err.getvalue())

    def test_report_body_accepts_manual_mark_with_a_reason(self):
        path = self.write_report(
            self.FULL_REPORT + "| 列表四種顏色 | ⬜ 純顏色，要人工看 |\n")
        self.assertIn("⬜ 純顏色，要人工看", slack_list.report_body(path))

    def test_report_body_drops_title_and_url_already_in_the_message(self):
        body = slack_list.report_body(self.write_report(self.FULL_REPORT))
        self.assertTrue(body.startswith("## 改了什麼"))
        self.assertNotIn("測試網址", body)
        self.assertNotIn("驗收說明", body)

    def test_report_body_warns_when_its_url_differs_from_the_flag(self):
        path = self.write_report(self.FULL_REPORT)
        with redirect_stderr(io.StringIO()) as err:
            slack_list.report_body(path, "https://other.teamsync-frontend.pages.dev")
        self.assertIn("測試網址", err.getvalue())

    @patch.object(slack_list, "api")
    @patch.object(slack_list, "bot_user_id", return_value="UBOT")
    @patch.object(slack_list, "thread_messages", return_value=[])
    @patch.object(slack_list, "item_thread_ts", return_value="1.2")
    @patch.object(slack_list, "record")
    @patch.object(slack_list, "schema")
    @patch.object(slack_list, "config", return_value=("token", "F123"))
    @patch.object(slack_list, "check_url")
    def test_ready_report_goes_out_as_one_markdown_block(
        self, check_url, config, schema, record, item_thread_ts,
        thread_messages, bot_user_id, api
    ):
        schema.return_value = self.add_schema() | {
            slack_list.COL_FILE: {"id": "file-col"}}
        record.return_value = {
            "created_by": "U123",
            "fields": [{"column_id": "title-col", "text": "庫存異常狀態顯示"}],
        }

        slack_list.cmd_ready([
            "RecA", "--report", self.write_report(self.FULL_REPORT),
            "--url", "https://fix-inventory.teamsync-frontend.pages.dev",
        ])

        blocks = api.call_args_list[0].args[1]["blocks"]
        # section 的 mrkdwn 不吃 pipe table，QA case 那張表得靠 markdown block
        markdown = [b for b in blocks if b["type"] == "markdown"]
        self.assertEqual(len(markdown), 1)
        self.assertIn("| 情境 | 自動測試 |", markdown[0]["text"])
        self.assertIn("<@U123>", blocks[0]["text"]["text"])

    def test_ready_refuses_report_and_flags_together(self):
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.cmd_ready([
                "RecA", "--report", self.write_report(self.FULL_REPORT),
                "--changed", "改了東西", "--no-url",
            ])
        self.assertIn("--changed", err.getvalue())

    def test_ready_refuses_when_neither_report_nor_flags_given(self):
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()) as err:
            slack_list.cmd_ready(["RecA", "--no-url"])
        self.assertIn("--report", err.getvalue())

    def completed_rows(self):
        return [
            {"id": "RecOpen", "fields": [
                {"key": "todo_completed", "checkbox": False},
                {"key": "name", "text": "還沒做完"},
            ]},
            {"id": "RecDone", "fields": [
                {"key": "todo_completed", "checkbox": True},
                {"key": "name", "text": "已經做完"},
            ]},
            {"id": "RecArchived", "archived": True, "fields": [
                {"key": "todo_completed", "checkbox": False},
                {"key": "name", "text": "被封存"},
            ]},
        ]

    def test_active_rows_drops_completed_and_archived(self):
        kept = slack_list.active_rows(self.completed_rows())
        self.assertEqual([r["id"] for r in kept], ["RecOpen"])

    @patch.object(slack_list, "fetch_all")
    def test_todo_defaults_to_open_rows_and_says_the_view_is_filtered(self, fetch_all):
        fetch_all.return_value = self.completed_rows()
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            slack_list.cmd_todo([])

        self.assertIn("還沒做完", output.getvalue())
        self.assertNotIn("已經做完", output.getvalue())
        # 沒有這句，agent 會把過濾後的結果當成整張表，回「PM 沒有這件事」
        self.assertIn("--all", errors.getvalue())
        self.assertIn("1 列未完成（全表 3 列", errors.getvalue())

    @patch.object(slack_list, "fetch_all")
    def test_todo_all_includes_completed_rows(self, fetch_all):
        fetch_all.return_value = self.completed_rows()
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            slack_list.cmd_todo(["--all"])

        self.assertIn("已經做完", output.getvalue())
        self.assertIn("被封存", output.getvalue())
        self.assertIn("含已完成", errors.getvalue())

    @patch.object(slack_list, "fetch_all")
    def test_json_defaults_to_open_rows(self, fetch_all):
        fetch_all.return_value = self.completed_rows()
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            slack_list.cmd_json([])

        self.assertEqual([r["_id"] for r in json.loads(output.getvalue())], ["RecOpen"])

    def test_one_line_collapses_newlines_and_truncates(self):
        self.assertEqual(slack_list.one_line("a\nb  c"), "a b c")
        self.assertEqual(slack_list.one_line("x" * 10, 4), "xxxx…")
        self.assertEqual(slack_list.one_line("x" * 4, 4), "xxxx")

    @patch.object(slack_list, "text_columns", return_value={slack_list.COL_DESCRIPTION})
    def test_format_row_truncates_text_columns_only(self, text_columns):
        assignees = " ".join(["U0B54FKJ93R"] * 12)
        line = slack_list.format_row({
            "_id": "RecA",
            slack_list.COL_DESCRIPTION: "規格\n第二行" + "字" * 300,
            slack_list.COL_ASSIGNEE: assignees,
        })

        self.assertTrue(line.startswith("[RecA] "))
        self.assertIn("規格 第二行", line)   # 換行壓成空格，一列才真的是一行
        self.assertNotIn("\n", line)
        self.assertIn("…", line)
        # user 欄不能截 —— 截一半的 U… 沒辦法拿去 --assignee，也沒辦法用眼睛比對
        self.assertIn(assignees, line)

    @patch.object(slack_list, "text_columns", return_value={slack_list.COL_DESCRIPTION})
    def test_format_row_full_keeps_the_original_text(self, text_columns):
        line = slack_list.format_row(
            {"_id": "RecA", slack_list.COL_DESCRIPTION: "規格\n第二行"}, full=True)
        self.assertIn("規格\n第二行", line)

    @patch.object(slack_list, "text_columns", return_value=set())
    def test_print_rows_columns_filter_keeps_the_record_id(self, text_columns):
        output = io.StringIO()
        with redirect_stdout(output):
            slack_list.print_rows(
                [{"_id": "RecA", slack_list.COL_TITLE: "甲",
                  slack_list.COL_DESCRIPTION: "乙"}],
                columns=[slack_list.COL_TITLE])

        self.assertEqual(output.getvalue().strip(), f"[RecA] {slack_list.COL_TITLE}: 甲")

    def test_resolve_column_rejects_an_unknown_name(self):
        with self.assertRaises(SystemExit), patch.object(
            slack_list, "die", side_effect=SystemExit
        ):
            slack_list.resolve_column("不存在", [slack_list.COL_TITLE])

    @patch.object(slack_list, "fetch_all", return_value=[])
    @patch.object(slack_list, "column_index", return_value=({}, {}))
    @patch.object(slack_list, "config", return_value=("xoxb-token", "F123"))
    def test_fields_lists_the_choices_of_select_columns(
        self, config, column_index, fetch_all
    ):
        # 不列出選項的話 --where 等於沒用：agent 不知道「狀態」能填什麼，
        # 只好先撈整張表再自己 grep 統計。
        cols = {
            slack_list.COL_STATUS: {
                "id": "status-col",
                "type": "select",
                "options": {"choices": [
                    {"label": slack_list.STATUS_READY, "value": "o1"},
                    {"label": "已完成", "value": "o2"},
                ]},
            },
            slack_list.COL_TITLE: {"id": "title-col", "type": "text"},
        }
        output = io.StringIO()
        with patch.object(slack_list, "schema", return_value=cols), \
                redirect_stdout(output), redirect_stderr(io.StringIO()):
            slack_list.cmd_fields()

        got = {e["欄位"]: e for e in json.loads(output.getvalue())}
        self.assertEqual(got[slack_list.COL_STATUS]["可填的值"],
                         [slack_list.STATUS_READY, "已完成"])
        self.assertNotIn("可填的值", got[slack_list.COL_TITLE])

    @patch.object(slack_list, "config", return_value=("xoxb-token", "F123"))
    @patch.object(slack_list, "api_get")
    def test_users_resolves_a_slack_id_back_to_a_name(self, api_get, config):
        # 表上只存 ID，列出「指派對象」之後一定會需要反查是誰。
        api_get.return_value = {
            "members": [
                {"id": "U123", "name": "henry", "profile": {"display_name": "henry"}},
                {"id": "U456", "name": "whales", "profile": {"display_name": "Whales"}},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            slack_list.cmd_users(["U456"])

        self.assertEqual(output.getvalue().strip().split("\t")[0], "U456")
        self.assertNotIn("U123", output.getvalue())

    @patch.object(slack_list, "config", return_value=("xoxb-token", "F123"))
    @patch.object(slack_list, "api_get")
    def test_users_id_match_is_exact_not_substring(self, api_get, config):
        api_get.return_value = {
            "members": [{"id": "U1234", "name": "henry", "profile": {}}],
            "response_metadata": {"next_cursor": ""},
        }
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            slack_list.cmd_users(["U123"])

        self.assertEqual(output.getvalue(), "")
        self.assertIn("已停用的帳號或 bot", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
