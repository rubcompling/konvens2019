#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np

from common import Token, Document, Morph

logging.basicConfig(filename="rule-application.log", filemode="w", level=logging.DEBUG)

# Paths that shouldn't change
SYSTEMS_DIR = Path("../data/system")
GOLD_DIR = Path("../data/gold/balanced")

# allerdings müssten wir noch schauen wie dem/das
# lemmatisiert wird...
APPRARTMAP = {
    "am": ("an", "dem"),
    "ans": ("an", "das"),
    "aufs": ("auf", "das"),
    "beim": ("bei", "dem"),
    "fürs": ("für", "das"),
    "im": ("in", "dem"),
    "ins": ("in", "das"),
    "ums": ("um", "das"),
    "vom": ("von", "dem"),
    "zum": ("zu", "dem"),
    "zur": ("zu", "der"),
    "übers": ("über", "das"),
    "durchs": ("durch", "das"),
}

LEMMA_MAP = {key: val for key, (val, _) in APPRARTMAP.items()}

MORPH_FEATS = [
    "degree",
    "case",
    "number",
    "gender",
    "definite",
    "person",
    "tense",
    "mood",
]

deprel_map = {
    "subj": "nsubj nsubjpass sb sbp nsubj:pass",
    "obj": "dobj obja oa oa2",
    "iobj": "objd objg da og",
    # "pobj": "objp op",
    "vsubj": "csubj csubjpass subjc sb csubj:pass",
    "vobj": "vobj ccomp objc obji oc rs xcomp",
    "pred": "pd",
    "expl": "ep expl:pv",
    # "cop": "cop",
    # "_": "ROOT root",
}
DEPREL_EQ = dict()
for k, v in deprel_map.items():
    DEPREL_EQ[k] = set(v.split())
    DEPREL_EQ[k].add(k)

ALL_DEPRELS = set(DEPREL_EQ.keys())
for val in DEPREL_EQ.values():
    ALL_DEPRELS.update(val)


def check_head_copula(gt: Token, at: Token) -> bool:
    try:
        # Rule 2a. from "er" = at
        # check if parent (= 'nett') of apparently wrong token `at` (= 'er') has
        # some other dependent (= 'ist') which points to it as a copula
        # GOLD: er <--subj-- ist --pred--> nett
        # 1 *er*   subj 2
        # 2 ist
        # 3 nett   pred 2
        # SYSTEM: er <--subj-- nett --cop--> ist)
        # 1 *er*   subj 3
        # 2 ist    cop  3
        # 3 nett
        if at.deprel in DEPREL_EQ.get(gt.deprel) and any(
            x.deprel == "cop" and x.id == gt.parent.id for x in at.parent.children
        ):
            logging.debug(f"rule 2a: {gt.id} {gt.word}")
            return True

        # Rule 1a. from "er"
        # GOLD: er <--subj-- helfen --aux--> will
        # 1 *er*    subj 3
        # 2 will    aux  3
        # 3 helfen
        #  SYSTEM: er <--subj-- will --x--> helfen)
        # 1 *er*    subj 2
        # 2 will
        # 3 helfen  --   2
        elif at.deprel in DEPREL_EQ.get(gt.deprel) and any(
            x.deprel == "aux" and x.id == at.parent.id for x in gt.parent.children
        ):
            logging.debug(f"rule 1a: {gt.id} {gt.word}")
            return True

    except AttributeError:
        return False


