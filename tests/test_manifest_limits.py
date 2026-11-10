"""The plugin's descriptions fit the upload limit.

Customize > Plugins > Upload plugin rejects a plugin whose description is over 500
characters, and `claude plugin validate` does not check it. This test runs from the
module and from its standalone edition, so it reads whatever `.claude-plugin/` holds.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 500


def descriptions():
    for path in sorted((ROOT / ".claude-plugin").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "description" in data:
            yield path.name, data["description"]
        meta = data.get("metadata", {}).get("description")
        if meta is not None:
            yield f"{path.name} metadata", meta
        for plugin in data.get("plugins", []):
            yield (
                f"{path.name} plugin {plugin.get('name')}",
                plugin.get("description", ""),
            )


def test_descriptions_fit_the_upload_limit():
    found = list(descriptions())
    assert found, "no description found under .claude-plugin/"
    for where, text in found:
        assert 0 < len(text) <= LIMIT, f"{where}: {len(text)} characters"
