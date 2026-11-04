#!/usr/bin/env python3
"""Can the day's quiz be answered from the day's capsule alone?

    python3 tools/check_capsule.py [YYYY-MM-DD ...]      (default: every date)

The capsule is meant to replace reading the newspaper, so every quiz answer must be
findable in it. For each question this checks that the capsule cites the fact being
tested and, for ordinary MCQs, that the words of the correct option appear in those
points. Statement and Assertion-Reason questions only need the fact to be covered.
Prints one line per gap and exits non-zero if any are found.
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "api", "v1")
SHORT = {"sec": "section", "art": "article", "bn": "billion", "cr": "crore", "mn": "million", "yrs": "years", "yr": "year",
         "tr": "reserve", "pct": "percent", "govt": "government", "amendment": "amendment"}
SKIP = {"the", "and", "for", "with", "from", "that", "this", "than", "over", "under",
        "india", "indian", "group", "year", "years", "about", "only", "both", "true", "false",
        "reason", "explains", "statement", "statements", "neither"}


def toks(t):
    out = []
    for w in re.sub(r"[^a-z0-9₹$%. ]", " ", t.lower()).replace(".", " ").split():
        w = SHORT.get(w, w)
        if len(w) > 3 and w not in SKIP:
            out.append(w)
    return out


def main():
    want = sys.argv[1:]
    gaps = 0
    for p in sorted(glob.glob(os.path.join(API, "quizzes", "*.json"))):
        d = os.path.splitext(os.path.basename(p))[0]
        if d == "index" or (want and d not in want):
            continue
        cp = os.path.join(API, "capsules", f"{d}.json")
        if not os.path.exists(cp):
            print(f"{d}: no capsule for a quiz of {len(json.load(open(p))['questions'])} questions")
            gaps += 1
            continue
        cap = json.load(open(cp, encoding="utf-8"))
        by_fact = {}
        for sec in cap["sections"]:
            for pt in sec["points"]:
                for f in pt["facts"]:
                    by_fact.setdefault(f, []).append(pt["plain"])
        bad = []
        for q in json.load(open(p, encoding="utf-8"))["questions"]:
            src = " ".join(by_fact.get(q["fact"], []))
            if not src:
                bad.append((q["id"], "fact not in the capsule", q["q"]))
                continue
            if q["type"] != "mcq":
                continue
            need = toks(q["options"][q["answer"]])
            have = toks(src)
            missing = [w for w in need if not any(w == h or w in h or h in w for h in have)]
            if need and len(missing) > len(need) // 3:
                bad.append((q["id"], "answer '%s' not in its capsule point" % q["options"][q["answer"]], q["q"]))
        qfacts = {q["fact"] for q in json.load(open(p, encoding="utf-8"))["questions"]}
        untested = sum(1 for sec in cap["sections"] for pt in sec["points"]
                       if not (set(pt["facts"]) | {m["fact"] for m in pt["more"]}) & qfacts)
        print(f"{d}: {len(bad)} gap(s); {untested} capsule point(s) with no question")
        for b in bad:
            print(f"   {b[0]}  {b[1]}\n      {b[2][:100]}")
        gaps += len(bad)
    print("OK, every quiz answer is in the capsule" if not gaps else f"{gaps} gap(s) to fix")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
