# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, KeepTogether)

OUT = "/home/claude/out/Master-Prompt-Exam-Knowledge-System.pdf"
INK = colors.HexColor("#18212c"); MUT = colors.HexColor("#5a6575")
ACC = colors.HexColor("#2448c8"); LINE = colors.HexColor("#d6dce5")
SOFT = colors.HexColor("#f3f5f8"); OK = colors.HexColor("#0f6e72")

ss = getSampleStyleSheet()
def S(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9.6, leading=14, textColor=INK, spaceAfter=6)
    base.update(kw); return ParagraphStyle(name, **base)
H1 = S("H1", fontName="Helvetica-Bold", fontSize=20, leading=24, spaceAfter=4)
SUB = S("SUB", fontSize=10.5, leading=15, textColor=MUT, spaceAfter=14)
H2 = S("H2", fontName="Helvetica-Bold", fontSize=13.5, leading=17, spaceBefore=16, spaceAfter=7, textColor=INK)
H3 = S("H3", fontName="Helvetica-Bold", fontSize=10.6, leading=14, spaceBefore=9, spaceAfter=4)
BODY = S("BODY", alignment=TA_JUSTIFY)
BUL = S("BUL", leftIndent=12, bulletIndent=2, spaceAfter=3)
NUM = S("NUM", leftIndent=16, bulletIndent=2, spaceAfter=4)
CODE = S("CODE", fontName="Courier", fontSize=8.4, leading=11.6, textColor=INK,
         backColor=SOFT, borderPadding=6, spaceBefore=4, spaceAfter=8)
NOTE = S("NOTE", fontSize=9.4, leading=13.4, textColor=INK, backColor=colors.HexColor("#eef2fb"),
         borderPadding=7, borderColor=ACC, borderWidth=0, spaceBefore=6, spaceAfter=8, leftIndent=2)
TH = S("TH", fontName="Helvetica-Bold", fontSize=8.6, leading=11, textColor=colors.white, spaceAfter=0)
TD = S("TD", fontSize=8.6, leading=11.6, spaceAfter=0)

def P(t, st=BODY): return Paragraph(t, st)
def B(items, st=BUL): return [Paragraph(t, st, bulletText="•") for t in items]
def N(items):
    return [Paragraph(t, NUM, bulletText="%d." % (i + 1)) for i, t in enumerate(items)]
def TBL(rows, widths, head=True):
    data = [[Paragraph(c, TH if (head and r == 0) else TD) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("GRID", (0, 0), (-1, -1), 0.5, LINE),
             ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
             ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    if head:
        style += [("BACKGROUND", (0, 0), (-1, 0), INK),
                  ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT])]
    t.setStyle(TableStyle(style))
    return t

story = []
A = story.append

# ---------------- cover / intro
A(P("Master prompt: build an exam knowledge system", H1))
A(P("A complete, subject-agnostic brief for an AI assistant. Give this document to a capable model with "
    "study material and it can build and run the same system for any exam subject — current affairs, "
    "quantitative aptitude, reasoning, English, static GK — without further instruction.", SUB))
A(P("Written from a working build for SSC CGL and UPSC current affairs: 651 filed facts, 262 capsule points "
    "and 345 quiz questions across seven newspapers, served as a public website and JSON API.", S("x", fontSize=9, textColor=MUT, spaceAfter=14)))

A(P("1. What you are building", H2))
A(P("A single pipeline that turns raw study material into three linked products, so the learner can skip "
    "the raw material entirely and still be exam-ready:", BODY))
A(TBL([["Product", "What it is", "Why it exists"],
       ["The web", "Every exam-worthy item filed on a tree of subjects and topics, each with a permanent id, "
                   "an exam tag, a priority and its source", "Long-term memory. Nothing is ever lost or duplicated; "
                   "a topic's whole history is one click away"],
       ["The capsule", "One date's or one chapter's material compressed to one-line points, grouped by subject, "
                       "with the small exam details hidden behind a tap", "The 5-10 minute read that replaces the raw material"],
       ["The quiz", "Questions built from the capsule, answers hidden until chosen, with an explanation and "
                    "1-2 related facts under each answer", "Turns reading into recall; proves the capsule was enough"]],
      [70, 215, 180]))
