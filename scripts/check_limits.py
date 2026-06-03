"""Check JAWABAN_FORM word counts against OFFICIAL guidebook limits."""
import re, sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

text = (Path(__file__).resolve().parent.parent / "JAWABAN_FORM_PIDI_Tahap2.md").read_text(encoding="utf-8")

# Official limits (order matters — more specific keys first)
LIMITS = [
    ("Team Composition", 120), ("Executive Summary", 150),
    ("Problem Validation", 180), ("Problem.Solution Mapping", 180), ("Ecosystem Alignment", 150),
    ("Solution Approach", 250), ("Impact Scale", 230), ("Impact Measurement", 270),
    ("System . Public Value", 200),
    ("Solution Originality", 300), ("Technological", 240), ("Creativity", 250),
    ("System Architecture", 250), ("Data . Feasibility", 200), ("Security . Compliance", 200),
    ("Implementation Readiness", 300),
    ("Value Proposition", 220), ("Model Revenue", 200), ("Cost Structure", 200),
    ("Scalability", 170), ("Partnership", 170), ("Problem.Market Fit", 120),
    ("Evidence of Demand", 220), ("Target Market", 150), ("Adoption Readiness", 180),
    ("Progress Since", 150), ("Current Status", 50),
]

parts = re.split(r"\n## ([^\n]+)\n", text)
over = 0
for i in range(1, len(parts), 2):
    title = parts[i]
    body = re.sub(r"\*\([^)]*\)\*", "", parts[i + 1])
    wc = len([w for w in re.split(r"\s+", re.sub(r"[^\w\s]", " ", body)) if w])
    lim = None
    for k, v in LIMITS:
        if re.search(k, title):
            lim = v
            break
    if lim is None:
        print(f"  {title[:40]:42} {wc:4}")
        continue
    if wc <= lim:
        print(f"  {title[:40]:42} {wc:4} / {lim}   OK")
    else:
        over += 1
        print(f"  {title[:40]:42} {wc:4} / {lim}   >>> LEBIH {wc-lim} kata")
print(f"\nTotal section MELEBIHI limit: {over}")
