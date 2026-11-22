"""Shared Word styling for the combined report and stand-alone chapters.

Blocks are simple tuples so every chapter is written the same way:
  ("title", text) ("byline", [lines]) ("h1", text) ("h2", text) ("h3", text)
  ("p", text)      text may use **bold** and *italic*
  ("bullets", [text, ...]) ("numbers", [text, ...])
  ("figure", image_path, caption, note)   note may be None
  ("table", header, rows, caption, note, col_widths_in_inches or None)
  ("refs", [text, ...])  hanging-indent reference list
  ("pagebreak",)
"""
import re
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

BODY_FONT = "Calibri"
INK = RGBColor(0x1F, 0x2A, 0x37)
ACCENT = RGBColor(0x1F, 0x4E, 0x79)
MUTED = RGBColor(0x55, 0x60, 0x6B)
TEXT_WIDTH_IN = 6.5


def _set_font(style, size, bold=False, italic=False, color=INK):
    f = style.font
    f.name = BODY_FONT
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = color
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
    for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(k), BODY_FONT)


def new_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Inches(1))
    st = doc.styles
    _set_font(st["Normal"], 11)
    pf = st["Normal"].paragraph_format
    pf.space_after = Pt(8); pf.line_spacing = 1.15
    for name, size, before, after in (("Title", 22, 0, 6), ("Heading 1", 16, 18, 8), ("Heading 2", 13, 14, 6), ("Heading 3", 11.5, 10, 4)):
        s = st[name]
        _set_font(s, size, bold=True, color=ACCENT if name != "Heading 3" else INK)
        s.paragraph_format.space_before = Pt(before)
        s.paragraph_format.space_after = Pt(after)
        s.paragraph_format.keep_with_next = True
        # Title style has a bottom border in the default template; keep it simple
    _set_font(st["Caption"], 10, bold=True, color=INK)
    st["Caption"].paragraph_format.space_before = Pt(4)
    st["Caption"].paragraph_format.space_after = Pt(2)
    st["Caption"].paragraph_format.keep_with_next = True
    for lst in ("List Bullet", "List Number"):
        _set_font(st[lst], 11)
        st[lst].paragraph_format.space_after = Pt(4)
    # the default template's <w:zoom> lacks the required percent attribute
    z = doc.settings.element.find(qn("w:zoom"))
    if z is not None: z.set(qn("w:percent"), "100")
    # page numbers in the footer
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _field(p, "PAGE")
    return doc


def _field(paragraph, code):
    run = paragraph.add_run()
    for tag, text in (("begin", None), (None, code), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), tag); run._r.append(el)
        else:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = f" {text} "; run._r.append(el)
    run.font.size = Pt(9); run.font.color.rgb = MUTED


def add_rich(paragraph, text, size=None, color=None, italic=False):
    # **bold** and *italic* markup
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("**"):
            r = paragraph.add_run(part[2:-2]); r.bold = True
        elif part.startswith("*"):
            r = paragraph.add_run(part[1:-1]); r.italic = True
        else:
            r = paragraph.add_run(part)
        if size: r.font.size = Pt(size)
        if color is not None: r.font.color.rgb = color
        if italic: r.italic = True
    return paragraph


def _shade(cell, hex_fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill)
    tcpr.append(shd)


def _borders(table):
    tblpr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "insideH"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "A6B1BC"); b.append(e)
    for edge in ("left", "right", "insideV"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "nil"); b.append(e)
    tblpr.append(b)


