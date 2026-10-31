import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser(description="Vul de echte GitHub-repository in voor HACS.")
parser.add_argument("repository", help="GitHub-eigenaar/repository")
arguments = parser.parse_args()
if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", arguments.repository):
    parser.error("Gebruik eigenaar/repository, zonder URL.")
root = Path(__file__).resolve().parent
manifest_path = root / "custom_components/talento_smart_ble/manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["documentation"] = f"https://github.com/{arguments.repository}"
manifest["issue_tracker"] = f"https://github.com/{arguments.repository}/issues"
manifest["codeowners"] = ["@" + arguments.repository.split("/")[0]]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("Repositorygegevens bijgewerkt; er is niets geüpload.")
