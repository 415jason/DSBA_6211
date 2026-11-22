import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from style import new_document, render
from ch5 import BLOCKS
here = Path(__file__).parent
doc = render(new_document(), BLOCKS, base_dir=here)
out = here.parent / "Ch5_World_Cup_Stress_Test.docx"
doc.save(out); print("wrote", out)
