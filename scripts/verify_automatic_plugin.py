"""Verify the first prompt, not a phrase echoed from checkout or the prompt."""

import json
import pathlib
import sys

base = pathlib.Path(sys.argv[1])
evidence = base / "evidence"
assert (evidence / "prompt-exit.txt").read_text().strip() == "0", "CLI prompt failed"
events = []
for path in [evidence / "response.jsonl", *base.glob("profile/session-state/*/events.jsonl")]:
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass

starts = [
    event for event in events
    if event.get("type") == "tool.execution_start"
    and event.get("data", {}).get("toolName") == "skill"
    and "marketplace-check" in json.dumps(event.get("data", {}).get("arguments"))
]
assert starts, "No actual marketplace-check skill tool invocation in prompt events"
call_ids = {event["data"]["toolCallId"] for event in starts}
completed = [
    event for event in events
    if event.get("type") == "tool.execution_complete"
    and event.get("data", {}).get("toolCallId") in call_ids
    and event.get("data", {}).get("success") is True
]
assert completed, "Skill tool did not complete successfully"
phrase = "MARKETPLACE_FIXTURE_LOADED: 7F2A9C"
assert any(phrase in json.dumps(event) for event in completed), "Skill result lacks fixture phrase"
files = (evidence / "files-after-prompt.txt").read_text()
assert "marketplace-check/SKILL.md" in files, "No installed skill before enumeration"
assert "marketplace-smoke-test" in (evidence / "plugins-after.json").read_text(), "Plugin not registered"
assert "marketplace-check" in (evidence / "skills-after.json").read_text(), "Skill not registered"
print("PASS: automatic installation, registration and successful skill tool invocation")