def check_child_copula(gt: Token, at: Token) -> bool:
    try:
        # Rule 2b. from 'nett'
        # check if apparently wrong token 'at' has child that
        # points to it as a copula
        # GOLD: er <--subj-- ist --pred--> nett
        # 1 er     subj 2
        # 2 ist
        # 3 *nett* pred 2
        # SYSTEM: er <--subj-- nett --cop--> ist)
        # 1 er     subj 3
        # 2 ist    cop  3
        # 3 *nett*
        if gt.deprel == "pred" and any(
            x.deprel == "cop" and x.id == gt.parent.id for x in at.children
        ):
            logging.debug(f"rule 2b: {gt.id} {gt.word}")
            return True

        # Rule 3a. from 'Park'
        # check if parent of at is a child of gt with rel 'pcase'
        # (GOLD: ist --pred--> Park --pcase--> im
        #  SYSTEM: ist --pred/pd--> im --X--> Park)
        elif gt.deprel == "pred" and at.parent.deprel in DEPREL_EQ.get("pred"):
            if any(
                x.deprel.startswith("pcase") and x.id == at.parent.id
                for x in gt.children
            ):
                logging.debug(f"rule 3a: {gt.id} {gt.word}")
                return True
            else:
                return False
        else:
            return False
    except AttributeError:
        return False


def check_verbal_deps(gt: Token, at: Token) -> bool:
    try:
        # Rule 2c. from 'ist'
        # GOLD: er <--subj-- ist --pred--> nett
        # 1 er     subj 2
        # 2 *ist*  vobj
        # 3 nett  pred 2
        # SYSTEM: er <--subj-- nett --cop--> ist)
        # 1 er     subj 3
        # 2 *ist*  cop  3
        # 3 nett   vobj
        if (
            at.deprel == "cop"
            and at.parent.deprel in DEPREL_EQ.get(gt.deprel)
            and any(x.deprel == "pred" and x.id == at.parent.id for x in gt.children)
        ):
            logging.debug(f"rule 2c: {gt.id} {gt.word}")
            return True

        # Rule 1b. from 'helfen'
        # GOLD: er <--subj-- helfen --aux--> will
        # 1 er       subj 3
        # 2 will     aux  3
        # 3 *helfen* vobj
        #  SYSTEM: er <--subj-- will --x--> helfen)
        # 1 er       subj 2
        # 2 will     X
        # 3 *helfen* aux  2
        elif at.parent.deprel in DEPREL_EQ.get(gt.deprel) and any(
            x.deprel == "aux" and at.parent.id == x.id for x in gt.children
        ):
            logging.debug(f"rule 1b: {gt.id} {gt.word}")
            return True
        else:
            return False

    except AttributeError:
        return False


def check_swapped_rels(gt: Token, at: Token) -> bool:
    try:
        # Rule 4. pred und subj dürfen genau vertauscht werden
        if (
            gt.deprel == "pred"
            and at.deprel in DEPREL_EQ.get("subj")
            and any(
                x.deprel == "subj"
                and y.deprel in DEPREL_EQ.get("pred")
                and x.id == y.id
                for x in gt.parent.children
                for y in at.parent.children
            )
        ):
            logging.debug(f"rule 4a: {gt.id} {gt.word}")
            return True
        elif (
            gt.deprel == "subj"
            and (at.deprel in DEPREL_EQ.get("pred"))
            and any(
                x.deprel == "pred"
                and y.deprel in DEPREL_EQ.get("subj")
                and x.id == y.id
                for x in gt.parent.children
                for y in at.parent.children
            )
        ):
            logging.debug(f"rule 4b: {gt.id} {gt.word}")
            return True

        # # Rule 5. expl darf genau mit (subj|obj) vertauscht werden
        elif (
            gt.deprel == "expl"
            and (
                at.deprel in DEPREL_EQ.get("subj") or at.deprel in DEPREL_EQ.get("obj")
            )
            and any(
                x.deprel in "subj obj"
                and y.deprel in DEPREL_EQ.get("expl")
                and x.id == y.id
                for x in gt.parent.children
                for y in at.parent.children
            )
        ):
            logging.debug(f"rule 5a: {gt.id} {gt.word}")
            return True
        elif (
            (gt.deprel == "subj" or gt.deprel == "obj")
            and at.deprel in DEPREL_EQ.get("expl")
            and any(
                x.deprel == "expl"
                and (
                    y.deprel in DEPREL_EQ.get("subj")
                    or y.deprel in DEPREL_EQ.get("obj")
                )
                and x.id == y.id
                for x in gt.parent.children
                for y in at.parent.children
            )
        ):
            logging.debug(f"rule 5b: {gt.id} {gt.word}")
            return True

        # Rule 6. pred und expl dürfen genau vertauscht werden
        elif (
            gt.deprel == "pred"
            and at.deprel in DEPREL_EQ.get("expl")
            and any(
                x.deprel == "expl"
                and y.deprel in DEPREL_EQ.get("pred")
                and x.id == y.id
                for x in gt.parent.children
                for y in at.parent.children
            )
        ):
            logging.debug(f"rule 6a: {gt.id} {gt.word}")
            return True
        elif (
            gt.deprel == "expl"
            and (at.deprel in DEPREL_EQ.get("pred"))
            and any(
                x.deprel == "pred"
                and y.deprel in DEPREL_EQ.get("expl")
                and x.id == y.id
                for x in gt.parent.children
                for y in at.parent.children
            )
        ):
            logging.debug(f"rule 6b: {gt.id} {gt.word}")
            return True
        else:
            return False

    except AttributeError:
        # no parent
        return False


