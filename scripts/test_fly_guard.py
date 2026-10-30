"""Exercise hook decisions with synthetic inputs; never run Fly commands."""

import importlib.util
import io
import json
import os
import subprocess
import tempfile
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

    def test_nested_wrappers(self):
        for command in (
            "bash -c 'fly apps destroy review-app -y'",
            "bash -c \"sh -c 'fly apps destroy review-app -y'\"",
            "/bin/bash -lc 'fly volumes destroy review-volume -a review-app'",
            "sh -ec 'fly status; fly machines stop machine-id -a review-app'",
            "timeout 30 fly apps destroy review-app -y",
            "timeout --signal TERM --kill-after=2s 30s fly apps destroy review-app -y",
            "gtimeout -sTERM -k2 30 fly apps destroy review-app -y",
            "env DISPLAY_LABEL=review fly apps destroy review-app -y",
            "/usr/bin/env -i -u DISPLAY_LABEL -- env DISPLAY_LABEL=review fly app rm review-app -y",
            "env --chdir=/tmp timeout --foreground 1m bash -lc 'sprite destroy -s review --force'",
            "command -p env DISPLAY_LABEL=review exec -a cli fly apps destroy review-app -y",
        ):
            with self.subTest(command=command):
                output = self.bash_output(command)
                self.assert_asks(output)
                self.assertNotIn("review-app", output)

    def test_safe_wrapped_reads(self):
        for command in (
            "bash -c 'fly status -a review-app'",
            "timeout -k 2 30 env DISPLAY_LABEL=review fly volumes list -a review-app",
            "env -u DISPLAY_LABEL -- command -p fly machines list -a review-app",
            "command -v fly",
            "printf '%s' \"bash -c 'fly apps destroy review-app -y'\"",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.bash_output(command), "")

    def test_unresolved_wrappers_require_confirmation(self):
        for command in (
            "env -S 'fly apps destroy review-app -y'",
            "env --unknown fly apps destroy review-app -y",
            "timeout --unknown 30 fly apps destroy review-app -y",
            "timeout '$DURATION' fly apps destroy review-app -y",
            "bash review-script.sh",
            "bash -c",
            "bash --rcfile review-script.sh -c 'fly status'",
            "bash -c '$1 apps destroy review-app -y' _ fly",
            "bash -c 'if true; then fly apps destroy review-app -y; fi'",
            "bash -c 'f() { fly apps destroy review-app -y; }; f'",
            "sudo -u root fly apps destroy review-app -y",
            "env " * 20 + "fly status",
        ):
            with self.subTest(command=command):
                self.assert_asks(self.bash_output(command))

    def test_invalid_input_blocks_without_echoing_it(self):
        for payload in (
            "", "invalid review-only-marker", "[]", "{}",
            json.dumps({"tool_name": "Bash", "tool_input": []}),
            json.dumps({"tool_name": "Bash", "tool_input": {}}),
            json.dumps({"tool_name": "Bash", "tool_input": {"command": 1}}),
            json.dumps({"tool_name": "Bash", "tool_input": {"command": "fly 'review-only-marker"}}),
        ):
            with self.subTest(payload=payload):
                output, errors = io.StringIO(), io.StringIO()
                with patch("sys.stdin", io.StringIO(payload)), redirect_stdout(output), patch("sys.stderr", errors):
                    self.assertEqual(guard.main(), 2)
                self.assertEqual(output.getvalue(), "")
                self.assertIn("Fly guard failed", errors.getvalue())
                self.assertNotIn("review-only-marker", errors.getvalue())

    def test_unexpected_guard_error_blocks(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "fly status"}})
        errors = io.StringIO()
        with patch("sys.stdin", io.StringIO(payload)), patch("sys.stderr", errors), \
                patch.object(guard, "guard_bash", side_effect=RuntimeError("review-only-marker")):
            self.assertEqual(guard.main(), 2)
        self.assertNotIn("review-only-marker", errors.getvalue())

    def test_hook_launcher_success_and_failures(self):
        hooks = json.loads((GUARD_PATH.parent.parent / "hooks/hooks.json").read_text())
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "fly status"}})
        with tempfile.TemporaryDirectory() as missing_root:
            broken_root = Path(missing_root) / "broken"
            (broken_root / "scripts").mkdir(parents=True)
            (broken_root / "scripts/fly_guard.py").write_text('raise RuntimeError("review-only-marker")\n')
            for entry in hooks["hooks"]["PreToolUse"]:
                hook = entry["hooks"][0]
                self.assertEqual(hook["onFailure"], "block")
                for scenario in ("success", "missing_script", "malformed_input", "script_error"):
                    with self.subTest(matcher=entry["matcher"], scenario=scenario):
                        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(GUARD_PATH.parent.parent))
                        env.pop("GROK_PLUGIN_ROOT", None)
                        if scenario == "missing_script":
                            env["CLAUDE_PLUGIN_ROOT"] = missing_root
                        if scenario == "script_error":
                            env["CLAUDE_PLUGIN_ROOT"] = str(broken_root)
                        result = subprocess.run(
                            ["/bin/sh", "-c", hook["command"]], env=env,
                            input="review-only-marker" if scenario == "malformed_input" else payload,
                            capture_output=True, text=True,
                        )
                        self.assertEqual(result.returncode, 0 if scenario == "success" else 2)
                        self.assertEqual(result.stdout, "")
                        self.assertNotIn("review-only-marker", result.stderr)
                        if scenario != "success":
                            self.assertIn("Fly guard failed", result.stderr)

    def test_unusable_python_warns_without_overriding_permissions(self):
        hooks = json.loads((GUARD_PATH.parent.parent / "hooks/hooks.json").read_text())
        payloads = (
            {"tool_name": "Bash", "tool_input": {"command": "printf review-only-marker"}},
            {"tool_name": "Bash", "tool_input": {"command": "fly apps destroy review-only-marker"}},
            {"tool_name": "mcp__plugin_fly_fly__delete_volume", "tool_input": {"volume_id": "review-only-marker"}},
        )
        with tempfile.TemporaryDirectory() as tmp:
            # No python3 on PATH at all.
            empty_path = Path(tmp) / "empty"
            empty_path.mkdir()
            # A python3 that exists but cannot run anything, like the Windows
            # Store alias stub that only offers to install Python.
            stub_path = Path(tmp) / "stub"
            stub_path.mkdir()
            stub = stub_path / "python3"
            stub.write_text('#!/bin/sh\nprintf "%s\\n" "Python was not found review-only-marker" >&2\nexit 9009\n')
            stub.chmod(0o755)
            for entry in hooks["hooks"]["PreToolUse"]:
                for root_variable in ("CLAUDE_PLUGIN_ROOT", "GROK_PLUGIN_ROOT"):
                    for search_path in (empty_path, stub_path):
                        for payload in payloads:
                            with self.subTest(matcher=entry["matcher"], root=root_variable,
                                              python=search_path.name, payload=payload):
                                env = dict(os.environ, PATH=str(search_path))
                                env.pop("CLAUDE_PLUGIN_ROOT", None)
                                env.pop("GROK_PLUGIN_ROOT", None)
                                env[root_variable] = str(GUARD_PATH.parent.parent)
                                result = subprocess.run(
                                    ["/bin/sh", "-c", entry["hooks"][0]["command"]], env=env,
                                    input=json.dumps(payload), capture_output=True, text=True,
                                )
                                self.assertEqual(result.returncode, 0)
                                self.assertEqual(result.stderr, "")
                                output = json.loads(result.stdout)
                                self.assertEqual(set(output), {"systemMessage"})
                                self.assertIn("python3 was not found on PATH or cannot run", output["systemMessage"])
                                self.assertIn("Normal client permissions still apply", output["systemMessage"])
                                self.assertNotIn("review-only-marker", result.stdout)

    def test_working_python_with_failing_guard_still_blocks(self):
        # A usable interpreter must not be mistaken for a missing one when the
        # guard itself fails: the launcher probes python3 only after a failure.
        hooks = json.loads((GUARD_PATH.parent.parent / "hooks/hooks.json").read_text())
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "fly status"}})
        with tempfile.TemporaryDirectory() as tmp:
            broken_root = Path(tmp) / "broken"
            (broken_root / "scripts").mkdir(parents=True)
            (broken_root / "scripts/fly_guard.py").write_text('raise RuntimeError("review-only-marker")\n')
            for entry in hooks["hooks"]["PreToolUse"]:
                with self.subTest(matcher=entry["matcher"]):
                    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(broken_root))
                    env.pop("GROK_PLUGIN_ROOT", None)
                    result = subprocess.run(
                        ["/bin/sh", "-c", entry["hooks"][0]["command"]], env=env,
                        input=payload, capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("Fly guard failed", result.stderr)
                    self.assertNotIn("review-only-marker", result.stderr)


if __name__ == "__main__":
    unittest.main()
