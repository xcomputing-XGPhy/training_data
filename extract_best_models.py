#!/usr/bin/env python3
"""
Extract best models from rand.iqtree files in an IQ-TREE results directory.
"""

import argparse
import csv
import json
import os
import re
from pathlib import Path


MODEL_PATTERNS = [
    r"^Best-fit model according to .*?:\s*(.+)$",
    r"^Best-fit model:\s*(.+)$",
    r"^Model of evolution:\s*(.+)$",
]


def extract_best_model_from_iqtree(iqtree_file):
    try:
        content = iqtree_file.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        print(f"  Error reading {iqtree_file}: {exc}")
        return None

    for pattern in MODEL_PATTERNS:
        match = re.search(pattern, content, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()

    return None


def infer_msa_name(rand_iqtree, results_dir):
    relative_parts = rand_iqtree.relative_to(results_dir).parts
    if "output_files" in relative_parts:
        output_files_index = relative_parts.index("output_files")
        if output_files_index > 0:
            return relative_parts[output_files_index - 1]
    return rand_iqtree.parent.name


def scan_rand_iqtree_files(results_dir, rand_filename="rand.iqtree"):
    results_dir = Path(results_dir).resolve()
    print(f"\n{'=' * 80}")
    print(f"Scanning for {rand_filename}: {results_dir}")
    print(f"{'=' * 80}\n")

    if not results_dir.is_dir():
        print(f"Error: Directory {results_dir} not found")
        return {}

    rand_files = sorted(results_dir.rglob(rand_filename))
    print(f"Found {len(rand_files)} {rand_filename} files\n")

    best_models = {}
    for index, rand_iqtree in enumerate(rand_files, start=1):
        msa_name = infer_msa_name(rand_iqtree, results_dir)
        model = extract_best_model_from_iqtree(rand_iqtree)
        source = str(rand_iqtree.relative_to(results_dir))

        if model:
            print(f"{index:4}. {msa_name:40} -> {model:20} ({source})")
            best_models[msa_name] = {
                "model": model,
                "source": source,
            }
        else:
            print(f"{index:4}. {msa_name:40} -> (khong tim duoc model) ({source})")

    print(f"\n{'=' * 80}")
    print(f"Summary: Extracted {len(best_models)} models from {len(rand_files)} files")
    print(f"{'=' * 80}\n")
    return best_models


def save_results(best_models, output_csv, output_json):
    print("Saving results:")
    print(f"{'=' * 80}\n")

    try:
        with open(output_csv, "w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["msa_file", "best_model", "source"])
            writer.writeheader()
            for msa_name, info in sorted(best_models.items()):
                writer.writerow(
                    {
                        "msa_file": msa_name,
                        "best_model": info["model"],
                        "source": info["source"],
                    }
                )
        print(f"Saved CSV:  {os.path.abspath(output_csv)}")
    except Exception as exc:
        print(f"Error saving CSV: {exc}")

    try:
        with open(output_json, "w") as handle:
            json.dump(best_models, handle, indent=2)
        print(f"Saved JSON: {os.path.abspath(output_json)}")
    except Exception as exc:
        print(f"Error saving JSON: {exc}")

    print(f"\n{'=' * 80}\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract one best model per MSA from rand.iqtree files."
    )
    parser.add_argument(
        "results_dir",
        nargs="?",
        default=None,
        help="Root results directory. If omitted, the script asks interactively.",
    )
    parser.add_argument(
        "--rand-filename",
        default="rand.iqtree",
        help="IQ-TREE filename to scan for. Default: rand.iqtree",
    )
    parser.add_argument(
        "--output-csv",
        default=None,
        help="Output CSV path. Default: <results_dir>/extracted_115_models.csv",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Output JSON path. Default: <results_dir>/extracted_115__models.json",
    )
    return parser.parse_args()


def main():
    print("\n" + "=" * 80)
    print("IQ-TREE rand.iqtree Best Model Extractor")
    print("=" * 80)

    args = parse_args()
    results_dir = args.results_dir
    if not results_dir:
        results_dir = input("\nEnter results directory path (or press Enter for current dir): ").strip()
    if not results_dir:
        results_dir = os.getcwd()

    results_dir = Path(results_dir).resolve()
    best_models = scan_rand_iqtree_files(results_dir, args.rand_filename)
    if not best_models:
        print("No models found!")
        return

    output_csv = args.output_csv or results_dir / "extracted_115_models.csv"
    output_json = args.output_json or results_dir / "extracted_115_models.json"
    save_results(best_models, output_csv, output_json)


if __name__ == "__main__":
    main()

