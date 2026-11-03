# Current Affairs Web

A growing knowledge web of current-affairs facts for **SSC CGL** and **UPSC** prep. Each newspaper is read page by page, and every exam-relevant fact is filed onto the web: subjects (junctions) branch into topics, facts hang on the topic they belong to, and dashed lines link related topics across subjects.

- **Web:** https://underwater001.github.io/current-affairs-web/
- **Sources:** https://underwater001.github.io/current-affairs-web/sources.html — every paper used, with links to the originals
- **API:** https://underwater001.github.io/current-affairs-web/api.html — free read-only JSON for building apps (quizzes, flashcards, bots)

## Repo layout

| Path | What it is |
|---|---|
| `data/nodes.json` | **Source of truth.** Every junction (subject) and branch (topic) |
| `data/sources.json` | **Source of truth.** Publications and every paper read, with an optional Drive `link` |
| `data/months/YYYY-MM.json` | **Source of truth.** Facts, grouped by paper, one file per month |
| `tools/build.py` | Validates the data and generates everything below |
| `api/v1/` | Generated JSON API (see `api.html`) |
| `exports/*.csv` | Generated spreadsheets: facts, nodes, papers |
| `index.html`, `sources.html`, `api.html` | The site |

Every update is a git commit, so the full history of what was added and when is kept.

## Data model

**Node** (`data/nodes.json`, keyed by id): `label`, `summary`, `order`, `created`, `parent` (`"hub"` for a junction), `links` (related node ids); junctions also have `short` and `hue` (0-359, never changed).

**Publication** (`data/sources.json` → `publications`, keyed by id): `name`, `short`, `publisher`, `language`, `frequency`, `website`.

**Paper** (`data/sources.json` → `papers`): `id` (the date, or `date-<pub>` when two papers share a date), `date`, `publication`, `edition`, `pages`, `link` (https URL or `null`), `added`.

**Fact** (`data/months/YYYY-MM.json` → `days[].facts`, under the paper's `id` and `date`): `id` (`fYYYYMMDD-NNN`, permanent), `node`, `tags` (`CGL`/`UPSC`), `priority` (CGL facts only: `high`/`medium`/`low`), `text` (`**bold**` for key terms), optional `page`, `gs` (GS1-GS4), `extra: true` (background knowledge, not printed in the paper).

## Adding a paper

1. Add the paper to `data/sources.json` → `papers` (and its publication, if new).
2. Add its facts to the month file (`data/months/YYYY-MM.json`; create it for a new month).
3. Add any new branches to `data/nodes.json`, and links on existing nodes.
4. Run `python3 tools/build.py`. It must print `OK`.
5. Commit and push. GitHub Pages republishes in a minute or two.

To attach a Drive link later, set the paper's `link` in `data/sources.json`, rebuild and push.

## CGL priority rules

Judged from previous CGL papers (2021 official papers, 2025 memory-based papers) and coaching analyses. CGL asks about 5-9 current-affairs questions per shift, mostly on events 3-9 months before the exam.

- **high**: appointments (incl. minor ones like PSU and board heads), awards, books and authors, firsts and "first State to", sports winners and records, important days, schemes with ministry/launch year/numbers, index ranks, defence and space milestones, new laws and their sections, classic static GK linked to the news.
- **medium**: useful context: summits, foreign elections, State-level schemes, economy data, court rulings with a clear principle.
- **low**: local crime, accidents, party infighting, day-to-day politics, market moves, quotes and opinions.

