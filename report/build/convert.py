"""Read a chapter .docx into a flat list of items, in document order.

Items: ("text", style, text_with_bold_markup, numbered_or_bulleted)
       ("image", saved_png_path)   ("table", rows)
The chapter modules (ch1.py, ...) turn these into report blocks.
"""
import json, sys
from pathlib import Path
import docx
from docx.oxml.ns import qn

def run_text(p):
    out = []
    for r in p.runs:
        t = r.text
        if not t:
            continue
        if r.bold and t.strip():
            lead = t[: len(t) - len(t.lstrip())]; trail = t[len(t.rstrip()):]
            out.append(f"{lead}**{t.strip()}**{trail}")
        else:
            out.append(t)
    s = "".join(out).replace("****", "")
    return s

def read(path, prefix, assets):
    d = docx.Document(path)
    rels = d.part.rels
    items = []; k = 0
    for el in d.element.body.iterchildren():
        if el.tag == qn("w:p"):
            p = docx.text.paragraph.Paragraph(el, d)
            for blip in el.iter(qn("a:blip")):
                rid = blip.get(qn("r:embed"))
                part = rels[rid].target_part
                k += 1
                ext = Path(part.partname).suffix or ".png"
                out = Path(assets) / f"{prefix}_{k}{ext}"
                out.write_bytes(part.blob)
                items.append(["image", str(out)])
            txt = run_text(p).strip()
            if txt:
                listed = el.find(qn("w:pPr")) is not None and el.find(qn("w:pPr")).find(qn("w:numPr")) is not None
                items.append(["text", p.style.name, txt, bool(listed or "List" in p.style.name)])
        elif el.tag == qn("w:tbl"):
            t = docx.table.Table(el, d)
            rows = []
            for row in t.rows:
                cells = []
                for c in row.cells:
                    cells.append(" ".join(run_text(pp).strip() for pp in c.paragraphs if run_text(pp).strip()))
                rows.append(cells)
            items.append(["table", rows])
    return items

if __name__ == "__main__":
    src, prefix = sys.argv[1], sys.argv[2]
    items = read(src, prefix, Path(__file__).parent / "assets")
    json.dump(items, open(Path(__file__).parent / "assets" / f"{prefix}.json", "w"), indent=1, ensure_ascii=False)
    print(prefix, len(items), "items")
