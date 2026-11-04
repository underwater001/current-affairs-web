#!/usr/bin/env python3
"""Search the web's data without loading it all by hand.

    python3 tools/find.py WORD [WORD ...]     facts whose text contains all words (case-insensitive)
    python3 tools/find.py --nodes [WORD]      branches (id, parent, label, fact count), optionally filtered
    python3 tools/find.py --node ID           the facts filed on one node and its sub-branches
    python3 tools/find.py --quiz WORD         quiz questions containing the word

Output is one line per hit, short enough to scan: use it to check for duplicates and
continuing stories before filing a new paper.
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load(p):
    with open(p, encoding="utf-8") as fp:
        return json.load(fp)


def facts():
    for p in sorted(glob.glob(os.path.join(DATA, "months", "*.json"))):
        for d in load(p)["days"]:
            for f in d["facts"]:
                yield d, f


def short(t, n=170):
    t = re.sub(r"\*\*", "", t)
    return t if len(t) <= n else t[: n - 1] + "…"


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    nodes = load(os.path.join(DATA, "nodes.json"))
    if a[0] == "--nodes":
        words = [w.lower() for w in a[1:]]
        cnt = {}
        for _, f in facts():
            cnt[f["node"]] = cnt.get(f["node"], 0) + 1
        for nid, n in sorted(nodes.items(), key=lambda kv: (kv[1]["parent"], kv[1].get("order", 99))):
            line = f"{nid} | {n['parent']} | {n['label']} | {cnt.get(nid, 0)}"
            if all(w in (line + " " + n.get("summary", "")).lower() for w in words):
                print(line)
        return
    if a[0] == "--node":
        nid = a[1]
        if nid not in nodes:
            sys.exit(f"no node '{nid}'")
        under = {nid}
        grew = True
        while grew:
            grew = False
            for k, n in nodes.items():
                if k not in under and n["parent"] in under:
                    under.add(k); grew = True
        for d, f in facts():
            if f["node"] in under:
                print(f"{f['id']} | {f['node']} | {''.join(t[0] for t in f['tags'])} {f.get('priority', '')} | {short(f['text'])}")
        return
    if a[0] == "--quiz":
        w = " ".join(a[1:]).lower()
        for p in sorted(glob.glob(os.path.join(DATA, "quizzes", "*.json"))):
            for q in load(p)["questions"]:
                if w in (q["q"] + " " + " ".join(q["options"])).lower():
                    print(f"{q['id']} | {q['fact']} | {short(q['q'], 140)} -> {q['options'][q['answer']]}")
        return
    words = [w.lower() for w in a]
    for d, f in facts():
        if all(w in f["text"].lower() for w in words):
            print(f"{f['id']} | {f['node']} | {''.join(t[0] for t in f['tags'])} {f.get('priority', '')} | {short(f['text'])}")


if __name__ == "__main__":
    main()
