#!/usr/bin/env python3

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

# Paths that shouldn't change
SYSTEMS_DIR = Path("../data/system")
GOLD_DIR = Path("../data/gold")
RESULTS_DIR = Path("../eval")


def precision(series):
    tp = series[series == "TP"].size
    fp = series[series == "FP"].size
    try:
        return tp / (tp + fp)
    except ZeroDivisionError:
        return np.nan


def recall(series):
    tp = series[series == "TP"].size
    fn = series[series == "FN"].size
    try:
        return tp / (tp + fn)
    except ZeroDivisionError:
        return np.nan


def f1score(series):
    p = precision(series)
    r = recall(series)
    try:
        return (2 * p * r) / (p + r)
    except ZeroDivisionError:
        return np.nan


def acc_or_fscore(col):
    try:
        # for most anno levels, we can say a value is either
        # right or wrong: 1 or 0 -- when we code it this
        # way we can get accuracy just by taking the mean
        return col.apply(float).mean()
    except ValueError:
        # if there's something non-floaty in the column, i.e.
        # one of {TN, TP, FN, FP}, then calc F1-score instead
        return f1score(col)


system_name_fmt = {
    "clevertagger": "Clevertagger",
    "syntok": "Syntok",
    "customlemmatizer": "GermaLemma++",
    "nltk": "NLTK",
    "somajo": "SoMaJo",
    "germalemma": "GermaLemma",
    "rftagger": "RFTagger",
    "corenlp": "CoreNLP",
    "stanfordnlp": "StanfordNLP",
    "spacy": "spaCy",
    "rnntagger": "RNNTagger",
    "treetagger": "TreeTagger",
    "someweta": "SoMeWeTa",
    "parzu": "ParZu",
    "iwnlp": "IWNLP",
    "spacydepsents": "spaCy parser",
}

level_name_fmt = {
    "lemmas": "Lemmas",
    "depparse": "Dependencies",
    "tokens": "Tokens",
    "morph": "Morph",
    "pos": "POS",
    "sentences": "Sents",
    "case": "Case",
    "degree": "Degree",
    "gender": "Gender",
    "mood": "Mood",
    "number": "Number",
    "person": "Person",
    "tense": "Tense",
}


