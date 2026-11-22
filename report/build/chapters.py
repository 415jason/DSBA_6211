"""Turn each teammate's chapter (.docx read by convert.py) into report blocks.

Wording is the authors' own. Changes made here, all mechanical:
- one heading and byline style for every chapter
- figures and tables numbered by chapter (Figure 1 in Chapter 3 becomes Figure 3.1),
  in captions and in the text that refers to them
- en and em dashes written as words ("2015 to 2025")
- captions added to the Chapter 6 charts and tables, which had none
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
A = HERE / "assets"


def items(name):
    return json.load(open(A / f"{name}.json"))


def undash(s):
    s = re.sub(r"(?<=[\w%])\s*[–—]\s*(?=[\w$])", " to ", s)
    s = s.replace("price to revenue relationship", "price and revenue relationship")
    s = s.replace("—", ", ").replace("–", " to ")
    return s


def renumber(s, ch):
    s = re.sub(r"\b(Figure|Table|Figures|Tables) (\d+)\b", lambda m: f"{m.group(1)} {ch}.{m.group(2)}", s)
    # "Figures 1 and 2" style pairs
    s = re.sub(rf"\b(Figures|Tables) {ch}\.(\d+) and (\d+)\b", lambda m: f"{m.group(1)} {ch}.{m.group(2)} and {ch}.{m.group(3)}", s)
    return s


def clean(s, ch):
    return renumber(undash(s), ch)


def unbold(s):
    return s.replace("**", "")


def chapter_head(title, author, date):
    return [("pagebreak",), ("h1", title), ("byline", [author, date])]


def body(name, ch, skip=(), heading_map=None, captions_after=False, extra_captions=None):
    """Generic walk: Figure/Table captions, images, notes, tables, lists, references."""
    its = items(name)
    out, pending_cap, refs, in_refs = [], None, [], False
    extra = list(extra_captions or [])
    i = 0
    while i < len(its):
        it = its[i]
        if i in skip:
            i += 1; continue
        if it[0] == "text":
            style, txt, listed = it[1], clean(it[2], ch), it[3]
            plain = unbold(txt).strip()
            if in_refs:
                refs.append(unbold(txt)); i += 1; continue
            if plain == "References":
                in_refs = True; i += 1; continue
            if heading_map and style in heading_map:
                out.append((heading_map[style], unbold(txt))); i += 1; continue
            if re.match(rf"^(Figure|Table) {ch}\.\d+\.", plain):
                if captions_after and out and out[-1][0] in ("figure_raw", "table_raw"):
                    kind, payload = out.pop()
                    note = None
                    if i + 1 < len(its) and its[i + 1][0] == "text" and unbold(its[i + 1][2]).startswith("Note."):
                        note = clean(unbold(its[i + 1][2]), ch); i += 1
                    out.append(_finish(kind, payload, plain, note))
                else:
                    pending_cap = plain
                i += 1; continue
            if plain.startswith("Note.") and out and out[-1][0] in ("figure", "table"):
                b = list(out[-1]); b[3] = clean(unbold(txt), ch); out[-1] = tuple(b); i += 1; continue
            if listed:
                if out and out[-1][0] == "bullets":
                    out[-1][1].append(txt)
                else:
                    out.append(("bullets", [txt]))
                i += 1; continue
            out.append(("p", txt)); i += 1; continue
        if it[0] == "image":
            cap = pending_cap
            if cap is None and not captions_after and extra:
                cap = extra.pop(0)
            if cap:
                out.append(("figure", it[1], cap, None)); pending_cap = None
            else:
                out.append(("figure_raw", it[1]))
            i += 1; continue
        if it[0] == "table":
            rows = [[clean(unbold(c), ch) for c in r] for r in it[1]]
            cap = pending_cap
            if cap is None and not captions_after and extra:
                cap = extra.pop(0)
            if cap:
                out.append(("table", rows[0], rows[1:], cap, None, None)); pending_cap = None
            else:
                out.append(("table_raw", rows))
            i += 1; continue
    if refs:
        out += [("h2", "References"), ("refs", refs)]
    return out


def _finish(kind, payload, caption, note):
    if kind == "figure_raw":
        return ("figure", payload, caption, note)
    return ("table", payload[0], payload[1:], caption, note, None)


# ---------------------------------------------------------------- Chapter 1
def ch1():
    return chapter_head("Chapter 1: Market Overview of Short-Term Rentals in Broward County",
                        "Harper Clark", "November 16, 2026") + body("ch1", 1, skip={0, 1, 2, 3})


# ------------------------------------------------------------ Chapters 2, 4
def ch24():
    blocks = body("ch24", 2, skip={0, 1}, heading_map={"Heading 1": "h2", "Heading 2": "h3"}, captions_after=True)
    fixed = []
    for b in blocks:
        if b[0] == "h2":
            t = re.sub(r"^Chapter (\d)\s+", r"Chapter \1: ", b[1])
            fixed.append(("h2", t))
        else:
            fixed.append(b)
    head = chapter_head("Chapters 2 and 4: Host Competition and Performance Drivers", "Jason Labrecque", "November 14, 2026")
    note = ("p", "*Chapters 2 and 4 were written as one piece because they share the same models: Chapter 2 asks whether professional hosts outperform independents, and Chapter 4 asks which listing traits drive performance. Their figures and tables are numbered 2.1, 2.2 and so on.*")
    return head + [note] + fixed


# ---------------------------------------------------------------- Chapter 3
def ch3():
    return chapter_head("Chapter 3: What Guests Say About Broward County Airbnb Stays",
                        "Matthew Sweeney", "November 16, 2026") + body("ch3", 3, skip={0, 1, 2, 3})


# ---------------------------------------------------------------- Chapter 6
CH6_CAPTIONS = [
    "Table 6.1. The three starter properties at the median revenue of established listings",
    "Table 6.2. Team data files used in this chapter",
    "Table 6.3. Cited cost rates",
    "Figure 6.1. Monthly costs and what an established Airbnb earns, by property type, September 2026",
    "Figure 6.2. Nights booked by established listings against the break-even point, before HOA",
    "Figure 6.3. Where December 2025 listings were nine months later",
    "Figure 6.4. Seasonal index of reviews, 2023 to 2025, with hurricane season shaded",
    "Figure 6.5. What it takes to turn the median listing positive: each assumption changed one at a time",
]


def ch6():
    blocks = body("ch6", 6, skip={0, 1}, heading_map={"Heading 1": "h2", "Heading 2": "h2", "Heading 3": "h3"},
                  extra_captions=CH6_CAPTIONS)
    out, after_method = [], False
    for b in blocks:
        if b[0] == "h2" and b[1] == "Summary":
            continue
        if b[0] == "h2":
            after_method = b[1] == "How I got there"
        if after_method and b[0] == "bullets":
            b = ("numbers", b[1]); after_method = False   # the method steps are a sequence
        out.append(b)
    # Table 6.3 has an empty source column for most rows; keep the authors' table as it is
    head = chapter_head("Chapter 6: Is It Worth Starting? Newcomer Break-Even in Broward",
                        "Chris Weihrauch", "October 30, 2026; revised November 17, 2026")
    return head + out


# ---------------------------------------------------------------- Chapter 5
def ch5():
    from ch5 import BLOCKS, F
    out = chapter_head("Chapter 5: The World Cup Stress Test", "Tim Goncharov", "November 22, 2026")
    for b in BLOCKS:
        if b[0] in ("title", "byline"):
            continue
        if b[0] == "p":
            out.append(("p", renumber(b[1], 5)))
        elif b[0] == "figure":
            out.append(("figure", b[1], renumber(b[2], 5), b[3]))
        elif b[0] == "table":
            out.append(("table", b[1], b[2], renumber(b[3], 5), b[4], b[5]))
        else:
            out.append(b)
    return out
