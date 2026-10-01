"""Deterministic integer CSV aggregation; Python standard library only."""
import argparse
import csv
import json
from pathlib import Path


def summarize(path):
    totals = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            name, value = row["name"], int(row["value"])
            totals[name] = totals.get(name, 0) + value
    return totals


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must be distinct")
    args.output.write_text(json.dumps(summarize(args.input), ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
