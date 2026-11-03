#!/usr/bin/env python3
"""Validate the Current Affairs Web data and generate the public API and exports.

Run from the repo root after every edit:   python3 tools/build.py

Source of truth (edit these):
  data/nodes.json            junctions and branches, keyed by id
  data/sources.json          publications and the papers read (with optional Drive link)
  data/months/YYYY-MM.json   facts, grouped by paper, one file per month

Generated (never edit by hand):
  api/v1/index.json          entry point: totals, months, endpoint list
  api/v1/papers.json         every paper with its source details, link and fact counts
  api/v1/nodes.json          every node with path, junction, children and fact counts
  api/v1/facts/YYYY-MM.json  all facts of a month, flattened and enriched
  api/v1/papers/<id>.json    one paper with its facts
  api/v1/nodes/<id>.json     one node with the facts filed on it and its sub-branches
  api/v1/latest.json         the most recent date's papers and facts
  exports/*.csv              the same data as spreadsheets
Exits non-zero, writing nothing, if validation fails.
"""
import csv, datetime, glob, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
API = os.path.join(ROOT, "api", "v1")
SITE = "https://underwater001.github.io/current-affairs-web"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load(path):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(obj, fp, ensure_ascii=False, separators=(",", ":"))


nodes = load(os.path.join(DATA, "nodes.json"))
sources = load(os.path.join(DATA, "sources.json"))
pubs, papers = sources["publications"], sources["papers"]
months = [(os.path.splitext(os.path.basename(p))[0], load(p))
          for p in sorted(glob.glob(os.path.join(DATA, "months", "*.json")))]

# ---------------------------------------------------------------- validate
errors = []
for nid, n in nodes.items():
    if not ID_RE.match(nid):
        errors.append(f"node id '{nid}' must be lowercase letters, digits and hyphens")
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

paper_by_id = {}
for pp in papers:
    pid = pp.get("id")
    if not pid or pid in paper_by_id:
        errors.append(f"sources: missing or duplicate paper id '{pid}'")
    paper_by_id[pid] = pp
    if pp.get("publication") not in pubs:
        errors.append(f"paper {pid}: unknown publication '{pp.get('publication')}'")
    link = pp.get("link")
    if link is not None and not str(link).startswith("https://"):
        errors.append(f"paper {pid}: link must be an https URL or null")

seen_fact, seen_day, n_facts = set(), set(), 0
for m, doc in months:
    for d in doc.get("days", []):
        did = d.get("id")
        if not did or did in seen_day:
            errors.append(f"{m}: missing or duplicate paper id '{did}'")
        seen_day.add(did)
        if did not in paper_by_id:
            errors.append(f"{m}: paper '{did}' is not listed in data/sources.json")
        elif paper_by_id[did]["date"] != d.get("date"):
            errors.append(f"paper {did}: date differs between sources.json and {m}.json")
        if not str(d.get("date", "")).startswith(m):
            errors.append(f"paper {did}: date {d.get('date')} is not in month file {m}")
        for f in d.get("facts", []):
            n_facts += 1
            fid = f.get("id")
            if not fid or fid in seen_fact:
                errors.append(f"paper {did}: missing or duplicate fact id '{fid}'")
            seen_fact.add(fid)
            if f.get("node") not in nodes:
                errors.append(f"fact {fid}: node '{f.get('node')}' does not exist")
            tags = f.get("tags") or []
            if not tags or any(t not in ("CGL", "UPSC") for t in tags):
                errors.append(f"fact {fid}: tags must be CGL and/or UPSC, got {tags}")
            if not f.get("text"):
                errors.append(f"fact {fid}: empty text")
            if f.get("gs") and f["gs"] not in ("GS1", "GS2", "GS3", "GS4"):
                errors.append(f"fact {fid}: gs must be GS1-GS4")
for pid in paper_by_id:
    if pid not in seen_day:
        errors.append(f"sources: paper '{pid}' has no entry in any month file")

