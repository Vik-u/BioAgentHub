#!/usr/bin/env python3
"""Create a structured instrument inventory from 08_Instrument_Docs/."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Dict, List, Sequence

from pypdf import PdfReader

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
CAPABILITY_KEYWORDS = [
    "µl",
    "ul",
    "well",
    "plate",
    "temperature",
    "°c",
    "incubator",
    "dispense",
    "throughput",
    "transfer",
    "automation",
    "storage",
    "humidity",
    "speed",
    "rpm",
    "centrifuge",
]
USE_CASE_KEYWORDS = {
    "dispense": ["dispense", "filling", "reagent"],
    "pcr": ["pcr", "qpcr", "amplification"],
    "incubation": ["incubat", "culture", "cell"],
    "screening": ["screening", "assay", "high-throughput"],
    "labeling": ["label", "barcode"],
    "centrifuge": ["centrifuge", "spin"],
    "spectrometry": ["mass spectrometer", "ms/ms", "proteomic"],
    "purification": ["purification", "extraction", "magnetic beads"],
}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "08_Instrument_Docs"
OUT_DIR = PROJECT_ROOT / "InstrumentGraph"
OUT_PATH = OUT_DIR / "inventory.json"

CATEGORY_OVERRIDES: Dict[str, str] = {
    "Agilent BioTek MultiFlo FX": "Reagent dispenser",
    "Applied Biosystems QuantStudio 7 Pro": "qPCR / RT-PCR",
    "Azenta Life Sciences XPeel": "Plate seal remover",
    "Beckman Coulter ECHO 650": "Acoustic liquid handler",
    "BioNex HiG3 Automated Centrifuge": "Plate centrifuge",
    "KingFisher Presto Purification System": "Magnetic-bead purification",
    "Multidrop Combi+ Microplate Dispenser": "Bulk dispenser",
    "Sci-Print MP2 Plate Labeler": "Plate labeler",
    "Singer Instruments PIXL": "Colony picker",
    "Tecan Fluent 1080": "Liquid handler",
    "Tecan Spark Reader": "Multimode plate reader",
    "Thermo Scientific ALPS 5000 Plate Sealer": "Plate sealer",
    "Thermo Scientific Cytomat 10 C450 R3 Lift": "Automated incubator",
    "Thermo Scientific Cytomat 2 C450-Lin B1 ToS": "Automated incubator",
    "Thermo Scientific Cytomat SkyLine": "Incubator / storage",
    "ZenoTOF 7600+ System": "Mass spectrometer",
}


def gather_manuals(path: Path) -> List[Dict[str, object]]:
    manuals: List[Dict[str, object]] = []
    for file_path in sorted(path.glob("*")):
        if file_path.is_file():
            manuals.append(
                {
                    "file": file_path.name,
                    "relative_path": str(file_path.relative_to(PROJECT_ROOT)),
                    "size_bytes": file_path.stat().st_size,
                }
            )
    return manuals


def extract_pdf_sentences(pdf_path: Path, max_pages: int = 5) -> List[str]:
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return []
    texts: List[str] = []
    for page in reader.pages[:max_pages]:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    combined = " ".join(texts)
    return [sentence.strip() for sentence in SENTENCE_SPLIT.split(combined) if sentence.strip()]


def select_capabilities(sentences: Sequence[str], limit: int = 6) -> List[str]:
    selected: List[str] = []
    for sentence in sentences:
        lower = sentence.lower()
        if any(keyword in lower for keyword in CAPABILITY_KEYWORDS):
            selected.append(sentence)
        if len(selected) >= limit:
            break
    return selected


def infer_use_cases(sentences: Sequence[str]) -> List[str]:
    uses: List[str] = []
    for label, keywords in USE_CASE_KEYWORDS.items():
        if any(keyword in sentence.lower() for sentence in sentences for keyword in keywords):
            uses.append(label)
    return uses


def build_inventory() -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    for instrument_dir in sorted(DOCS_DIR.iterdir()):
        if not instrument_dir.is_dir():
            continue
        name = instrument_dir.name
        manuals = gather_manuals(instrument_dir)
        sentences: List[str] = []
        for manual in manuals:
            pdf_path = PROJECT_ROOT / manual["relative_path"]
            sentences.extend(extract_pdf_sentences(pdf_path))
        capabilities = select_capabilities(sentences)
        use_cases = infer_use_cases(sentences)
        meta_capabilities = capabilities if capabilities else ["No capability sentences extracted (check PDFs)."]
        meta_use_cases = use_cases if use_cases else ["unspecified"]
        entry = {
            "name": name,
            "category": CATEGORY_OVERRIDES.get(name, "unspecified"),
            "capabilities": meta_capabilities,
            "use_cases": meta_use_cases,
            "manual_count": len(manuals),
            "manuals": manuals,
        }
        entries.append(entry)
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DOCS_DIR,
        help="Directory containing instrument manuals.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUT_PATH,
        help="Where to write the instrument inventory JSON.",
    )
    args = parser.parse_args()

    if not args.docs_dir.exists():
        raise SystemExit(f"Instrument docs directory not found: {args.docs_dir}")

    inventory = build_inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2))
    print(f"Wrote instrument inventory for {len(inventory)} instruments to {args.output}")


if __name__ == "__main__":
    main()
