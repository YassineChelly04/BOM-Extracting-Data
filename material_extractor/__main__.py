"""Command-line entry point.

    python -m material_extractor <file-or-dir> [--output OUTDIR]

Examples:
    python -m material_extractor templates/test_files
    python -m material_extractor ../Data

By default results are written to the package's own ``output/`` folder
(``material_extractor/output``), regardless of the current directory.
"""
from __future__ import annotations
import argparse
from pathlib import Path

from material_extractor.pipeline import run

# results live alongside the package, not wherever the command was launched
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output"


def main() -> None:
    parser = argparse.ArgumentParser(prog="material_extractor",
                                     description="Extract material composition from supplier PDFs/XLSXs.")
    parser.add_argument("input", type=Path, help="File or directory to process")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT,
                        help="Output directory (default: material_extractor/output)")
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"input not found: {args.input}")

    results = run(args.input, args.output)

    matched = [r for r in results if r.matched and r.records]
    unmatched = [r for r in results if not r.matched]
    errored = [r for r in results if r.error]

    print(f"\nProcessed {len(results)} file(s):")
    for r in results:
        if r.error:
            status = f"ERROR ({r.error})"
        elif r.matched and r.records:
            status = f"{r.template} -> {len(r.records)} materials"
        elif r.matched:
            status = f"{r.template} -> 0 materials"
        else:
            status = "no template matched"
        print(f"  {Path(r.source_file).name:35} {status}")

    print(f"\n{len(matched)} matched, {len(unmatched)} unmatched, {len(errored)} errored.")
    if matched:
        print(f"Report written to {args.output / 'all_materials.csv'}")


if __name__ == "__main__":
    main()
