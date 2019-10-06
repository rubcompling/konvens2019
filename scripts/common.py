import time
import re
from functools import partial
from pathlib import Path

from rft2stts import rft2stts


class Timer:
    def __enter__(self):
        self.start = time.time()
        self.process_start = time.process_time()
        return self

    def __exit__(self, *args):
        self.stop = time.time()
        self.process_stop = time.process_time()
        self.elapsed = self.stop - self.start
        self.process_elapsed = self.process_stop - self.process_start


class TestSystem:
    def process(self, input_data):
        with Timer() as self.run_time:
            self.output_data = self.processor(input_data)
        return self

    def write_exp_results(self, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as outfile:
            for sent in self.data:
                print(sent, end="", file=outfile)


# standard Doc is a list of lists of these
# each sublist = sentence
class Token:
    fields = "id word lemma upos xpos feats head deprel deps misc".split()

    def __init__(self, **kwargs):
        for key in Token.fields:
            # covers unspecified fields
            val = kwargs.get(key, "_")
            # covers fields specified as None
            self.__dict__[key] = val if val else "_"
        # i'll just leave this here
        self.children = list()
        # make sure morph transformations are applied
        self.feats = str(Morph(from_string=self.feats))

    def __str__(self):
        return "\t".join(self.__dict__.get(key, "_") for key in Token.fields)

    @classmethod
    def from_str(cls, instring):
        return cls(**dict(zip(Token.fields, instring.rstrip().split("\t"))))

    def hide_fields(self, fields_to_hide):
        for field in fields_to_hide:
            if field == "head":
                self.head = self.id
            else:
                setattr(self, field, "_")


class Sentence:
    """Use this class instead of plain lists to make sure
       tokens get correct IDs. """

    def __init__(self, tokens):
        self.tokens = list()
        for i, tok in enumerate(tokens, start=1):
            tok.id = str(i)
            self.tokens.append(tok)

        # Establish dependency links
        for tok in self.tokens:
            try:
                if tok.head == "_":
                    # establish no links
                    pass
                    # maybe set head to something int-like
                    # tok.head = tok.id
                    # tok.deprel = "null"
                else:
                    tok_head = int(tok.head) - 1
                    if tok_head >= 0:
                        tok.parent = self.tokens[tok_head]
                        self.tokens[tok_head].children.append(tok)
            except ValueError:
                print("WARNING: weird value in 'head' field")
                print(tok)

    def __getitem__(self, key):
        return self.tokens[key]

    def __iter__(self):
        return iter(self.tokens)

    def __str__(self):
        return "\n".join(str(entry) for entry in self.tokens) + "\n\n"


class Document:
    def __init__(self, inputdata, hidden_fields=None):
        self.name = str()
        self.sentences = list()
        if isinstance(inputdata, Path):
            with inputdata.open(encoding="utf-8") as infile:
                self.sentences.extend(string2doc(infile.read(), hide_fields=hidden_fields))
            self.name = inputdata.stem
        elif isinstance(inputdata, str):
            self.sentences.extend(string2doc(inputdata, hide_fields=hidden_fields))
            self.name = ""
        else:
            self.sentences.extend(string2doc(inputdata.read(), hide_fields=hidden_fields))
            self.name = ""

        self.tokens = [tok for sent in self.sentences for tok in sent]

    def __getitem__(self, key):
        return self.sentences[key]

    def __iter__(self):
        return iter(self.sentences)

    def __len__(self):
        return len(self.tokens)

    def __str__(self):
        return "".join(str(sentence) for sentence in self.sentences)


def doc2string(conlldoc):
    return "".join(str(sentence) for sentence in conlldoc)


def string2doc(conllstring, hide_fields=None):
    sentences = list()
    sentstrings = conllstring.rstrip().split("\n\n")
    for sentstring in sentstrings:
        mytokens = list()
        for t in sentstring.split("\n"):
            t = Token.from_str(t)
            if hide_fields:
                t.hide_fields(hide_fields)
            mytokens.append(t)
        sentences.append(Sentence(mytokens))
    return sentences


def feature(featname, arg):
    """Use this dict to change the way morph values
    are represented.
    Map a value to `None` if you want a feature to
    be removed."""
    value_map = {"cmp": "comp", "indef": "ind", "sing": "sg", "plur": "pl"}
    return (featname, value_map.get(arg.lower(), arg.lower()))


degree = partial(feature, "degree")
case = partial(feature, "case")
number = partial(feature, "number")
gender = partial(feature, "gender")
definite = partial(feature, "definite")
person = partial(feature, "person")
tense = partial(feature, "tense")
mood = partial(feature, "mood")


def null(arg):
    """The `null` function always returns None.
       Use it to remove features."""
    return ("type", None)


class Morph:
    def __init__(self, from_string=None, orig_tag=None, **kwargs):
        self.empty = False
        self.feats = dict()
        self.original_tag = orig_tag

        if not (from_string or kwargs) or from_string == "_":
            self.empty = True
        else:
            if from_string:
                self.feats = dict(
                    feature(*keyval.lower().split("="))
                    for keyval in from_string.split("|")
                )
            else:
                self.feats = kwargs

        # remove None values
        self.feats = {key: val for key, val in self.feats.items() if val}

    def __str__(self):
        if self.empty:
            return "_"
        else:
            return "|".join(
                f"{key.lower()}={val.lower()}" for key, val in self.feats.items()
            )

    def to_set(self):
        return set(self.feats.items())

    @classmethod
    def from_goldtag(cls, goldtag):
        stts, *parts = goldtag.split(".")

        def fields_for_tag(tag):
            if tag.startswith("V") and tag.endswith("IMP"):
                return [number]
            elif tag.startswith("V") and tag.endswith("FIN"):
                return [person, number, tense, mood]
            elif tag == "ADJA":
                return [degree, gender, case, number]
            elif tag == "ADJD":
                return [degree]
            elif tag in {
                "NN",
                "NE",
                "ART",
                "PPOSS",
                "PPOSAT",
                "PDAT",
                "PDS",
                "PIS",
                "PIDAT",
                "PIAT",
                "PRELS",
                "PRELAT",
                "PWS",
                "PWAT",
            }:
                return [gender, case, number]
            elif tag == "PPER":
                return [person, number, gender, case]
            elif tag == "PRF":
                return [person, number, case]
            elif tag == "APPRART":
                return [gender, case]
            else:
                return []

        active_fields = fields_for_tag(stts)
        feats = dict(f(p) for f, p in zip(active_fields, parts))
        return cls(**feats, orig_tag=goldtag)

    @classmethod
    def from_tigertag(cls, tigertag):
        """Extract morphological information from a TIGER tag."""
        stts, *parts = tigertag.split(".")

        # Maps an POS tag to the list of functions we need in
        # order to interpret the morphological information.
        def fields_for_tag(tag):
            if tag == "ADJA":
                return [degree, case, number, gender]
            elif tag == "ADJD":
                return [degree]
            elif tag in {"VVFIN", "VAFIN", "VMFIN"}:
                return [person, number, tense, mood]
            elif tag in {"VVIMP", "VAIMP"}:
                return [person, number, mood]
            elif tag in {
                "APPRART",
                "ART",
                "NN",
                "NE",
                "PPOSAT",
                "PPOSS",
                "PDAT",
                "PDS",
                "PIAT",
                "PIS",
                "PRELS",
                "PRELAT",
                "PWAT",
                "PWS",
            }:
                return [case, number, gender]
            elif tag == "PPER":
                return [person, case, number, gender]
            elif tag == "PRF":
                return [person, case, number]
            else:
                return []

        active_fields = fields_for_tag(stts)
        feats = dict(f(p) for f, p in zip(active_fields, parts))
        return cls(**feats, orig_tag=tigertag)

    @classmethod
    def from_rftag(cls, rftag):
        for rftag_begin, stts_tag in rft2stts:
            tigertag, n = re.subn(f"^{rftag_begin}", stts_tag, rftag)
            if n > 0:
                break
        else:
            tigertag = rftag

        stts, *parts = tigertag.split(".")

        # Maps an POS tag to the list of functions we need in
        # order to interpret the morphological information.
        def fields_for_tag(tag):
            if tag == "ADJA":
                return [degree, case, number, gender]
            elif tag == "ADJD":
                return [degree]
            elif tag in {"VVFIN", "VAFIN", "VMFIN"}:
                return [person, number, tense, mood]
            elif tag in {"VVIMP", "VAIMP"}:
                return [person, number, mood]
            elif tag in {"APPRART", "ART", "NN", "NE"}:
                return [case, number, gender]
            elif tag in {
                "PPOSAT",
                "PPOSS",
                "PDAT",
                "PDS",
                "PIAT",
                "PIS",
                "PRELS",
                "PRELAT",
                "PWAT",
                "PWS",
                "PRF",
            }:
                return [person, case, number]
            elif tag == "PPER":
                return [person, case, number, gender]
            else:
                return []

        active_fields = fields_for_tag(stts)
        feats = dict(f(p) for f, p in zip(active_fields, parts))
        return cls(**feats, orig_tag=rftag)

    @classmethod
    def from_stanfordnlp(cls, snlp_tag):
        # just send everything through the tag map
        return cls(**dict(feature(*entry.split("=")) for entry in snlp_tag.split("|")))

    @classmethod
    def from_parzu(cls, parzutag):
        # "_" -> "*" for underspecified vals
        # (remember to prepend stts tag)
        stts, *parts = parzutag.replace("_", "*").split("|")

        def fields_for_tag(tag):
            if tag == "PPER":
                return [person, number, gender, case]
            elif tag == "ADJA":
                return [degree, gender, case, number, null, null]
            elif tag == "ADJD":
                return [degree, null]
            elif tag == "ART":
                return [definite, gender, case, number]
            elif tag in {"APPRART", "APPR"}:
                return [case]
            elif tag in {"VVFIN", "VAFIN", "VMFIN"}:
                return [person, number, tense, mood]
            elif tag in {"VVIMP", "VAIMP"}:
                return [number]
            elif tag in {
                "NN",
                "NE",
                "PIS",
                "PIAT",
                "PPOSAT",
                "PDS",
                "PWS",
                "PRELS",
                "PRELAT",
                "PDAT",
                "PWAT",
                "PPOSS",
            }:
                return [gender, case, number]
            elif tag == "PRF":
                return [person, number, case]
            else:
                return []

        active_fields = fields_for_tag(stts)
        feats = dict(f(p) for f, p in zip(active_fields, parts))
        return cls(**feats, orig_tag=parzutag)


def rftag2stts(rftag):
    for key, val in rft2stts:
        if rftag.startswith(key):
            return val
    else:
        return rftag


def main(task, system_list):
    import argparse
    from pathlib import Path

    argparser = argparse.ArgumentParser()
    argparser.add_argument("indir", type=Path)
    argparser.add_argument("--outdir", default="../data/system", type=Path)
    argparser.add_argument("--testing", action="store_true",
                           help="don't record timing stats")
    argparser.add_argument(
        "-s", "--systems", nargs="+", help="names of systems to run (lowercase)"
    )
    args = argparser.parse_args()

    exp_exec_time = int(time.time())
    for System in system_list:
        sys_name = System.__name__.lower()

        if args.systems and sys_name not in args.systems:
            continue

        s = System()
        for inputfile in args.indir.iterdir():
            print(f"Running {s.__class__.__name__} on {str(inputfile)}...")

            domain, *_ = inputfile.stem.split("_")
            ext = ".conll" if task != "tokens" else ".txt"

            # gold annotations to hide from the test systems
            # fields_to_hide = {"pos": ["lemma", "upos", "xpos", "feats", "head", "deprel", "deps"],
            #                   "lemmas": [],
            #                   "depparse": []}

            with inputfile.open("r", encoding="utf-8") as input_data:
                s.process(input_data.read())
            s.postprocess()

            outpath = args.outdir / sys_name / task / f"{domain}_{task}{ext}"
            s.write_exp_results(outpath)

            if not args.testing:
                timepath = Path("../eval/timing.csv")
                with timepath.open("a", encoding="utf-8") as outfile:
                    print(
                        sys_name,
                        domain,
                        task,
                        s.model_load_time.elapsed,
                        s.run_time.elapsed,
                        s.run_time.process_elapsed,
                        exp_exec_time,
                        sep="\t",
                        file=outfile,
                    )

    print("done!")
