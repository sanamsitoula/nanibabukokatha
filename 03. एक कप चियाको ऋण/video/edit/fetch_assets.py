"""Download OpenArt results listed in a saved creation_list dump into local folders.

Usage: py -3 fetch_assets.py <creation_list.json> <ids.json> <out_dir> <ext>
ids.json maps segment name -> historyId. Writes <out_dir>/<segment>.<ext> and
<out_dir>/_resources.json (segment -> {id, url}) for reuse as generation references.
"""
import json
import sys
import urllib.request
from pathlib import Path


def load_items(dump_path):
    data = json.loads(Path(dump_path).read_text(encoding="utf-8"))
    return {item["historyId"]: item for item in data["items"]}


def main(dump_path, ids_path, out_dir, ext):
    items = load_items(dump_path)
    ids = json.loads(Path(ids_path).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    res_path = out / "_resources.json"
    resources = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else {}
    pending = []
    for seg, history_id in ids.items():
        item = items.get(history_id)
        if not item or not item.get("url"):
            pending.append(f"{seg}:{item.get('status') if item else 'missing'}")
            continue
        target = out / f"{seg}.{ext}"
        if not target.exists():
            req = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                target.write_bytes(resp.read())
        resources = {**resources, seg: {"id": item["id"], "url": item["url"]}}
    res_path.write_text(json.dumps(resources, indent=1), encoding="utf-8")
    print(f"have {len(resources)}/{len(ids)}; pending: {pending}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
