"""Build the combined report: python3 make_report.py (run from report/build)."""
from pathlib import Path
import chapters, frontmatter as fm
from style import new_document, render

HERE = Path(__file__).parent
OUT = HERE.parent / "Broward_Airbnb_Final_Report.docx"

blocks = (fm.TITLE_PAGE + [("pagebreak",)] + fm.CONTENTS + fm.SUMMARY + fm.QUESTION_MAP + fm.DATA_METHODS
          + chapters.ch1() + chapters.ch24() + chapters.ch3() + chapters.ch5() + chapters.ch6()
          + fm.ADDITIONAL_DATA + [("pagebreak",)] + fm.AI_STATEMENT + [("pagebreak",)] + fm.APPENDIX)

# chapter figure paths are relative to report/build (assets/) or to ch5's notebook figures folder
doc = render(new_document(), blocks, base_dir=HERE)
doc.core_properties.title = "Who Wins Broward County's Airbnb Market?"
doc.core_properties.author = "Harper Clark, Tim Goncharov, Jason Labrecque, Matthew Sweeney, Chris Weihrauch"
doc.save(OUT)
print("wrote", OUT)
