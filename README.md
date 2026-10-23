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
shows that the plugin was not loaded in that session; the validation workflow
only checks repository files and does not itself prove cloud-agent plugin
installation.

## Local validation

```sh
python scripts/validate_marketplace.py
```
