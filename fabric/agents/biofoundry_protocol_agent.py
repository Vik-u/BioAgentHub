#!/usr/bin/env python3
"""Generate biofoundry protocols from local module templates (no invented steps)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = PROJECT_ROOT / "ModuleTemplate"

TEMPLATES = {
    "ecoli_plate": TEMPLATE_DIR / "E.coli_plate_reader_protocol.md",
    "ecoli_echoms": TEMPLATE_DIR / "E.coli_EchoMS_protocol.md",
    "yeast_plate": TEMPLATE_DIR / "Yeast_plate_reader_protocol.md",
    "yeast_echoms": TEMPLATE_DIR / "Yeast_EchoMS_protocol.md",
}

CASE_MAP = {
    "petase": {"template": "ecoli_plate", "rationale": "E. coli expression, optical assays (plate reader)."},
    "3hp_pand": {"template": "ecoli_echoms", "rationale": "E. coli pathway, metabolite/product quant requires Echo-MS."},
    "retron": {
        "template": "ecoli_plate",
        "rationale": "E. coli build pipeline; templates cover cloning/assembly. Screening modules 6/7 may be skipped; genotyping TODO.",
    },
}


def load_template(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Template not found: {path}")
    return path.read_text()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=sorted(CASE_MAP.keys()), help="Case study key (petase, 3hp_pand, retron).")
    parser.add_argument("--out", type=Path, help="Optional output path for the assembled protocol.")
    args = parser.parse_args()

    choice: Dict[str, str] = CASE_MAP[args.case]
    template_key = choice["template"]
    template_path = TEMPLATES[template_key]
    content = load_template(template_path)

    header = (
        f"# Biofoundry protocol for {args.case}\n\n"
        f"Template: {template_path.name}\n"
        f"Rationale: {choice['rationale']}\n\n"
        "Note: Content is copied verbatim from the chosen template. "
        "Do not add steps, reagents, or instruments beyond what is listed here. "
        "If downstream screening/genotyping is needed (e.g., retron), add a TODO outside this file.\n\n"
    )
    assembled = header + content

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(assembled)
        print(f"Wrote protocol to {args.out}")
    else:
        print(assembled)


if __name__ == "__main__":
    main()
