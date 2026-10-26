"""Prove automatic marketplace loading without exporting profiles or credentials."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request
import urllib.error


def successful_skill(events):
    starts = {
        event["data"]["toolCallId"]
        for event in events
        if event.get("type") == "tool.execution_start"
        and event.get("data", {}).get("toolName") == "skill"
        and event["data"].get("arguments", {}).get("skill") == "private-market-check"
    }
    for event in events:
        data = event.get("data", {})
        if event.get("type") != "tool.execution_complete":
            continue
        properties = data.get("toolTelemetry", {}).get("properties", {})
        plugin = data.get("toolTelemetry", {}).get("restrictedProperties", {})
        content = data.get("result", {}).get("content", "")
        if (
            data.get("toolCallId") in starts
            and data.get("success") is True
            and properties.get("found") == "true"
            and properties.get("skillSource") == "plugin"
            and plugin.get("pluginName") == "private-marker"
            and plugin.get("pluginVersion") == "1.0.0"
            and "loaded successfully" in content
            and "Skill not found" not in content
        ):
            return True
    return False


def main():
    owner = os.environ["MARKETPLACE_OWNER"]
    repo = os.environ["MARKETPLACE_REPO"]
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", value) for value in (owner, repo)):
        raise ValueError("Invalid marketplace owner or repository")
    mode = os.environ.get("AUTH_MODE", "public")
    if mode not in {"public", "native", "app"}:
        raise ValueError("Invalid AUTH_MODE")
    root = Path(os.environ["PROOF_ROOT"]).resolve()
    if root.exists():
        raise ValueError("Proof profile already exists")
    root.mkdir(mode=0o700, parents=True)
    try:
        project = root / "project"
        home = root / "home"
        project.mkdir()
        home.mkdir()
        env = dict(os.environ)
        env.update(
            HOME=str(home),
            COPILOT_HOME=str(home / ".copilot"),
            XDG_CONFIG_HOME=str(home / ".config"),
            COPILOT_AUTO_UPDATE="false",
            GIT_TERMINAL_PROMPT="0",
            GIT_CONFIG_GLOBAL="/dev/null",
            GIT_CONFIG_NOSYSTEM="1",
            CI="true",
        )
        env.pop("GIT_CONFIG_PARAMETERS", None)
        if mode == "app":
            token = env["APP_GIT_TOKEN"]
            request = urllib.request.Request(
                "https://api.github.com/installation/repositories",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                accessible = json.load(response)
            if accessible["total_count"] != 1 or [
                item["full_name"].lower() for item in accessible["repositories"]
            ] != [f"{owner}/{repo}".lower()]:
                raise ValueError("App token repository scope is not exactly the fixture")
            if accessible["repositories"][0]["private"] is not True:
                raise ValueError("App test requires a private fixture")
        env["FIXTURE_GIT_TOKEN"] = (
            env["APP_GIT_TOKEN"] if mode == "app"
            else env["COPILOT_GITHUB_TOKEN"] if mode == "native" else ""
        )
        env["FIXTURE_GIT_PATH"] = f"{owner}/{repo}".lower()
        helper = root / "credential-helper.py"
        helper.write_text(
            "import os, sys\n"
            "fields = dict(line.rstrip('\\n').split('=', 1) for line in sys.stdin if '=' in line)\n"
            "path = fields.get('path', '').lower().removesuffix('.git')\n"
            "if (sys.argv[1:] == ['get'] and fields.get('protocol') == 'https'\n"
            "    and fields.get('host') == 'github.com'\n"
            "    and path == os.environ['FIXTURE_GIT_PATH']\n"
            "    and os.environ.get('FIXTURE_GIT_TOKEN')):\n"
            "    print('username=x-access-token')\n"
            "    print('password=' + os.environ['FIXTURE_GIT_TOKEN'])\n"
        )
        env.update(
            GIT_CONFIG_COUNT="3",
            GIT_CONFIG_KEY_0="credential.helper",
            GIT_CONFIG_VALUE_0="",
            GIT_CONFIG_KEY_1="credential.useHttpPath",
            GIT_CONFIG_VALUE_1="true",
            GIT_CONFIG_KEY_2="credential.helper",
            GIT_CONFIG_VALUE_2=f"!python3 {helper}",
        )
        settings = project / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({
            "extraKnownMarketplaces": {
                "synthetic-private-market": {
                    "source": {"source": "github", "repo": f"{owner}/{repo}"}
                }
            },
            "enabledPlugins": {"private-marker@synthetic-private-market": True},
        }) + "\n")
        subprocess.run(["git", "init", "-q", str(project)], env=env, check=True)
        prompt = (
            "Invoke the private-market-check skill to verify the marketplace. "
            "Return only its verification marker. Do not read repository files "
            "or run shell commands. If that skill is unavailable, respond "
            "SKILL_UNAVAILABLE instead; do not invent a marker."
        )
        command = [
            "copilot", "-p", prompt, "--trust-folder", "--allow-tool=skill",
            "--deny-tool=shell", "--deny-tool=view", "--log-level", "warning",
            "--output-format", "json",
        ]
        result = subprocess.run(
            command, cwd=project, env=env, capture_output=True, text=True, timeout=240
        )
        plugins = subprocess.run(
            ["copilot", "plugin", "list", "--json"], cwd=project, env=env,
            capture_output=True, text=True, timeout=30,
        )
        try:
            installed = any(
                item.get("name") == "private-marker"
                and item.get("marketplace") == "synthetic-private-market"
                and item.get("source") == "installed"
                and item.get("version") == "1.0.0"
                for item in json.loads(plugins.stdout)
            )
        except (ValueError, TypeError, AttributeError):
            installed = False
        events = []
        for line in result.stdout.splitlines():
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    events.append(event)
            except json.JSONDecodeError:
                pass
        for path in home.rglob("events.jsonl"):
            for line in path.read_text().splitlines():
                events.append(json.loads(line))
        assistant_output = "\n".join(
            event.get("data", {}).get("content", "")
            for event in events if event.get("type") == "assistant.message"
        )
        skill_enabled = any(
            skill.get("name") == "private-market-check"
            and skill.get("source") == "plugin"
            and skill.get("enabled") is True
            and "/installed-plugins/synthetic-private-market/private-marker/"
            in skill.get("path", "").replace("\\", "/")
            and Path(skill.get("path", "")).is_relative_to(home)
            for event in events if event.get("type") == "session.skills_loaded"
            for skill in event.get("data", {}).get("skills", [])
        )
        report = {
            "mode": mode,
            "session_registration_diagnostics": [
                {
                    "plugin_source": skill.get("source") == "plugin",
                    "enabled": skill.get("enabled") is True,
                    "path_under_home": Path(skill.get("path", "")).is_relative_to(home),
                    "path_under_profile": Path(skill.get("path", "")).is_relative_to(Path(env["COPILOT_HOME"])),
                    "expected_marketplace_plugin_path": "/installed-plugins/synthetic-private-market/private-marker/"
                    in skill.get("path", "").replace("\\", "/"),
                }
                for event in events if event.get("type") == "session.skills_loaded"
                for skill in event.get("data", {}).get("skills", [])
                if skill.get("name") == "private-market-check"
            ],
            "cli_ok": result.returncode == 0,
            "automatically_installed": installed,
            "session_plugin_skill_enabled": skill_enabled,
            "successful_plugin_skill_tool": successful_skill(events),
            "marker_in_assistant_response": "PRIVATE_MARKET_SKILL_20261026_A7F3" in assistant_output,
        }
        report["automatic_success"] = all(
            report[key] for key in (
                "cli_ok", "automatically_installed", "session_plugin_skill_enabled",
                "successful_plugin_skill_tool", "marker_in_assistant_response",
            )
        )
        output = json.dumps(report, indent=2)
        print(output)
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write("## Automatic marketplace proof\n```json\n" + output + "\n```\n")
        return 0 if report["automatic_success"] else 1
    finally:
        shutil.rmtree(root)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as error:
        print(f"App scope API failed: HTTP {error.code}; check installation and permission scope.", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Proof timed out; CLI or plugin-list did not finish within its limit.", file=sys.stderr)
        sys.exit(1)
    except (ValueError, KeyError) as error:
        known = {
            "Invalid marketplace owner or repository",
            "Invalid AUTH_MODE",
            "Proof profile already exists",
            "App token repository scope is not exactly the fixture",
            "App test requires a private fixture",
        }
        message = str(error) if str(error) in known else "Invalid or missing proof configuration or JSON evidence"
        print(message, file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        print(f"Proof blocked or failed ({type(error).__name__}); raw logs not exported.", file=sys.stderr)
        sys.exit(1)
