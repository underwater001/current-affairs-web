# Current Affairs Web

A growing knowledge web of current-affairs facts for **SSC CGL** and **UPSC** prep. Each newspaper is read page by page, and every exam-relevant fact is filed onto the web: subjects (junctions) branch into topics, facts hang on the topic they belong to, and dashed lines link related topics across subjects.

- **Web:** https://underwater001.github.io/current-affairs-web/
- **Sources:** https://underwater001.github.io/current-affairs-web/sources.html — every paper used, with links to the originals
- **Quiz:** https://underwater001.github.io/current-affairs-web/quiz.html — a date-wise quiz from each day's papers, answers hidden until you choose
- **API:** https://underwater001.github.io/current-affairs-web/api.html — free read-only JSON for building apps (quizzes, flashcards, bots)

## Repo layout

| Path | What it is |
|---|---|
| `data/nodes.json` | **Source of truth.** Every junction (subject) and branch (topic) |
| `data/sources.json` | **Source of truth.** Publications and every paper read, with an optional Drive `link` |
| `data/quizzes/YYYY-MM-DD.json` | **Source of truth.** That date's quiz; each question points to a fact |
| `data/months/YYYY-MM.json` | **Source of truth.** Facts, grouped by paper, one file per month |
| `tools/add_paper.py` | Adds one paper (facts, new branches, corrections, quiz) from a single spec file, then builds |
| `tools/find.py` | Searches facts, branches and quiz questions (duplicate checks) |
| `tools/build.py` | Validates the data and generates everything below |
| `api/v1/` | Generated JSON API (see `api.html`) |
| `exports/*.csv` | Generated spreadsheets: facts, nodes, papers |
| `index.html`, `quiz.html`, `sources.html`, `api.html` | The site |

Every update is a git commit, so the full history of what was added and when is kept.

## Data model

**Node** (`data/nodes.json`, keyed by id): `label`, `summary`, `order`, `created`, `parent` (`"hub"` for a junction), `links` (related node ids); junctions also have `short` and `hue` (0-359, never changed).

**Publication** (`data/sources.json` → `publications`, keyed by id): `name`, `short`, `publisher`, `language`, `frequency`, `website`.

**Paper** (`data/sources.json` → `papers`): `id` (the date, or `date-<pub>` when two papers share a date), `date`, `publication`, `edition`, `pages`, `link` (https URL or `null`), `added`.

**Fact** (`data/months/YYYY-MM.json` → `days[].facts`, under the paper's `id` and `date`): `id` (`fYYYYMMDD-NNN`, permanent), `node`, `tags` (`CGL`/`UPSC`), `priority` (CGL facts only: `high`/`medium`/`low`), `text` (`**bold**` for key terms), optional `page`, `gs` (GS1-GS4), `extra: true` (background knowledge, not printed in the paper).

## Adding a paper

Write one spec file for the paper and run:

```
python3 tools/add_paper.py spec.json --dry-run   # check
python3 tools/add_paper.py spec.json             # write + build
```

The spec holds the paper (date, publication, pages, Drive link), any new branches, the facts, corrections to older facts, and the day's quiz. The tool numbers facts and questions, fills in branch order and creation date, adds links in both directions, shuffles answer options, and runs the build; if anything fails, all data files are restored. See the docstring in `tools/add_paper.py` for the format. Then commit and push; GitHub Pages republishes in a minute or two.

To attach a Drive link later, set the paper's `link` in `data/sources.json`, run `python3 tools/build.py` and push.

**Quiz question** (`data/quizzes/<date>.json` → `questions`): `id` (`qYYYYMMDD-NNN`), `fact` (the fact it tests), `type` (`mcq`, `statements` or `assertion`), `q`, `options` (2-5), `answer` (option index), `explanation`. Tags, priority and GS paper come from the fact, so they never disagree.

## Scaling

- Facts live in one file per month, so each paper touches only the current month.
- The web loads only the latest three months at first; older months load on "All time" or a search.
- The build regenerates the API in a few seconds and groups facts by paper and node in one pass.

## CGL priority rules

Judged from previous CGL papers (2021 official papers, 2025 memory-based papers) and coaching analyses. CGL asks about 5-9 current-affairs questions per shift, mostly on events 3-9 months before the exam.

- **high**: appointments (incl. minor ones like PSU and board heads), awards, books and authors, firsts and "first State to", sports winners and records, important days, schemes with ministry/launch year/numbers, index ranks, defence and space milestones, new laws and their sections, classic static GK linked to the news.
- **medium**: useful context: summits, foreign elections, State-level schemes, economy data, court rulings with a clear principle.
- **low**: local crime, accidents, party infighting, day-to-day politics, market moves, quotes and opinions.

