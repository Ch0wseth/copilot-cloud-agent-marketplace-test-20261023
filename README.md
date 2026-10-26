# Copilot Cloud Agent Marketplace Test

Public, company-neutral sandbox for testing plugin marketplace discovery and
the repository setup used by Copilot cloud-agent sessions.

## Test fixture

- `.github/plugin/marketplace.json` publishes one minimal plugin.
- `.claude/settings.json` declares the marketplace and enables its plugin.
- The plugin provides a distinctive verification phrase:
  `MARKETPLACE_FIXTURE_LOADED: 7F2A9C`.
- GitHub Actions validates the manifest, plugin, and skill files. The
  `copilot-setup-steps.yml` workflow runs the same check before cloud-agent
  sessions.

## What this can verify

This public repository can verify marketplace discovery and installation when
the marketplace is publicly accessible. It cannot reproduce access to an
internal/private marketplace; that requires a private test marketplace and
the same organization permissions as the target cloud-agent environment.

After enabling Copilot cloud agent for this repository, start a cloud-agent
session and ask it to report the marketplace verification phrase. Compare the
result with a session using the Actions-based setup path. A missing phrase
alone does not establish whether a plugin was loaded; the validation workflow
only checks repository files and does not itself prove cloud-agent plugin
installation.

## Local validation

```sh
python scripts/validate_marketplace.py
```

## Automatic `enabledPlugins` experiment

Manually dispatch **Automatic enabledPlugins test**
(`.github/workflows/automatic-enabled-plugins.yml`). It uses Copilot CLI
**1.0.103**, a fresh GitHub-hosted runner per configuration, and only
`GITHUB_TOKEN` with `contents: read` and `copilot-requests: write`.
There are no plugin-install or marketplace-add commands in this experiment.
The older **Actions marketplace smoke test** explicitly installs the plugin,
so its success does **not** demonstrate automatic installation.

The exact same `.claude/settings.json` content is tested at three scopes:

| Scope | Configuration location |
| --- | --- |
| `repository` | Fresh git repository `.claude/settings.json` |
| `user-copilot` | Isolated `$COPILOT_HOME/settings.json` |
| `user-claude` | Isolated `$HOME/.claude/settings.json` |

Both `HOME` and `COPILOT_HOME` are isolated. The prompt runs in a new repository
containing only configuration, not this README or the plugin's skill source.
Only the `skill` tool is exposed; the prompt does not contain the expected
phrase. Verification requires a successful real skill-tool execution with the
fixture response, an installed skill file already present before enumeration,
and an enabled plugin-source skill registration in the prompt's own events.
Standalone `plugin list` and `skill list` afterward are additional diagnostics,
not the authority for the earlier prompt's effective repository scope.
Missing evidence fails the job.
Artifacts retain the public fixture response, configuration, inventory and logs
for 14 days. These CLI-in-Actions results are not proof of identical behavior in
Copilot cloud-agent sessions or any other unseen environment.

### Verified outcomes — 2026-10-26

The end-to-end experiment is **completed**, with scope-dependent results:

| Scope | Actual result on CLI 1.0.103 |
| --- | --- |
| `repository` | **PASS**: automatic installation and successful plugin skill invocation |
| `user-copilot` | **FAIL**: `Skill not found: marketplace-check`; no fixture plugin registered |
| `user-claude` | **FAIL**: `Skill not found: marketplace-check`; no fixture plugin registered |

Evidence:

- [Verified workflow revision `94cac77`](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/commit/94cac779f608f141ada281774421bfd95736bc4b)
- [Full matrix run `40289693932`](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/40289693932)
- [Successful repository-scope job](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/40289693932/job/121461585006)
- [Failed isolated Copilot-user-settings job](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/40289693932/job/121461585018)
- [Failed isolated Claude-user-settings job](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/40289693932/job/121461584844)

For the repository case, `session.skills_loaded` registers `marketplace-check`
with `source: "plugin"`, `enabled: true`, and a path beneath
`$COPILOT_HOME/installed-plugins/public-sandbox/marketplace-smoke-test/`.
The real `tool.execution_start` calls `skill` with
`{"skill":"marketplace-check"}`; its matching `tool.execution_complete` has
`success: true`, `skillSource: "plugin"`, `pluginName: "marketplace-smoke-test"`,
and `pluginVersion: "0.1.0"`. The following assistant response contains the
fixture phrase. The installed `SKILL.md` was present before enumeration.

For both user-location cases, the real skill call completes with
`success: false`, `found: "false"`, and `Skill not found: marketplace-check`.
Only the built-in `customize-cloud-agent` and `github-pr-media` skills were
loaded. Model requests and `GITHUB_TOKEN` authentication worked in all three
jobs; these failures are not authentication failures. The overall run is
intentionally red rather than hiding the two negative outcomes.

One diagnostic limitation: standalone `plugin list --json` after the successful
repository prompt reports the installed fixture as `enabled: false`, and
standalone `skill list --json` omits it. Those commands do not reflect the
effective repository-enabled skills observed in this prompt session. The
verifier therefore uses actual session registration and tool telemetry, not
those standalone flags. An earlier
[exploratory run](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/40289500603)
also invoked the repository skill successfully but exposed an overly strict
verifier assumption: the tool completion acknowledges loading, while the
phrase is returned in the subsequent assistant message.

This proves automatic loading for the trusted repository `.claude/settings.json`
and this public marketplace on this CLI version, without an explicit plugin
installation. Copying the same configuration into either tested user location
did not reproduce it. This does not establish support for all user settings
formats, private marketplaces, or the separate cloud-agent product.
