import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
marketplace = json.loads(
    (root / ".github" / "plugin" / "marketplace.json").read_text(encoding="utf-8")
)
settings = json.loads(
    (root / ".claude" / "settings.json").read_text(encoding="utf-8")
)

plugins = {plugin["name"]: plugin for plugin in marketplace["plugins"]}
for enabled_plugin in settings["enabledPlugins"]:
    plugin_name, marketplace_name = enabled_plugin.split("@", maxsplit=1)
    assert marketplace_name == marketplace["name"], (
        f"{enabled_plugin} points to the wrong marketplace"
    )
    assert plugin_name in plugins, f"{plugin_name} is not in the marketplace"
    source = plugins[plugin_name]["source"].removeprefix("./")
    assert (root / source / "plugin.json").is_file(), (
        f"Plugin manifest missing for {plugin_name}"
    )
    assert (root / source / "skills" / "marketplace-check" / "SKILL.md").is_file(), (
        f"Verification skill missing for {plugin_name}"
    )

print("Marketplace manifest, enabled plugin, and skill are consistent.")