A(Spacer(1, 6))
A(P("<b>The rule that holds it together:</b> the capsule must be sufficient to answer the quiz, and the quiz must "
    "cover every capsule point. Both directions are enforced by a script, not by good intentions.", NOTE))

A(P("2. The core concept", H2))
A(P("Material → <b>atomic items</b> on a topic web → <b>priority</b> from real exam evidence → "
    "<b>capsule</b> (compressed, with detail behind a tap) → <b>quiz</b> written from the capsule → "
    "<b>automatic checks</b> → publish → short report to the learner.", BODY))
A(Spacer(1, 2))
A(P("Four principles make it work for any subject:", H3))
A(TBL([["Principle", "What it means in practice"],
       ["Atomise", "One item = one testable idea, in 1-3 sentences, with the testable terms in <b>bold</b>. "
                   "Bold terms become quiz answers and search keys."],
       ["Place, don't pile", "Every item hangs on a topic node in a shallow tree (subject → topic → sub-topic). "
                             "A continuing story or a recurring question type grows its own node, so the learner sees a timeline, not a feed."],
       ["Rank by evidence", "Priority comes from previous years' papers, not from how interesting the item feels. "
                            "Everything the learner sees can be filtered by it."],
       ["Compress, then test", "The capsule is the deliverable; the web is the archive; the quiz is the proof. "
                               "If an answer is not in the capsule, the capsule is wrong — not the learner."]],
      [95, 370]))

A(P("3. Before you write anything: learn the exam", H2))
A(P("Do this first, once per subject. It decides every priority tag afterwards.", BODY))
A(*[[]][0:0]) if False else None
for p in N([
 "Collect <b>3-5 years of real previous-year papers</b> (official papers beat memory-based reconstructions; "
 "8-10 shifts per year beats one shift from ten years).",
 "Extract only the section you are building for. Classify every question: topic, what exactly is asked "
 "(a name, a number, a place, a rule, a method), and how old the tested material was.",
 "Write the findings down as a <b>pick list</b> and a <b>skip list</b> with a priority scale. Coaching blogs are a "
 "starting point, not evidence — check them against the real papers and prefer the papers when they disagree.",
 "Re-read this list whenever the learner corrects a pick. Every correction becomes a rule.",
]): A(p)
A(P("<b>Worked example (SSC CGL current affairs).</b> The 2021 official papers showed 5-9 current-affairs questions "
    "per 25-question section, events 3-9 months old, and — the surprise — that small items (a PSU chief, a brand "
    "ambassador, a mascot, a 'first State to…', a book's author) are asked as often as the big stories. That single "
    "finding changed what counts as high priority.", NOTE))

A(PageBreak())

# ---------------- data model
A(P("4. Data model", H2))
A(P("Plain JSON files in a git repository are the source of truth. Everything else is generated. "
    "Keep the generated output out of the editing path so a bad edit can never corrupt the archive.", BODY))
A(TBL([["File", "Holds", "Key fields"],
       ["nodes.json", "The topic tree: subjects (the 10-14 roots) and topics under them",
        "id, label, summary, parent, order, created, links (related topics in other subjects); roots add short, hue"],
       ["sources.json", "Every piece of material used, so any item can be traced",
        "id, date or chapter, publication/book, edition, pages, link, added"],
       ["items/&lt;group&gt;.json", "The items themselves, grouped by month (or chapter)",
        "id (permanent, e.g. f20261104-017), node, tags (which exam), priority, text, page, extra (true if you added it)"],
       ["capsules/&lt;key&gt;.json", "One capsule: sections by subject, each a list of points",
        "junction, points[{text, facts, more}] — more holds the ids revealed on tap"],
       ["quizzes/&lt;key&gt;.json", "One quiz", "id, fact (the item tested), type, q, options, answer, explanation, also"]],
      [78, 150, 237]))
