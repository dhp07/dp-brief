#!/usr/bin/env python3
"""Prepend a new edition (JSON file) to editions.json. Keeps newest first, caps history.
Usage: python3 update_edition.py new_edition.json [editions.json]"""
import json, sys, os
new_path = sys.argv[1]
store    = sys.argv[2] if len(sys.argv) > 2 else "editions.json"
CAP = 60
new = json.load(open(new_path, encoding="utf-8"))
eds = json.load(open(store, encoding="utf-8")) if os.path.exists(store) else []
# de-dupe by date: drop any existing edition with same date, then prepend
eds = [e for e in eds if e.get("date") != new.get("date")]
eds.insert(0, new)
eds = eds[:CAP]
json.dump(eds, open(store, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"OK: {new.get('date')} added; store now holds {len(eds)} edition(s).")
