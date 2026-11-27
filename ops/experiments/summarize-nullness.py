#!/usr/bin/env python3
"""Summarize a complete Maven core nullness audit without counting repeats twice."""

import argparse
from collections import Counter
import csv
from pathlib import Path
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--csv", type=Path, help="write individual diagnostic sites")
    args = parser.parse_args()
    text = re.sub(r"\x1b\[[0-9;]*m", "", args.log.read_text())
    modules = dict.fromkeys(("swrlapi", "swrlapi-drools-engine", "swrlapi-example"), 0)
    if "BUILD SUCCESS" not in text or "[ERROR]" in text:
        parser.error("audit did not complete successfully; inspect the original log")
    for module in modules:
        pattern = (r"--- compiler:[^\n]+:compile \(default-compile\) @ "
                   + re.escape(module) + r" ---(?:(?!---).)*?Compiling (\d+) source files?")
        match = re.search(pattern, text, re.S)
        if not match or int(match[1]) == 0:
            parser.error(f"no fresh compilation recorded for {module}; run clean compile")
        if f":enforce (nullness-build-jdk) @ {module} ---" not in text:
            parser.error(f"nullness profile was not recorded for {module}")
        modules[module] = int(match[1])
    matches = re.findall(
        r"\[WARNING\] (.*?\.java):\[(\d+),(\d+)\] \[([^]]+)\] (.*)", text)
    if not matches:
        subprocess.run([sys.executable, str(Path(__file__).with_name("check-nullness-profile.py"))], check=True)
    rows = []
    for path, line, column, key, message in sorted(set(matches)):
        module, source = path.split("/src/main/java/", 1)
        module = Path(module).name
        if module not in modules:
            parser.error(f"unexpected module {module}")
        category = ("placement" if key.startswith("type.anno.") else
                    "primitive annotation" if key == "nullness.on.primitive" else "contract")
        rows.append((module, source, int(line), int(column), key, category, message))
    print(f"Compiled sources: {sum(modules.values())} {modules}")
    print(f"Raw diagnostics: {len(matches)}; distinct diagnostic sites: {len(rows)}")
    for module in modules:
        selected = [r for r in rows if r[0] == module]
        print(f"{module}: {dict(Counter(r[5] for r in selected))}")
    contracts = [r for r in rows if r[5] == "contract"]
    print(f"Contract findings: {len(contracts)} in {len(set((r[0], r[1]) for r in contracts))} files")
    print(f"Contract categories: {dict(Counter(r[4] for r in contracts).most_common())}")
    if args.csv:
        with args.csv.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("module", "source", "line", "column", "key", "category", "message"))
            writer.writerows(rows)


if __name__ == "__main__":
    main()