A(Spacer(1, 4))
for p in B([
 "<b>Ids are permanent.</b> Never renumber. A corrected item keeps its id, so quiz progress and links never break.",
 "<b>Tags and priority live on the item</b>, never on the question or the capsule point, so the three products "
 "can never disagree with each other.",
 "<b>Mark your own additions.</b> Anything not present in the source material is flagged (extra: true) and shown as "
 "a note, never as something the source said.",
]): A(p)

A(P("5. The four tools", H2))
A(P("Write these before filing anything. They are what keeps the daily cost flat as the archive grows.", BODY))
A(TBL([["Tool", "Does"],
       ["add_batch", "Takes <b>one spec file per batch of material</b> (the source, new topics, items, corrections to older "
                     "items, the capsule, the quiz) and does everything: numbers ids, fills topic order and creation date, "
                     "adds links both ways, shuffles answer options, runs the build, and <b>restores every file if anything "
                     "fails</b>. Refuses a source that was already added."],
       ["build", "Validates the whole archive, then regenerates the API and the spreadsheet exports. Prints OK or a list of "
                 "errors and writes nothing. Validation must include: ids unique and well-formed, every item on an existing "
                 "topic, every required tag present, priority present where required, options distinct, answer in range, "
                 "cross-references real."],
       ["find", "One-line search over items, topics and questions. Used before filing, to catch duplicates and to spot a "
                "continuing story without reading whole files."],
       ["check_capsule", "The quality gate: every quiz answer must be findable in that capsule, and every capsule point "
                         "must have at least one question. Prints the gaps; exits non-zero."]],
      [78, 387]))
A(P("<b>Why a single spec file matters.</b> The first version of this system used a fresh hand-written script per batch. "
    "By the third batch that was the slowest part of the work and the only place bugs appeared. One declarative spec plus "
    "one idempotent command removed both problems.", NOTE))

A(P("6. The pages", H2))
A(TBL([["Page", "Must do"],
       ["Capsule (the home page for daily use)", "Pick a date or chapter; points grouped by subject; tap the circle to mark "
        "read; tap a point to reveal the exam notes; reading-time estimate; one button to the matching quiz; link to the source."],
       ["Quiz", "Same picker; filters by exam and priority; options hidden until one is chosen; then the verdict, a one-line "
        "explanation, 'also remember' facts, the source and a link to the topic; a running score."],
       ["Web", "The whole tree, searchable and filterable, with each topic's items newest-first — the archive view."],
       ["Sources", "Every piece of material used, with a link to the original and how many items came from it."],
       ["API", "The same data as plain JSON so a future app (flashcards, a bot, spaced repetition) needs no scraping."]],
      [120, 345]))
A(Spacer(1, 4))
for p in B([
 "Load only what the current view needs (one small file per date) so the pages stay fast after a year of material.",
 "Store the learner's ticks and scores locally in the browser; never make reading depend on a login.",
 "Light and dark themes, readable on a phone, no horizontal scrolling.",
]): A(p)

A(PageBreak())

# ---------------- rules
A(P("7. Writing rules that decide quality", H2))
A(P("Items", H3))
for p in B([
 "One idea per item. Continuing stories get an update phrased as an update, never a repeat.",
 "Bold every testable term: names, numbers, dates, places, section numbers, formulas.",
 "Be faithful to the source. Attribute claims (“the minister said…”). Never present your own knowledge as the source's.",
 "Add the background the source leaves out — but only through one test: <b>would a question on this detail plausibly "
 "appear in the exam?</b> Cap it at about two per story. Unchecked background is the fastest way to ruin the capsule.",
]): A(p)
A(P("Capsule points", H3))
for p in B([
 "One line per story or concept, under ~240 characters, grouped by subject; fold the background into the line or park it behind the tap.",
 "Cover every high-priority item; drop the low-priority ones entirely. Target a 5-10 minute read.",
 "Write the detail the learner must <i>recall</i>, not the detail that makes the sentence read nicely.",
]): A(p)
A(P("Questions", H3))
for p in B([
 "Walk the capsule point by point so nothing is left untested. Ask exactly what the exam asks.",
 "Distractors must be the same kind of thing as the answer (four holders of the same office, four close years, "
 "four States of one region). Never joke options — they teach nothing and inflate scores.",
 "Spread correct answers evenly across the positions; shuffle options programmatically, not by feel.",
 "Add 1-2 related facts under the answer, chosen by hand from the same story. Loosely related extras are worse than none.",
 "Mix formats the exam uses: direct, 'which statements are correct', assertion-reason.",
]): A(p)

