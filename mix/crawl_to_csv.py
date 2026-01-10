import json
import csv

IN_PATH = "site.jsonl"
OUT_PATH = "site_full.csv"

with open(IN_PATH, "r", encoding="utf-8") as f_in, \
     open(OUT_PATH, "w", encoding="utf-8-sig", newline="") as f_out:

    writer = csv.DictWriter(f_out, fieldnames=["url", "title", "content"])
    writer.writeheader()

    for line in f_in:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)

        writer.writerow({
            "url": obj.get("source_url", ""),
            "title": obj.get("title", ""),
            "content": obj.get("content", "")
        })

print(f"✅ Saved: {OUT_PATH}")