def compare_depparse(g, a):
    if g.deprel in DEPREL_EQ:
        if a.deprel in DEPREL_EQ.get(g.deprel) and int(g.head) == int(a.head):
            return 1
        elif check_head_copula(g, a):
            return 1
        elif check_child_copula(g, a):
            return 1
        elif check_verbal_deps(g, a):
            return 1
        elif check_swapped_rels(g, a):
            return 1
        else:
            return 0
    elif any(a.deprel in DEPREL_EQ.get(x) for x in DEPREL_EQ):
        # add exceptions to prevent conflicts with special rules above
        if (
            (a.deprel == "cop" and g.lemma in "sein werden")
            or g.deprel == "aux"
            or (g.deprel.startswith("pcase") and g.parent.deprel == "pred")
        ):
            logging.debug(f"rule FP: {g.id} {g.word}")
            return np.nan
        # "false positives"
        else:
            return 0
    else:
        # ignore if not one of the annotated relations
        return np.nan


def compare_lemmas(g, a):
    def match(gold_val, anno_val):
        mod_gold_val = gold_val.lower()
        mod_anno_val = anno_val.lower()

        # for TreeTagger
        mod_anno_val = re.sub(r"^(\w+)\+.*$", r"\1", mod_anno_val)

        # also replace ß mit ss
        mod_gold_val = mod_gold_val.replace("ß", "ss")
        mod_anno_val = mod_anno_val.replace("ß", "ss")
        return mod_gold_val == mod_anno_val

    if match(g.lemma, a.lemma):
        return 1

    elif g.xpos == "APPRART":
        if match(g.lemma, LEMMA_MAP.get(a.lemma, a.lemma)):
            return 1
        else:
            return 0

    elif a.xpos == "PRF" and a.lemma == "sich":
        return 1

    elif g.xpos.startswith("$") and (a.lemma == g.word or a.lemma == "_"):
        return 1

    elif g.xpos == "PPER" and match(g.word, a.word):
        return 1

    elif a.lemma in {"<card>", "@card@", "@ord@"} and match(g.lemma, a.word):
        return 1

    elif a.lemma == "_" and match(g.lemma, a.word):
        return 1

    elif (
        sys_name in {"treetagger", "rftagger", "parzu"}
        and g.xpos in ["PDS", "PRELS", "ART"]
        and (
            (g.lemma == "ein" and a.lemma == "eine")
            or (g.lemma == "der" and a.lemma == "die")
        )
    ):
        return 1

    elif sys_name in {"rftagger", "stanfordnlp", "treetagger"}:
        if match(g.lemma, a.lemma.split("|")[0]):
            return 1
        else:
            return 0

    else:
        return 0


