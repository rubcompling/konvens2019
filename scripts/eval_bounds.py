#!/usr/bin/env python3

import sys
from pathlib import Path

import pandas as pd

# Paths that shouldn't change
SYSTEMS_DIR = Path("../data/system")
GOLD_DIR = Path("../data/gold/balanced")
RESULTS_DIR = Path("../eval")


def sentbounds_preprocess(tokenized_file):
    sentences = []
    with tokenized_file.open("r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue
            for c in line:
                if not c.isspace():
                    sentences.append(c)
            sentences.append("#BOUNDARY#")
    return sentences


def tokenbounds_preprocess(tokenized_file):
    tokens = []
    with tokenized_file.open("r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue
            for c in line:
                if c.isspace():
                    if tokens and tokens[-1] == "#BOUNDARY#":
                        continue
                    tokens.append("#BOUNDARY#")
                else:
                    tokens.append(c)
            if tokens and tokens[-1] == "#BOUNDARY#":
                continue
            tokens.append("#BOUNDARY#")
    return tokens


def compare_bounds(gold, annotation):
    a = 0
    g = 0
    data_rows = list()

    while g < len(gold):
        new_row = dict()

        # Automatic detection has boundary here:
        if annotation[a] == "#BOUNDARY#":
            new_row["sys_val"] = "BOUND"

            # Gold has boundary, too:
            if gold[g] == "#BOUNDARY#":
                new_row["gold_val"] = "BOUND"

                # True positive.
                new_row["correct"] = "TP"

                a += 1
                g += 1

            # Gold has no boundary here:
            else:
                new_row["gold_val"] = "NONE"

                # False positive.
                new_row["correct"] = "FP"

                a += 1

        # Gold has boundary but automatic detection has not:
        elif gold[g] == "#BOUNDARY#":
            new_row["gold_val"] = "BOUND"
            new_row["sys_val"] = "NONE"

            # False negative.
            new_row["correct"] = "FN"

            g += 1

        # No boundary here in Gold or automatic detection:
        else:
            new_row["gold_val"] = "NONE"
            new_row["sys_val"] = "NONE"
            new_row["correct"] = "TN"
            a += 1
            g += 1

        data_rows.append(new_row)
    return data_rows


if __name__ == "__main__":

    all_systems = [p.name for p in SYSTEMS_DIR.iterdir()]

    all_data_rows = list()

    # Read gold data
    gold_files = sorted(GOLD_DIR.joinpath("tokens").iterdir())

    for sys_name in all_systems:
        anno_files_path = SYSTEMS_DIR / sys_name / "tokens"
        if anno_files_path.exists():
            anno_files = sorted(p for p in anno_files_path.iterdir())
        else:
            # skip systems that don't have the annotation level
            # we're interested in
            continue

        for goldfile, sysfile in zip(gold_files, anno_files):
            gold_sentbounds = sentbounds_preprocess(goldfile)
            sys_sentbounds = sentbounds_preprocess(sysfile)
            sent_results = compare_bounds(gold_sentbounds, sys_sentbounds)
            for row in sent_results:
                row.update(
                    {
                        "annotation": "sentences",
                        "genre": goldfile.stem,
                        "system": sys_name,
                    }
                )

            gold_tokenbounds = tokenbounds_preprocess(goldfile)
            sys_tokenbounds = tokenbounds_preprocess(sysfile)
            tok_results = compare_bounds(gold_tokenbounds, sys_tokenbounds)
            for row in tok_results:
                row.update(
                    {"annotation": "tokens", "genre": goldfile.stem, "system": sys_name}
                )

            all_data_rows.extend(sent_results)
            all_data_rows.extend(tok_results)

    # results auch in eine pandas DataFrame speichern:
    # damit können wir einfacherweise Statistiken berechnen
    # und direkt Latex-Tabellen daraus generieren -> analysis.py
    results = pd.DataFrame(
        all_data_rows,
        columns=[
            "annotation",
            "genre",
            "system",
            "token",
            "pos",
            "gold_val",
            "sys_val",
            "correct",
            "degree",
            "case",
            "number",
            "gender",
            "definite",
            "person",
            "tense",
            "mood",
        ],
    )
    results.to_csv(sys.stdout)
