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