if errors:
    print("VALIDATION FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)

# ---------------------------------------------------------------- derive
def parent(nid):
    return nodes[nid]["parent"]

def path(nid):
    out = []
    while nid != "hub":
        out.append(nid)
        nid = parent(nid)
    return out[::-1]

children = {nid: [] for nid in nodes}
for nid, n in nodes.items():
    if n["parent"] != "hub":
        children[n["parent"]].append(nid)
for k in children:
    children[k].sort(key=lambda c: (nodes[c].get("order", 99), c))

BOLD = re.compile(r"\*\*(.+?)\*\*")
def plain(s):
    s = BOLD.sub(r"\1", s)
    return re.sub(r"(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s).,;:]|$)", r"\1\2", s)

def paper_view(pp):
    pub = pubs[pp["publication"]]
    return {"id": pp["id"], "date": pp["date"], "publication": pp["publication"], "name": pub["name"],
            "short": pub["short"], "edition": pp.get("edition"), "pages": pp.get("pages"),
            "link": pp.get("link"), "added": pp.get("added")}

flat = []          # every fact, enriched, in date order
by_month = {}
for m, doc in months:
    for d in sorted(doc.get("days", []), key=lambda x: (x["date"], x["id"])):
        pp = paper_by_id[d["id"]]
        pub = pubs[pp["publication"]]
        for f in d.get("facts", []):
            pth = path(f["node"])
            row = {"id": f["id"], "date": d["date"], "paper": d["id"], "source": pub["short"],
                   "link": pp.get("link"), "node": f["node"], "junction": pth[0], "path": pth,
                   "tags": f["tags"], "gs": f.get("gs"), "page": f.get("page"),
                   "background": bool(f.get("extra")), "text": f["text"], "plain": plain(f["text"]),
                   "keys": BOLD.findall(f["text"])}
            flat.append(row)
            by_month.setdefault(m, []).append(row)

def counts(rows):
    return {"facts": len(rows), "cgl": sum("CGL" in r["tags"] for r in rows),
            "upsc": sum("UPSC" in r["tags"] for r in rows), "background": sum(r["background"] for r in rows)}

facts_on = {nid: [] for nid in nodes}       # own facts
facts_under = {nid: [] for nid in nodes}    # own + descendants
for r in flat:
    facts_on[r["node"]].append(r)
    for anc in r["path"]:
        facts_under[anc].append(r)

node_rows = []
for nid, n in nodes.items():
    under = facts_under[nid]
    row = {"id": nid, "label": n["label"], "short": n.get("short"), "parent": n["parent"],
           "junction": path(nid)[0], "path": path(nid), "depth": len(path(nid)), "order": n.get("order"),
           "hue": nodes[path(nid)[0]].get("hue"), "summary": n["summary"], "links": n.get("links", []),
           "children": children[nid], "created": n["created"], "facts_own": len(facts_on[nid]),
           "facts_total": len(under), "first_date": min((r["date"] for r in under), default=None),
           "last_date": max((r["date"] for r in under), default=None)}
    node_rows.append(row)
node_rows.sort(key=lambda r: (r["depth"], nodes[r["junction"]].get("order", 99), r.get("order") or 99, r["id"]))

paper_rows = []
for pp in sorted(papers, key=lambda x: (x["date"], x["id"])):
    rows = [r for r in flat if r["paper"] == pp["id"]]
    paper_rows.append({**paper_view(pp), **counts(rows),
                       "nodes_used": len({r["node"] for r in rows})})

latest_date = max((pp["date"] for pp in papers), default=None)
now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

# ---------------------------------------------------------------- write API
if os.path.isdir(API):
    shutil.rmtree(API)
endpoints = {
    "index": "api/v1/index.json",
    "papers": "api/v1/papers.json",
    "nodes": "api/v1/nodes.json",
    "facts_by_month": "api/v1/facts/{YYYY-MM}.json",
    "paper": "api/v1/papers/{paper_id}.json",
    "node": "api/v1/nodes/{node_id}.json",
    "latest": "api/v1/latest.json",
}
dump(os.path.join(API, "index.json"), {
    "name": "Current Affairs Web API", "version": 1, "base_url": SITE + "/",
    "docs": SITE + "/api.html", "updated": latest_date, "generated_at": now,
    "totals": {"junctions": sum(1 for n in nodes.values() if n["parent"] == "hub"),
               "branches": sum(1 for n in nodes.values() if n["parent"] != "hub"),
               "papers": len(papers), "publications": len(pubs), **counts(flat)},
    "months": sorted(by_month), "endpoints": endpoints,
})
dump(os.path.join(API, "papers.json"), {"publications": pubs, "papers": paper_rows})
dump(os.path.join(API, "nodes.json"), node_rows)
for m, rows in by_month.items():
    dump(os.path.join(API, "facts", f"{m}.json"), {"month": m, "count": len(rows), "facts": rows})
for pr in paper_rows:
    dump(os.path.join(API, "papers", f"{pr['id']}.json"),
         {"paper": pr, "facts": [r for r in flat if r["paper"] == pr["id"]]})
for nr in node_rows:
    dump(os.path.join(API, "nodes", f"{nr['id']}.json"),
         {"node": nr, "facts": sorted(facts_under[nr["id"]], key=lambda r: (r["date"], r["id"]), reverse=True)})
dump(os.path.join(API, "latest.json"), {
    "date": latest_date, "papers": [pr for pr in paper_rows if pr["date"] == latest_date],
    "facts": [r for r in flat if r["date"] == latest_date]})

# ---------------------------------------------------------------- exports
os.makedirs(os.path.join(ROOT, "exports"), exist_ok=True)
with open(os.path.join(ROOT, "exports", "nodes.csv"), "w", newline="", encoding="utf-8") as fp:
    w = csv.writer(fp)
    w.writerow(["id", "label", "short", "parent", "junction", "order", "hue", "summary", "links", "created", "facts_total"])
    for r in node_rows:
        w.writerow([r["id"], r["label"], r["short"] or "", r["parent"], r["junction"], r["order"], r["hue"],
                    r["summary"], ";".join(r["links"]), r["created"], r["facts_total"]])
with open(os.path.join(ROOT, "exports", "papers.csv"), "w", newline="", encoding="utf-8") as fp:
    w = csv.writer(fp)
    w.writerow(["id", "date", "publication", "edition", "pages", "facts", "cgl", "upsc", "background", "link"])
    for r in paper_rows:
        w.writerow([r["id"], r["date"], r["name"], r["edition"] or "", r["pages"] or "", r["facts"], r["cgl"],
                    r["upsc"], r["background"], r["link"] or ""])
with open(os.path.join(ROOT, "exports", "facts.csv"), "w", newline="", encoding="utf-8") as fp:
    w = csv.writer(fp)
    w.writerow(["date", "source", "paper", "fact_id", "node", "node_label", "junction", "tags", "gs", "page",
                "background", "text"])
    for r in flat:
        w.writerow([r["date"], r["source"], r["paper"], r["id"], r["node"], nodes[r["node"]]["label"],
                    r["junction"], ";".join(r["tags"]), r["gs"] or "", r["page"] or "",
                    "yes" if r["background"] else "", r["plain"]])

# old location, superseded by api/v1/index.json
old = os.path.join(DATA, "index.json")
if os.path.exists(old):
    os.remove(old)

print(f"OK  {len(nodes)} nodes, {len(papers)} papers, {n_facts} facts, latest {latest_date}")
