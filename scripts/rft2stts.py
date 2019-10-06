
# extracted from RFtagger Java interface
# rftj/src/de/sfb833/a4/RFTagger/tagsetconv/mappings/stts.xml
# 
raw_map = [
    ("ADJA", "ADJA"),
    ("ADJD", "ADJD"),
    ("ADV", "ADV"),
    ("APPO", "APPO"),
    ("APPRART", "APPRART"),
    ("APPR", "APPR"),
    ("APZR", "APZR"),
    ("ART", "ART"),

    ####
    # might also need these
    ("ART.Def", "ART"),
    ("ART.Indef", "ART"),
    ######

    ("CARD", "CARD"),
    ("CONJ.Comp", "KOKOM"),
    ("CONJ.Comp", "KOUS"),
    ("CONJ.Coord", "KON"),
    ("CONJ.SubFin", "KOUS"),
    ("CONJ.SubInf", "KOUI"),
    ("FM", "FM"),
    ("ITJ", "ITJ"),
    ("N.Name", "NE"),
    ("N.Reg", "NN"),
    ("PART.Ans", "PTKANT"),
    ("PART.Deg", "PTKA"),
    ("PART.Neg", "PTKNEG"),
    ("PART.Verb", "PTKVZ"),
    ("PART.Zu", "PTKZU"),
    ("PROADV.Dem", "PROP"),
    ("PROADV.Inter", "PWAV"),
    ("PRO.Dem.Attr", "PDAT"),
    ("PRO.Dem.Subst", "PDS"),
    ("PRO.Indef.Attr", "PIAT"),
    ("PRO.Indef.Subst", "PIS"),
    ("PRO.Inter.Attr", "PWAT"),
    ("PRO.Inter.Subst", "PWS"),
    ("PRO.Pers.Subst", "PPER"),
    ("PRO.Poss.Attr", "PPOSAT"),
    ("PRO.Poss.Subst", "PPOS"),    
    ("PRO.Refl.Subst", "PRF"),
    ("PRO.Rel.Attr", "PRELAT"),
    ("PRO.Rel.Subst", "PRELS"),
    ("SYM.Other.Auth", "NE"),
    ("SYM.Other.XY", "$("),
    ("SYM.Other.Aster", "$("),    
    ("SYM.Paren.Left", "$("),
    ("SYM.Paren.Right", "$("),
    ("SYM.Pun.Colon", "$."),
    ("SYM.Pun.Comma", "$,"),
    ("SYM.Pun.Cont", "$("),
    ("SYM.Pun.Hyph", "$("),
    ("SYM.Pun.Sent", "$."),
    ("SYM.Pun.Slash", "$("),
    ("SYM.Quot.Left", "$("),
    ("SYM.Quot.Right", "$("),
    ("TRUNC", "TRUNC"),
    ("VFIN.Aux", "VAFIN"),
    ("VFIN.Full", "VVFIN"),
    ("VFIN.Haben", "VAFIN"),
    ("VFIN.Mod", "VMFIN"),
    ("VFIN.Sein", "VAFIN"),
    ("VIMP.Full", "VVIMP"),
    ("VIMP.Haben", "VAIMP"),
    ("VIMP.Sein", "VAIMP"),
    ("VINF.Full", "VVINF"),
    ("VINF.Aux", "VAINF"),
    ("VINF.Full.zu", "VVIZU"),
    ("VINF.Haben", "VAINF"),
    ("VINF.Mod", "VMINF"),
    ("VINF.Sein", "VAINF"),
    ("VPP.Aux.Psp", "VAPP"),
    ("VPP.Full.Psp", "VVFIN"),
    ("VPP.Full.Psp", "VVPP"),
    ("VPP.Sein.Psp", "VAPP"),
    ("VPP.Haben.Psp", "VAPP"),
    ("VPP.Mod.Psp", "VMPP")
]

rft2stts = sorted(raw_map, key=lambda tup: len(tup[0]), reverse=True)