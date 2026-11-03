# Current Affairs Web

A growing knowledge web of current-affairs facts for **SSC CGL** and **UPSC** prep. Each newspaper is read page by page, and every exam-relevant fact is filed onto the web: subjects (junctions) branch into topics, facts hang on the topic they belong to, and dashed lines link related topics across subjects.

**Open the web:** https://underwater001.github.io/current-affairs-web/

## What's in the repo

| Path | What it is |
|---|---|
| `index.html` | The page: radial web, search, CGL/UPSC filter, period filter, reading panel |
| `data/nodes.json` | The structure: every junction (subject) and branch (topic) |
| `data/months/YYYY-MM.json` | The facts: one file per month, holding each newspaper read that month |
| `data/index.json` | Generated: which month files exist, plus totals |
| `exports/facts.csv`, `exports/nodes.csv` | Generated: the same data as spreadsheets |
| `tools/build.py` | Validates the data and regenerates the generated files |

Every update is a git commit, so the full history of what was added and when is kept.

## Data model

**Node** (`data/nodes.json`, keyed by id)
- `label`, `summary` (one sentence), `order` (position among siblings), `created` (date of the paper that created it)
- `parent`: `"hub"` for a junction, otherwise the parent node's id
- `links`: ids of related nodes, usually in other subjects
- junctions also have `short` (label on the web) and `hue` (0-359, never changed)

**Paper** (an entry in `data/months/YYYY-MM.json` → `days`)
- `id` (the date, or `date-source` if two papers share a date), `date`, `source`, `short`, `pages`
- `facts`: each with `id` (`fYYYYMMDD-NNN`), `node`, `tags` (`CGL` / `UPSC`), `text`, and optional `page`, `gs` (GS1-GS4), `extra: true` (background knowledge, not printed in the paper)

## Adding a paper

1. Add the paper's entry to the month file (create `data/months/YYYY-MM.json` if it's a new month).
2. Add any new branches to `data/nodes.json`, and add links on existing nodes.
3. Run `python3 tools/build.py`. It must print `OK`.
4. Commit and push. GitHub Pages republishes within a minute or two.