A(P("8. Adapting the concept to other subjects", H2))
A(P("Only the meaning of an <i>item</i> changes. The pipeline, the tools and the checks stay identical.", BODY))
A(TBL([["Subject", "An item is…", "Topic tree", "Priority from", "Capsule looks like", "Quiz"],
       ["Current affairs", "A fact with its source and date", "Subjects → running stories",
        "Frequency of that fact type in past papers", "One line per story", "Recall MCQs"],
       ["Quantitative aptitude", "A method, formula or trap, with one worked example and the condition it applies under",
        "Arithmetic / algebra / geometry / DI → question types", "How many marks that type carried per paper",
        "The formula plus the one-line trigger: 'when the ratio is given and time differs, use…'",
        "Solve-it items generated from the same template with new numbers; the worked example is the explanation"],
       ["Reasoning", "A pattern with its recognition cue and the fastest route to the answer",
        "Verbal / non-verbal → puzzle families (seating, syllogism, series…)",
        "Count of each family per shift", "Cue → method → common trap, one line each",
        "One fresh puzzle per family; time limit per item"],
       ["English", "A rule, a confusable pair, an idiom or a high-frequency word",
        "Grammar / vocabulary / comprehension → rule families", "Error-spotting and vocabulary repeats",
        "Rule plus a minimal example and the wrong version", "Spot-the-error and fill-in from the same rule"],
       ["Static GK, history, polity", "A fact tied to a syllabus heading, not a date",
        "Syllabus headings → sub-headings", "Syllabus weight and past-paper counts",
        "Grouped tables (rulers, articles, dams, dances)", "Matching and direct recall"],
       ["Science", "A concept with its definition, unit and one application",
        "Physics / chemistry / biology → chapters", "Past-paper counts per chapter",
        "Definition, formula, one application", "Direct recall plus one applied item"]],
      [62, 95, 78, 70, 88, 72]))
A(Spacer(1, 5))
A(P("<b>Two adaptations worth making explicit.</b> For skill subjects (maths, reasoning) add a <i>variant generator</i>: "
    "each item carries a template so the quiz can produce unlimited fresh questions with the same method, and record which "
    "methods the learner keeps failing. For subjects with a fixed syllabus, index the tree by the official syllabus headings "
    "so coverage gaps are visible at a glance.", NOTE))

A(PageBreak())

# ---------------- build order & ops
A(P("9. Build order", H2))
for p in N([
 "<b>Study the papers</b> (section 3) and write the pick, skip and priority rules into a document you will follow every day.",
 "<b>Create the repository</b> and the empty data files; decide the subject roots and their colours.",
 "<b>Write build first</b>, with full validation, then find, then add_batch, then check_capsule. Test add_batch on a copy "
 "of the repository, including a deliberately broken spec, before trusting it.",
 "<b>File one batch of material end to end</b> — items, capsule, quiz — and fix what the checks complain about.",
 "<b>Build the pages</b>, capsule first; publish; verify the deployment actually serves the new data before telling the learner.",
 "<b>Write the daily procedure down</b> (as a reusable instruction file) so a fresh session repeats it exactly.",
]): A(p)

A(P("10. Acceptance checklist", H2))
A(P("A batch is finished only when all of these are true:", BODY))
for p in B([
 "The build prints OK and the checker reports <b>0 gaps and 0 untested points</b>.",
 "Every item carries a priority (where the exam tag requires one) and traces to a source with a page or location.",
 "The capsule reads in the target time and covers every high-priority item.",
 "Correct answers are spread across the option positions; no duplicate or joke distractors.",
 "The deployment is live and serving the new data — verified, not assumed.",
 "The learner gets a short report: what was added, what was skipped and why, what changed, what is still missing.",
]): A(p)

