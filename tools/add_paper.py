#!/usr/bin/env python3
"""Add one paper (its facts, new branches, corrections and quiz) to the web in one step.

    python3 tools/add_paper.py path/to/spec.json [--dry-run]

The spec is one JSON file per paper:

{
  "paper":  {"id": "2026-11-04", "date": "2026-11-04", "publication": "the-hindu",
             "edition": "Delhi", "pages": 18, "link": null},
  "publication": {...}                 optional: a new publication, keyed by "id" inside
  "nodes":  {"new-branch": {"label": "...", "parent": "economy", "summary": "...",
                            "links": ["other-node"]}},       order/created filled in
  "links":  [["node-a", "node-b"]],    extra links between existing nodes (both ways)
  "facts":  [{"node": "...", "tags": ["CGL","UPSC"], "priority": "high",
              "text": "...", "page": "1", "gs": "GS2", "extra": true}],
  "fixes":  [{"id": "f20261102-029", "find": "1 November", "replace": "31 October"}],
  "quiz":   [{"fact": 3, "q": "...", "options": ["a","b","c","d"], "answer": 0,
              "explanation": "...", "type": "mcq"}]
}

- Fact ids continue the date's numbering (a second paper on the same date goes on from the first).
- A quiz "fact" is a 1-based index into this spec's "facts", or a full fact id from any date.
- Quiz questions go into data/quizzes/<date>.json, numbered q<YYYYMMDD>-NNN. Options of "mcq"
  questions are shuffled (write the right answer anywhere; add "shuffle": false to keep the order).
  "statements" and "assertion" questions keep their standard option order.
- Re-running the same spec is refused (the paper id already exists), so nothing is added twice.
- After writing, the build runs; if it fails, every data file is restored.
"""
import json, os, random, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load(p):
    with open(p, encoding="utf-8") as fp:
        return json.load(fp)