def compare_morph(g, a):
    gfeats = Morph(from_string=g.feats).feats
    afeats = Morph(from_string=a.feats).feats

    new_row = dict()
    this_instance_vals = list()
    for feat in MORPH_FEATS:
        if feat in gfeats:
            # correct if feature exists and value matches
            if gfeats.get(feat) == afeats.get(feat):
                new_row[feat] = 1
            else:
                new_row[feat] = 0
        else:
            # not in gold,
            # ignorieren wir das
            new_row[feat] = np.nan
        this_instance_vals.append(new_row[feat])
    return pd.Series(this_instance_vals).mean(), new_row


def compare_pos(g, a):
    if any(
        [
            g.xpos == a.xpos,
            g.xpos == "PAV" and a.xpos == "PROAV",
            g.xpos == "PAV" and a.xpos == "PROP",
            g.xpos == "$(" and a.xpos == "$[",
        ]
    ):
        return 1

    elif sys_name == "stanfordnlp":
        if (
            g.xpos == "APPRART"
            and a.xpos in {"APPR", "ART"}
            and g.word.lower() in APPRARTMAP
        ):
            return 1
        else:
            return 0

    else:
        return 0


if __name__ == "__main__":

    all_systems = [p.name for p in SYSTEMS_DIR.iterdir()]

    all_data_rows = list()
    for sys_name in all_systems:
        for anno_level in ["pos", "lemmas", "morph", "depparse"]:
            if anno_level == "depparse":
                anno_files_path = SYSTEMS_DIR / sys_name / "depparse"
            elif anno_level == "depparseud":
                anno_files_path = SYSTEMS_DIR / sys_name / "depparseud"
            else:
                anno_files_path = SYSTEMS_DIR / sys_name / "pos"

            # if anno_level == "depparseud":
            #     gold_files = sorted(GOLD_DIR.joinpath("ud-tokenized").iterdir())
            # else:
            gold_files = sorted(GOLD_DIR.joinpath("annotations-upos").iterdir())

            if anno_files_path.exists():
                anno_files = sorted(anno_files_path.iterdir())
            else:
                # skip systems that don't have the annotation level
                # we're interested in
                continue

            assert len(gold_files) == len(anno_files)
            for goldfile, sysfile in zip(gold_files, anno_files):
                gold_doc = Document(goldfile)
                sys_doc = Document(sysfile)

                assert len(gold_doc) == len(sys_doc)
                logging.debug(f"# file = {goldfile.name}, system = {sys_name}")
                for gtok, atok in zip(gold_doc.tokens, sys_doc.tokens):
                    new_row = {
                        "pos": gtok.xpos,
                        "token": gtok.word,
                        "annotation": anno_level,
                        "genre": goldfile.stem,
                        "system": sys_name,
                    }
                    if anno_level == "pos":
                        new_row["gold_val"] = gtok.xpos
                        new_row["sys_val"] = atok.xpos
                        new_row["correct"] = compare_pos(gtok, atok)

                    elif anno_level == "morph":
                        new_row["gold_val"] = gtok.feats
                        new_row["sys_val"] = atok.feats
                        new_row["correct"], featcols = compare_morph(gtok, atok)
                        new_row.update(featcols)

                    elif anno_level == "lemmas":
                        new_row["gold_val"] = gtok.lemma
                        new_row["sys_val"] = atok.lemma
                        new_row["correct"] = compare_lemmas(gtok, atok)

                    elif anno_level == "depparse" or anno_level == "depparseud":
                        new_row["gold_val"] = f"{gtok.head}-{gtok.deprel}"
                        new_row["sys_val"] = f"{atok.head}-{atok.deprel}"
                        new_row["correct"] = compare_depparse(gtok, atok)

                        # if anno_level == "depparseud":
                        #     breakpoint()
                    else:
                        print("unknown anno level")
                        exit(1)

                    assert isinstance(new_row, dict)
                    assert new_row.get("correct") is not None
                    all_data_rows.append(new_row)

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
    ).astype({"correct": float})

    # breakpoint()
    existing_results = pd.read_csv(sys.stdin, index_col=0)
    new_results = pd.concat([existing_results, results])
    new_results.to_csv(sys.stdout)