if __name__ == "__main__":

    # be careful about what subdirs are in SYSTEMS_DIR!
    # unexpected subdirs can cause unexpected behaviors, missing cols, etc.
    all_systems = list(p.name for p in SYSTEMS_DIR.iterdir())
    all_anno_levels = ["tokens", "sentences", "pos", "morph", "lemmas", "depparse"]

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-a", "--annotations", nargs="+", choices=all_anno_levels)
    argparser.add_argument(
        "-s",
        "--systems",
        nargs="+",
        choices=all_systems,
        help="list of system names (lowercase) to include (default: all)",
    )
    argparser.add_argument("-d", "--debug", action="store_true")
    args = argparser.parse_args()

    # read results.csv
    results = pd.read_csv(Path("../eval/results.csv"), index_col=0)

    # do analysis
    # maybe differentiate between debugging and producing
    if args.debug:
        print("error analysis:")
        sys_filtered = results[results.system.isin(args.systems)]

        for annolevel in args.annotations:
            print("for anno level:", annolevel)
            if annolevel in {"tokens", "sentences"}:
                confmat = (
                    sys_filtered.query(f"annotation == '{annolevel}' & correct != 'TP'")
                    .groupby(["gold_val", "sys_val"])
                    .size()
                    .sort_values()
                )
            else:
                confmat = (
                    sys_filtered.query(f"annotation == '{annolevel}' & correct == 0")
                    .groupby(["gold_val", "sys_val"])
                    .size()
                    .sort_values()
                )
        print(confmat)

    else:
        outfile = Path("../eval/output_tables.tex").open("w", encoding="utf-8")
        print(f"writing tables to {outfile.name}")

        # analyses for publication
        # generate tables / figures

        # 1. accuracy/f1score table
        # Overview: Systems vs Annotation levels
        crosstabbed = pd.crosstab(
            results.system,
            results.annotation,
            aggfunc=acc_or_fscore,
            values=results.correct,
        )[all_anno_levels].rename(index=system_name_fmt, columns=level_name_fmt)

        # a few corrections:
        # remove "baseline" vals from table
        lemmas_baseline = crosstabbed["Lemmas"]["Clevertagger"]
        # these are the three POS-level systems that do not do lemmas
        crosstabbed["Lemmas"]["Clevertagger"] = np.nan
        crosstabbed["Lemmas"]["CoreNLP"] = np.nan
        crosstabbed["Lemmas"]["SoMeWeTa"] = np.nan

        # sentences from spacy-parser: remove doubled token val
        crosstabbed["Tokens"]["spaCy parser"] = np.nan

        print(f"Lemmatization baseline = {lemmas_baseline}")

        def bold(s):
            return r"\textbf{" + normal(s) + r"}"

        def normal(s):
            return "--" if pd.isna(s) or s == 0.00 else "%.4f" % s

        maxes = [crosstabbed[col].max() for col in crosstabbed]

        def myformatter(x: float) -> str:
            if x > 0.0 and x in maxes:
                maxes.pop(maxes.index(x))
                return bold(x)
            else:
                return normal(x)

        print(
            crosstabbed.to_latex(float_format=myformatter, escape=False), file=outfile
        )

        sns.set(font="Arial")
        # also produce a heatmap for accuracies
        # (but first take out the zeroes which mess up the colors)
        crosstabbed.replace(0.0, np.nan, inplace=True)
        crosstabbed = crosstabbed.rename(columns={"Dependencies": "Deps"})
        plt.figure()
        acc_hmap = sns.heatmap(
            crosstabbed,
            annot=True,
            cmap=sns.color_palette("coolwarm_r", 100),
            robust=True,
            fmt=".3f",
        )
        acc_hmap.set_ylabel("")
        acc_hmap.set_xlabel("")
        acc_hmap.tick_params(axis="both", which="both", length=0)
        acc_fig = acc_hmap.get_figure()
        acc_fig.set_tight_layout(True)
        acc_fig.savefig("../eval/accplot.png", dpi=400)

        # 2. make timing table for each annotation level

        timing = pd.read_csv(
            "../eval/timing.csv",
            sep="\t",
            header=None,
            names=[
                "system",
                "domain",
                "annotation",
                "model_load_time",
                "run_time",
                "process_time",
                "exp_exec_time",
            ],
        )

        #  old (unbalanced) data
        # text_lengths = {
        #     "wikipedia": 1575,
        #     "novelette": 2499,
        #     "sermononline": 1646,
        #     "ted": 1482,
        #     "opensubtitles": 702,
        # }
        text_lengths = {
            "wikipedia": 1514,
            "novelette": 1588,
            "sermononline": 1520,
            "ted": 1506,
            "opensubtitles": 1514,
        }
        timing["num_tokens"] = timing.domain.apply(lambda x: text_lengths.get(x))
        timing["secs_per_1ktoken"] = (timing.process_time / timing.num_tokens) * 1000

        # timing_levels = ["tokens", "pos", "lemmas", "depparse"]
        # for level in timing_levels:
        #     print(f"Table for {level}", file=outfile)
        #     grouped = (
        #         timing.query(f"annotation == '{level}'")
        #         .groupby("system")
        #         .secs_per_1ktoken.agg(["mean", "std"])
        #         .rename(index=system_name_fmt)
        #     )
        #     print(grouped.to_latex(escape=False), file=outfile)
        xtab_time = pd.crosstab(
            timing.system,
            timing.annotation,
            values=timing.secs_per_1ktoken,
            aggfunc="mean",
        )
        plt.figure()
        time_plot = sns.heatmap(
            xtab_time[["tokens", "pos", "lemmas", "depparse"]].rename(
                index=system_name_fmt,
                columns={
                    "tokens": "Tokenization",
                    "lemmas": "Lemmas",
                    "pos": "Word-Level",
                    "depparse": "Dependencies",
                },
            ),
            annot=True,
            cmap=sns.color_palette("coolwarm", 100),
            robust=True,
        )
        time_plot.set_ylabel("")
        time_plot.set_xlabel("")
        time_plot.tick_params(axis="both", which="both", length=0)
        time_fig = time_plot.get_figure()
        time_fig.set_tight_layout(True)
        time_fig.savefig("../eval/timingplot.png", dpi=400)

        # 3. accuracy per morph feature (TODO)
        # + wenn POS correct und sonst
        morphcols = ["case", "degree", "gender", "mood", "number", "person", "tense"]
        aggmorph = (
            results[results.annotation == "morph"].groupby(["system"]).agg("mean")
        )
        # filtering according to case vals is a bit hacky, but works for now
        print(
            aggmorph.loc[aggmorph.case > 0.0, morphcols]
            .rename(index=system_name_fmt, columns=level_name_fmt)
            .to_latex(float_format=myformatter)
        )