def save(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fp:
        fp.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def die(msg):
    sys.exit("add_paper: " + msg)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) != 1:
        die(__doc__)
    spec = load(args[0])
    paper = spec.get("paper") or die("spec needs 'paper'")
    for k in ("id", "date", "publication"):
        if not paper.get(k):
            die(f"paper needs '{k}'")
    date, pid = paper["date"], paper["id"]
    month = date[:7]
    ymd = date.replace("-", "")

    p_nodes = os.path.join(DATA, "nodes.json")
    p_src = os.path.join(DATA, "sources.json")
    p_month = os.path.join(DATA, "months", f"{month}.json")
    p_quiz = os.path.join(DATA, "quizzes", f"{date}.json")
    touched = [p_nodes, p_src, p_month, p_quiz]
    backup = {p: open(p, encoding="utf-8").read() if os.path.exists(p) else None for p in touched}

    nodes, src = load(p_nodes), load(p_src)
    if any(p["id"] == pid for p in src["papers"]):
        die(f"paper '{pid}' is already in sources.json")

    # publication + paper
    if spec.get("publication"):
        pub = dict(spec["publication"]); pub_id = pub.pop("id")
        src["publications"].setdefault(pub_id, pub)
    if paper["publication"] not in src["publications"]:
        die(f"unknown publication '{paper['publication']}' (add it under 'publication')")
    src["papers"].append({"id": pid, "date": date, "publication": paper["publication"],
                          "edition": paper.get("edition"), "pages": paper.get("pages"),
                          "link": paper.get("link"), "added": paper.get("added") or __import__("datetime").date.today().isoformat()})
    src["papers"].sort(key=lambda p: (p["date"], p["id"]))

    # nodes
    def link(a, b):
        for x, y in ((a, b), (b, a)):
            lk = nodes[x].setdefault("links", [])
            if y not in lk:
                lk.append(y)
    new_nodes = spec.get("nodes") or {}
    for nid, n in new_nodes.items():
        if nid in nodes:
            die(f"node '{nid}' already exists")
        par = n.get("parent")
        if par != "hub" and par not in nodes and par not in new_nodes:
            die(f"node '{nid}': unknown parent '{par}'")
        n = dict(n)
        n.setdefault("created", date)
        if "order" not in n:
            sib = [m.get("order", 0) for m in nodes.values() if m.get("parent") == par]
            n["order"] = max(sib, default=0) + 1
        links = n.pop("links", [])
        n["links"] = []
        nodes[nid] = n
        n["_pending"] = links
    for nid in new_nodes:
        for l in nodes[nid].pop("_pending"):
            if l not in nodes:
                die(f"node '{nid}': link to unknown node '{l}'")
            link(nid, l)
    for a, b in spec.get("links") or []:
        if a not in nodes or b not in nodes:
            die(f"link {a} - {b}: unknown node")
        link(a, b)

    # facts
    mdoc = load(p_month) if os.path.exists(p_month) else {"month": month, "days": []}
    used = [int(f["id"].split("-")[1]) for d in mdoc["days"] if d["date"] == date for f in d["facts"]]
    nxt = max(used, default=0) + 1
    facts = []
    for i, f in enumerate(spec.get("facts") or [], 1):
        if f.get("node") not in nodes:
            die(f"fact {i}: unknown node '{f.get('node')}'")
        row = {"id": f"f{ymd}-{nxt:03d}", "node": f["node"], "tags": f["tags"]}
        if "CGL" in f["tags"]:
            row["priority"] = f.get("priority") or die(f"fact {i}: CGL fact needs a priority")
        row["text"] = f["text"]
        for k in ("page", "gs"):
            if f.get(k):
                row[k] = f[k]
        if f.get("extra"):
            row["extra"] = True
        facts.append(row); nxt += 1
    mdoc["days"].append({"id": pid, "date": date, "facts": facts})
    mdoc["days"].sort(key=lambda d: (d["date"], d["id"]))

    # fixes (any month)
    other = {}
    for fx in spec.get("fixes") or []:
        fid = fx["id"]; m = f"{fid[1:5]}-{fid[5:7]}"
        pm = os.path.join(DATA, "months", f"{m}.json")
        doc = mdoc if pm == p_month else other.setdefault(pm, load(pm))
        if pm not in backup:
            backup[pm] = open(pm, encoding="utf-8").read(); touched.append(pm)
        hit = [f for d in doc["days"] for f in d["facts"] if f["id"] == fid]
        if not hit:
            die(f"fix: fact {fid} not found")
        f = hit[0]
        if "find" in fx:
            if fx["find"] not in f["text"]:
                die(f"fix {fid}: text not found: {fx['find']!r}")
            f["text"] = f["text"].replace(fx["find"], fx["replace"])
        for k in ("node", "tags", "priority", "gs", "page"):
            if k in fx:
                f[k] = fx[k]

    # quiz
    qdoc = load(p_quiz) if os.path.exists(p_quiz) else {"date": date, "questions": []}
    qn = max((int(q["id"].split("-")[1]) for q in qdoc["questions"]), default=0) + 1
    for i, q in enumerate(spec.get("quiz") or [], 1):
        ref = q.get("fact")
        fid = facts[ref - 1]["id"] if isinstance(ref, int) else ref
        if isinstance(ref, int) and not 1 <= ref <= len(facts):
            die(f"quiz {i}: fact index {ref} out of range")
        qid = f"q{ymd}-{qn:03d}"
        opts, ans = list(q["options"]), q["answer"]
        if q.get("type", "mcq") == "mcq" and q.get("shuffle", True):
            # spread correct answers across A-D; deterministic per question id
            idx = list(range(len(opts))); random.Random(qid).shuffle(idx)
            right = opts[ans]; opts = [opts[j] for j in idx]; ans = opts.index(right)
        row = {"id": qid, "fact": fid, "type": q.get("type", "mcq"),
               "q": q["q"], "options": opts, "answer": ans, "explanation": q.get("explanation", "")}
        qdoc["questions"].append(row); qn += 1

    if dry:
        print(f"dry run OK: {len(facts)} facts ({facts[0]['id'] if facts else '-'} ...), "
              f"{len(new_nodes)} new nodes, {len(spec.get('fixes') or [])} fixes, {len(spec.get('quiz') or [])} questions")
        return

    save(p_nodes, nodes); save(p_src, src); save(p_month, mdoc)
    for pm, doc in other.items():
        save(pm, doc)
    if qdoc["questions"]:
        save(p_quiz, qdoc)
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "build.py")], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        for p, txt in backup.items():
            if txt is None:
                if os.path.exists(p):
                    os.remove(p)
            else:
                open(p, "w", encoding="utf-8").write(txt)
        print(r.stderr.strip())
        die("build failed; all data files restored")
    hi = sum(f.get("priority") == "high" for f in facts)
    print(f"added {pid}: {len(facts)} facts ({hi} high), {len(new_nodes)} new nodes, "
          f"{len(spec.get('fixes') or [])} fixes, {len(spec.get('quiz') or [])} quiz questions")


if __name__ == "__main__":
    main()
