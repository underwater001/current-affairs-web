#!/usr/bin/env python3
"""Validate the Current Affairs Web data and rebuild the derived files.

Run from the repo root after every edit:   python3 tools/build.py

Checks
  - every node's parent exists ("hub" for junctions) and every link points to a real node
  - junctions carry `short` and `hue`
  - every fact points to a real node, has CGL/UPSC tags and a unique id
Writes
  - data/index.json        list of month files + totals (the page reads this first)
  - exports/nodes.csv      the topic structure, for spreadsheets
  - exports/facts.csv      every fact, for spreadsheets
Exits non-zero (and writes nothing) if validation fails.
"""
import csv, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load(path):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


nodes = load(os.path.join(DATA, "nodes.json"))
month_files = sorted(glob.glob(os.path.join(DATA, "months", "*.json")))
months = [(os.path.splitext(os.path.basename(p))[0], load(p)) for p in month_files]

errors = []
for nid, n in nodes.items():
    p = n.get("parent")
    if p != "hub" and p not in nodes:
        errors.append(f"node {nid}: parent '{p}' does not exist")
    if p == "hub" and ("short" not in n or "hue" not in n):
        errors.append(f"junction {nid}: needs 'short' and 'hue'")
    for l in n.get("links", []):
        if l not in nodes:
            errors.append(f"node {nid}: link '{l}' does not exist")
    for k in ("label", "summary", "order", "created"):
        if k not in n:
            errors.append(f"node {nid}: missing '{k}'")

seen_fact, seen_day, total = set(), set(), 0
for m, doc in months:
    for d in doc.get("days", []):
        did = d.get("id")
        if not did or did in seen_day:
            errors.append(f"{m}: missing or duplicate day id '{did}'")
        seen_day.add(did)
        if not str(d.get("date", "")).startswith(m):
            errors.append(f"day {did}: date {d.get('date')} is not in month file {m}")
        for f in d.get("facts", []):
            total += 1
            fid = f.get("id")
            if not fid or fid in seen_fact:
                errors.append(f"day {did}: missing or duplicate fact id '{fid}'")
            seen_fact.add(fid)
            if f.get("node") not in nodes:
                errors.append(f"fact {fid}: node '{f.get('node')}' does not exist")
            tags = f.get("tags") or []
            if not tags or any(t not in ("CGL", "UPSC") for t in tags):
                errors.append(f"fact {fid}: tags must be CGL and/or UPSC, got {tags}")
            if not f.get("text"):
                errors.append(f"fact {fid}: empty text")

if errors:
    print("VALIDATION FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)

all_days = sorted((d for _, doc in months for d in doc.get("days", [])), key=lambda d: (d["date"], d["id"]))
index = {
    "updated": all_days[-1]["date"] if all_days else None,
    "months": [m for m, _ in months],
    "totals": {"nodes": len(nodes), "papers": len(all_days), "facts": total},
}
with open(os.path.join(DATA, "index.json"), "w", encoding="utf-8") as fp:
    json.dump(index, fp, ensure_ascii=False, indent=2)
    fp.write("\n")

os.makedirs(os.path.join(ROOT, "exports"), exist_ok=True)
with open(os.path.join(ROOT, "exports", "nodes.csv"), "w", newline="", encoding="utf-8") as fp:
    w = csv.writer(fp)
    w.writerow(["id", "label", "short", "parent", "order", "hue", "summary", "links", "created"])
    for nid, n in nodes.items():
        w.writerow([nid, n.get("label", ""), n.get("short", ""), n.get("parent", ""), n.get("order", ""),
                    n.get("hue", ""), n.get("summary", ""), ";".join(n.get("links", [])), n.get("created", "")])

with open(os.path.join(ROOT, "exports", "facts.csv"), "w", newline="", encoding="utf-8") as fp:
    w = csv.writer(fp)
    w.writerow(["date", "source", "fact_id", "node", "node_label", "tags", "gs", "page", "background", "text"])
    for d in all_days:
        for f in d.get("facts", []):
            w.writerow([d["date"], d.get("source", ""), f["id"], f["node"], nodes[f["node"]]["label"],
                        ";".join(f["tags"]), f.get("gs", ""), f.get("page", ""),
                        "yes" if f.get("extra") else "", f["text"]])

print(f"OK  {len(nodes)} nodes, {len(all_days)} papers, {total} facts, latest {index['updated']}")
