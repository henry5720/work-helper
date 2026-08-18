import importlib.machinery
import importlib.util
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "slack-list"
loader = importlib.machinery.SourceFileLoader("slack_list", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
slack_list = importlib.util.module_from_spec(spec)
loader.exec_module(slack_list)


class SlackListTest(unittest.TestCase):
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
        self.assertIn("1 列（全表 3 列）", errors.getvalue())

    def test_assigned_rejects_non_slack_user_id(self):
        with self.assertRaises(SystemExit), patch.object(
            slack_list, "die", side_effect=SystemExit
        ):
            slack_list.cmd_assigned(["henry"])

    @patch.object(slack_list, "print_assigned")
    @patch.object(slack_list, "my_user_id", return_value="U123")
    def test_mine_uses_local_user_id(self, my_user_id, print_assigned):
        with patch.object(sys, "argv", ["slack-list", "mine", "庫存"]):
            slack_list.cmd_mine()

        my_user_id.assert_called_once_with()
        print_assigned.assert_called_once_with("U123", "庫存")

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


if __name__ == "__main__":
    unittest.main()