def render(doc, blocks, base_dir="."):
    from pathlib import Path
    for b in blocks:
        kind = b[0]
        if kind == "title":
            p = doc.add_paragraph(style="Title"); add_rich(p, b[1])
        elif kind == "byline":
            for line in b[1]:
                p = doc.add_paragraph(); add_rich(p, line, size=10.5, color=MUTED)
                p.paragraph_format.space_after = Pt(0)
            doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
        elif kind in ("h1", "h2", "h3"):
            p = doc.add_paragraph(style={"h1": "Heading 1", "h2": "Heading 2", "h3": "Heading 3"}[kind]); add_rich(p, b[1])
        elif kind == "p":
            add_rich(doc.add_paragraph(), b[1])
        elif kind == "bullets":
            for item in b[1]:
                add_rich(doc.add_paragraph(style="List Bullet"), item)
        elif kind == "numbers":
            # numbered by hand so each list starts at 1 in a long document
            for k, item in enumerate(b[1], start=1):
                p = doc.add_paragraph(); add_rich(p, f"{k}.\t" + item)
                p.paragraph_format.left_indent = Inches(0.35); p.paragraph_format.first_line_indent = Inches(-0.35)
                p.paragraph_format.tab_stops.add_tab_stop(Inches(0.35)); p.paragraph_format.space_after = Pt(5)
        elif kind == "figure":
            _, path, caption, note = b[:4]
            width = b[4] if len(b) > 4 else TEXT_WIDTH_IN
            cap = doc.add_paragraph(style="Caption"); add_rich(cap, caption)
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = bool(note)
            p.add_run().add_picture(str(Path(base_dir) / path), width=Inches(width))
            if note:
                n = doc.add_paragraph(); add_rich(n, note, size=9.5, color=MUTED); n.paragraph_format.space_after = Pt(12)
        elif kind == "table":
            _, header, rows, caption, note, widths = b
            cap = doc.add_paragraph(style="Caption"); add_rich(cap, caption)
            t = doc.add_table(rows=1 + len(rows), cols=len(header))
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            t.autofit = False
            _borders(t)
            for j, h in enumerate(header):
                c = t.rows[0].cells[j]; c.text = ""
                add_rich(c.paragraphs[0], f"**{h}**", size=9.5); _shade(c, "E8EEF4")
            for i, row in enumerate(rows, start=1):
                for j, v in enumerate(row):
                    c = t.rows[i].cells[j]; c.text = ""
                    add_rich(c.paragraphs[0], str(v), size=9.5)
            for row in t.rows:
                for j, c in enumerate(row.cells):
                    c.paragraphs[0].paragraph_format.space_after = Pt(1)
                    c.paragraphs[0].paragraph_format.line_spacing = 1.0
                    # center short values (numbers); leave sentences left-aligned
                    if j > 0 and max(len(r.cells[j].text) for r in t.rows) <= 28:
                        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    if widths: c.width = Inches(widths[j])
            if widths:
                grid = t._tbl.tblGrid
                for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
                    gc.set(qn("w:w"), str(int(widths[j] * 1440)))
            if note:
                n = doc.add_paragraph(); add_rich(n, note, size=9.5, color=MUTED)
                n.paragraph_format.space_before = Pt(4); n.paragraph_format.space_after = Pt(12)
            else:
                doc.add_paragraph()
        elif kind == "refs":
            for r in b[1]:
                p = doc.add_paragraph(); add_rich(p, r, size=10)
                p.paragraph_format.left_indent = Inches(0.5); p.paragraph_format.first_line_indent = Inches(-0.5)
                p.paragraph_format.space_after = Pt(4)
        elif kind == "cover":
            d = b[1]
            for _ in range(6):
                doc.add_paragraph()
            p = doc.add_paragraph(style="Title"); add_rich(p, d["title"])
            p = doc.add_paragraph(); add_rich(p, d["subtitle"], size=13, color=MUTED)
            p.paragraph_format.space_after = Pt(36)
            for line in d["lines"]:
                p = doc.add_paragraph(); add_rich(p, line, size=11.5)
                p.paragraph_format.space_after = Pt(2)
        elif kind == "contents":
            for title, sub in b[1]:
                p = doc.add_paragraph(); add_rich(p, f"**{title}**")
                if sub:
                    p.add_run("\n")
                    add_rich(p, sub, size=10, color=MUTED)
                p.paragraph_format.space_after = Pt(6)
        elif kind == "pagebreak":
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        else:
            raise ValueError(kind)
    return doc
