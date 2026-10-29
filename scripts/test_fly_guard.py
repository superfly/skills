"""Exercise hook decisions with synthetic inputs; never run Fly commands."""

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch


GUARD_PATH = Path(__file__).resolve().parents[1] / "plugins/fly/scripts/fly_guard.py"
spec = importlib.util.spec_from_file_location("fly_guard", GUARD_PATH)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class FlyGuardTests(unittest.TestCase):
    def bash_output(self, command):
        output = io.StringIO()
        with redirect_stdout(output):
            guard.guard_bash({"command": command})
        return output.getvalue()

    def assert_asks(self, output):
        result = json.loads(output)["hookSpecificOutput"]
        self.assertEqual(result["hookEventName"], "PreToolUse")
        self.assertEqual(result["permissionDecision"], "ask")

    def test_command_separators(self):
        for separator in ("\n", "\r\n", ";", "&&", "||", "|", "&"):
            with self.subTest(separator=separator):
                self.assert_asks(self.bash_output(
                    f"fly status -a review-app{separator}fly apps destroy review-app -y"
                ))

    def test_comments_and_line_continuations(self):
        for command in (
            "fly status # inspect first\nfly apps destroy review-app -y",
            "# inspect first\nfly apps destroy review-app -y",
            "fly apps \\\ndestroy review-app -y",
            "fly status\\\n -a review-app\nfly apps destroy review-app -y",
        ):
            with self.subTest(command=command):
                self.assert_asks(self.bash_output(command))

    def test_quoted_or_escaped_commands_are_not_executed(self):
        for command in (
            "printf '%s' 'notes\nfly apps destroy review-app -y'",
            'printf "%s" "notes;fly apps destroy review-app -y"',
            "printf '%s' 'notes&&fly apps destroy review-app -y'",
            "printf '%s' notes\\;fly apps destroy review-app -y",
            "echo safe # fly apps destroy review-app -y",
            "echo 'literal\\'\nfly status -a review-app",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_output(command), "")

    def test_command_after_quoted_separator_is_still_checked(self):
        self.assert_asks(self.bash_output(
            "printf '%s' 'notes;with\nseparators'\nfly apps destroy review-app -y"
        ))

    def test_destructive_aliases(self):
        for group in ("machine", "machines", "m"):
            for action in ("destroy", "remove", "rm", "stop", "restart", "suspend"):
                with self.subTest(group=group, action=action):
                    self.assert_asks(self.bash_output(
                        f"fly {group} {action} machine-id -a review-app"
                    ))
        for group in ("volumes", "volume", "vol", "v"):
            for action in ("destroy", "delete", "rm", "extend", "create"):
                with self.subTest(group=group, action=action):
                    self.assert_asks(self.bash_output(
                        f"flyctl -a review-app {group} {action} review-volume"
                    ))
        for command in (
            "fly app rm review-app -y",
            "fly mpg remove review-cluster -y",
            "fly pg restart -a review-app",
            "fly tigris destroy review-bucket",
            "fly certs delete example.com -a review-app",
            "fly ip release review-address -a review-app",
            "fly wg reset review-org",
            "fly img update -a review-app",
            "fly ext storage destroy review-bucket",
        ):
            with self.subTest(command=command):
                self.assert_asks(self.bash_output(command))

    def test_machine_execution(self):
        for command in (
            "fly machine exec machine-id 'rm -rf /data' -a review-app",
            "fly machines exec machine-id 'uname -a' -a review-app",
            "flyctl m exec machine-id 'uname -a' -a review-app",
            "fly ssh console -a review-app -C 'uname -a'",
            "fly ssh console -a review-app",
        ):
            with self.subTest(command=command):
                self.assert_asks(self.bash_output(command))

    def test_existing_decisions(self):
        for command in (
            "fly apps destroy review-app -y",
            "git status && fly volumes destroy review-volume -a review-app",
            "sprite destroy -s review-sprite --force",
        ):
            with self.subTest(command=command):
                self.assert_asks(self.bash_output(command))
        for command in (
            "fly status -a review-app --json",
            "fly deploy",
            "fly machines list -a review-app",
            "fly volume list -a review-app",
            "fly app list",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_output(command), "")

    def test_main_mcp_dispatch(self):
        for tool, asks in (
            ("mcp__plugin_fly_fly__delete_app", True),
            ("mcp__plugin_fly_fly__checkpoint_restore", True),
            ("mcp__plugin_fly_fly__list_apps", False),
            ("mcp__other__delete_app", False),
        ):
            with self.subTest(tool=tool):
                payload = json.dumps({"tool_name": tool, "tool_input": {}})
                output = io.StringIO()
                with patch("sys.stdin", io.StringIO(payload)), redirect_stdout(output):
                    self.assertEqual(guard.main(), 0)
                if asks:
                    self.assert_asks(output.getvalue())
                else:
                    self.assertEqual(output.getvalue(), "")

    def test_confirmation_omits_arguments(self):
        # A non-sensitive marker checks redaction without a credential fixture.
        marker = "review-only-display-label"
        output = self.bash_output(f"fly secrets set DISPLAY_LABEL={marker} -a review-app")
        self.assert_asks(output)
        self.assertNotIn(marker, output)
        self.assertNotIn("review-app", output)


if __name__ == "__main__":
    unittest.main()
