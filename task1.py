import json
import sys
import urllib.error
import urllib.request
from urllib.parse import quote


def fetch(url):
    """Return parsed JSON, or None if the URL gives a 404."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def main(path="requirements.txt"):
    checked = 0
    missing_pkgs = 0
    missing_versions = 0
    oldest = None  # (upload_time, "name==version")

    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            checked += 1

            if "==" in line:
                name, version = line.split("==", 1)
            else:
                name, version = line, None
            name = name.strip()
            version = version.strip() if version else None

            # 1) does the package exist?
            if fetch(f"https://pypi.org/pypi/{quote(name)}/json") is None:
                missing_pkgs += 1
                continue

            # no pinned version (e.g. "flask"), nothing more to check
            if version is None:
                continue

            # 2) does that version exist?
            release = fetch(f"https://pypi.org/pypi/{quote(name)}/{quote(version)}/json")
            if release is None:
                missing_versions += 1
                continue

            # 3) upload_time of the first file listed under urls
            files = release.get("urls", [])
            if not files:
                continue
            uploaded = files[0]["upload_time"]
            if oldest is None or uploaded < oldest[0]:
                oldest = (uploaded, f"{name}=={version}")

    print(f"dependencies checked: {checked}")
    print(f"packages not on pypi: {missing_pkgs}")
    print(f"version not on pypi: {missing_versions}")
    if oldest:
        print(f"oldest pinned release: {oldest[1]}({oldest[0][:4]})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "requirements.txt")