A(P("11. Operating rules", H2))
for p in B([
 "<b>Version everything.</b> A git repository plus a static host costs nothing and keeps the full history; the learner "
 "should never depend on a single chat or a single device.",
 "<b>Never commit copyrighted source material.</b> Link to the learner's own copy instead, and tell them to keep the "
 "sharing restricted.",
 "<b>Correct in place.</b> When later material shows an earlier item was wrong, fix that item (keeping its id) and say so "
 "in the report. Silent corrections destroy trust in the archive.",
 "<b>Report honestly.</b> Say what was skipped and what could not be verified. A confident summary over a thin pass is "
 "the one failure mode the learner cannot detect.",
]): A(p)

A(P("12. The prompt to paste", H2))
A(P("Give the model this, together with the material:", BODY))
A(Paragraph(
 "You are building and running an exam knowledge system for &lt;exam&gt;, subject &lt;subject&gt;.<br/><br/>"
 "First, study the previous-year papers I give you and write down, as rules, what that exam actually asks: the "
 "question types, how they are phrased, and which details are tested. Rank everything you will later file as high, "
 "medium or low priority on that evidence alone.<br/><br/>"
 "Then, for every batch of material I send, run this pipeline without being asked:<br/>"
 "1. Read all of it, including the parts that look unpromising.<br/>"
 "2. File each exam-worthy item on a topic tree, with a permanent id, an exam tag, a priority, the testable terms in "
 "bold, and the source and page.<br/>"
 "3. Add the exam background the material leaves out, but only details a question could plausibly be built on, and "
 "mark them as your own additions.<br/>"
 "4. Write a capsule: that batch compressed to one-line points grouped by subject, a five-to-ten minute read, with "
 "the small details hidden behind a tap.<br/>"
 "5. Write the quiz from the capsule, point by point, so every point is tested and every answer is findable in the "
 "capsule. Hide the answers until chosen; give each one a one-line explanation and one or two closely related facts.<br/>"
 "6. Attach the source link, run your own checker until it reports no gaps in either direction, publish, and verify "
 "the published copy.<br/>"
 "7. Report briefly: what was added, what was skipped and why, what you corrected, what is still missing.<br/><br/>"
 "Build the tools so that each batch is one spec file and one command, with automatic rollback. Keep everything in a "
 "git repository with a static site and a JSON API. Never commit the source material itself. Never present your own "
 "knowledge as the source's. When I correct a judgement of yours, write it into the rules so it holds next time.",
 CODE))
A(Spacer(1, 8))
A(P("Everything in this document was derived from a working system, not a plan. The parts that proved most valuable, "
    "in order: priority judged from real papers; the capsule as the primary product; and the two-way check between the "
    "capsule and the quiz — which caught four unanswerable questions on the first day it existed.",
    S("end", fontSize=9.2, textColor=MUT, leading=13)))

def deco(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.6)
    canvas.line(20 * mm, A4[1] - 14 * mm, A4[0] - 20 * mm, A4[1] - 14 * mm)
    canvas.setFont("Helvetica", 7.6); canvas.setFillColor(MUT)
    canvas.drawString(20 * mm, A4[1] - 11.6 * mm, "Master prompt — exam knowledge system")
    canvas.drawRightString(A4[0] - 20 * mm, A4[1] - 11.6 * mm, "page %d" % doc.page)
    canvas.line(20 * mm, 14 * mm, A4[0] - 20 * mm, 14 * mm)
    canvas.drawString(20 * mm, 10 * mm, "Built from the Current Affairs Web (SSC CGL / UPSC)")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, "underwater001.github.io/current-affairs-web")
    canvas.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                      topMargin=20 * mm, bottomMargin=20 * mm,
                      title="Master prompt: build an exam knowledge system",
                      author="Prepared with Claude")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=deco)])
doc.build([s for s in story if s is not None])
print("written", OUT)
