#!/usr/bin/env python3
import hashlib
import json
import re
import requests
from pathlib import Path
from urllib.parse import quote

SHARE = "https://nas-greenbotics.isr.uc.pt/drive/d/s/19Nbg4F76IZ5qEWUbGyWhFfmqULZf0kO/lzGW7jJopGGo_ZGmhFpz4dQizFZiahPs-P7_gYpHyaA0"
OUT = Path("/tmp/nas_download")

m = re.match(r"^(https?://[^/]+)/drive/d/s/([^/]+)/([^/?]+)", SHARE)
if not m:
    raise RuntimeError("Unexpected Synology share URL")
base, perm, sharing = m.groups()
s = requests.Session()
r = s.get(SHARE, timeout=60)
r.raise_for_status()
tokens = [c.value for c in s.cookies if c.name.startswith("drive-sharing-")]
if not tokens:
    raise RuntimeError("No Synology Drive sharing cookie received")
token = tokens[0]

shard = (
    f"{base}/drive/webapi/entry.cgi?api=SYNO.SynologyDrive.Shard&version=1&method=getjs"
    f"&permanent_link={quote(json.dumps(perm))}&sharing_link={quote(json.dumps(sharing))}"
)
js = s.get(shard, timeout=60).text
marker = "getDriveFile=function(){return "
pos = js.find(marker)
if pos < 0:
    marker = "window.getDriveFile=function(){return "
    pos = js.find(marker)
if pos < 0:
    raise RuntimeError("Cannot parse Synology root metadata")
start = pos + len(marker)
depth = 0
in_string = False
escaped = False
end = None
for i, ch in enumerate(js[start:], start):
    if in_string:
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"':
            in_string = False
        continue
    if ch == '"':
        in_string = True
    elif ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            end = i + 1
            break
if end is None:
    raise RuntimeError("Malformed Synology root metadata")
root = json.loads(js[start:end])
endpoint = f"{base}/drive/webapi/entry.cgi"

def listdir(file_id):
    params = {
        "api": "SYNO.SynologyDrive.Files",
        "method": "list",
        "version": "2",
        "path": f"id:{file_id}",
        "offset": 0,
        "limit": 1000,
        "sharing_token": json.dumps(token),
    }
    rr = s.get(endpoint, params=params, timeout=60)
    rr.raise_for_status()
    obj = rr.json()
    if not obj.get("success"):
        raise RuntimeError(obj)
    return (obj.get("data") or {}).get("items") or []

files = []
def walk(item, prefix=Path()):
    rel = prefix / item["name"]
    if item.get("type") == "dir" or item.get("content_type") == "dir":
        for child in listdir(item["file_id"]):
            walk(child, rel)
    else:
        files.append((rel, item))

for child in listdir(root["file_id"]):
    walk(child)

wanted = [x for x in files if x[0].parts and x[0].parts[0].startswith("rosbag2_2026_08_07-21_")]
mcaps = [x for x in wanted if x[0].suffix.lower() == ".mcap"]
if len(mcaps) != 3:
    raise RuntimeError(f"Expected exactly 3 MCAP files, found {len(mcaps)}")

OUT.mkdir(parents=True, exist_ok=True)
manifest = []

def download(rel, item):
    dst = OUT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    url = f"{base}/drive/d/s/{perm}/webapi/entry.cgi/{quote(item['name'])}"
    params = {
        "api": "SYNO.SynologyDrive.Files",
        "method": "download",
        "version": "2",
        "download_type": json.dumps("download"),
        "files": json.dumps([f"id:{item['file_id']}"]),
        "force_download": "true",
        "json_error": "true",
        "sharing_token": json.dumps(token),
    }
    sha = hashlib.sha256()
    total = 0
    with s.get(url, params=params, stream=True, timeout=(60, 300)) as rr:
        rr.raise_for_status()
        if "application/json" in rr.headers.get("content-type", "").lower():
            raise RuntimeError(rr.text[:2000])
        with dst.open("wb") as f:
            for chunk in rr.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)
                    sha.update(chunk)
                    total += len(chunk)
    expected = int(item.get("size", 0))
    if expected and total != expected:
        raise RuntimeError(f"Size mismatch {rel}: {total} != {expected}")
    rec = {
        "path": str(rel),
        "file_id": str(item["file_id"]),
        "expected_size": expected,
        "downloaded_size": total,
        "sha256": sha.hexdigest(),
        "synology_hash_reference": item.get("hash", ""),
    }
    manifest.append(rec)
    print(f"OK {rel}: {total} bytes sha256={rec['sha256']}")

for rel, item in wanted:
    download(rel, item)

(OUT / "download_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Downloaded {len(mcaps)} MCAP files, total advertised MCAP bytes: {sum(int(i.get('size', 0)) for _, i in mcaps)}")
