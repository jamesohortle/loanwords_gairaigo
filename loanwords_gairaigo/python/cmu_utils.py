#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Constants to work with CMU dictionary data."""

# From the website.
"""
Phoneme	Example	Translation
-------	-------	-----------
AA	odd	AA D
AE	at	AE T
AH	hut	HH AH T
AO	ought	AO T
AW	cow	K AW
AY	hide	HH AY D
B	be	B IY
CH	cheese	CH IY Z
D	dee	D IY
DH	thee	DH IY
EH	Ed	EH D
ER	hurt	HH ER T
EY	ate	EY T
F	fee	F IY
G	green	G R IY N
HH	he	HH IY
IH	it	IH T
IY	eat	IY T
JH	gee	JH IY
K	key	K IY
L	lee	L IY
M	me	M IY
N	knee	N IY
NG	ping	P IH NG
OW	oat	OW T
OY	toy	T OY
P	pee	P IY
R	read	R IY D
S	sea	S IY
SH	she	SH IY
T	tea	T IY
TH	theta	TH EY T AH
UH	hood	HH UH D
UW	two	T UW
V	vee	V IY
W	we	W IY
Y	yield	Y IY L D
Z	zee	Z IY
ZH	seizure	S IY ZH ER
"""

# Do vowels first.
vowels = {
    None: "v",  # Represent a consonant cluster with an intermediate vowel. Should it always be "u"?
    "AA": "a",
    "AE": "a x",
    "AH": "a",
    "AO": "o",
    "AW": "a u",
    "AY": "a i",
    "EH": "e",
    "ER": "a r",  # Roticised schwa so add an r?
    "EY": "e i",
    "IH": "i",
    "IY": "i -",
    "OW": "o -",
    "OY": "o i",
    "UH": "u",
    "UW": "u -",
}

# Now look at semivowels.
semivowels = {"W": "w", "Y": "y"}

# Now look at consonants.
consonants = {
    "B": "b",
    "CH": "ty",
    "D": "d",
    "DH": "z",
    "F": "f",
    "G": "g",
    "HH": "h",
    "JH": "jy",
    "K": "k",
    "L": "r",
    "M": "m",
    "N": "n",
    "NG": "N",
    "P": "p",
    "R": "r",
    "S": "s",
    "SH": "sy",
    "T": "t",
    "TH": "s",
    "V": "b",
    "Z": "z",
    "ZH": "jy",
}

# Exceptions and the like.
special = {"NP": "np", "NB": "nb", "TS": "ts"}

# Non-geminating symbols (can't take x before).
non_geminating = {
    **vowels,
    **semivowels,
    **{
        "B": "b",
        "D": "d",
        "DH": "z",
        "F": "f",
        "G": "g",
        "HH": "h",
        "JH": "jy",
        "L": "r",
        "M": "m",
        "N": "n",
        "NG": "N",
        "R": "r",
        "V": "b",
        "Z": "z",
        "ZH": "jy",
        "NP": "np",
        "NB": "nb",
    },
}

# Full dictionary of all symbols.
symb_to_prekana = {**vowels, **semivowels, **consonants, **special}

# Prekana to kana map.
# See prekana_map.py

# Some test data.
test_data = [
    ("BEHEMOTHS", "B IH0 HH IY1 M AH0 TH S", "ビヒーモスス"),
    ("ENCOURAGES", "EH0 N K ER1 IH0 JH IH0 Z", "エンカレッジズ"),
    ("MABILE", "M AA1 B AH0 L", "マービル"),
    ("TIEDT", "T IY1 D T", "ティート"),
    ("GARNERS", "G AA1 R N ER0 Z", "ガーナーズ"),
    ("CONSORTIA", "K AH0 N S AO1 R SH AH0", "コンソーシャ"),
    ("POWDERS", "P AW1 D ER0 Z", "パウダーズ"),
    ("TERESA(1)", "T ER0 EY1 S AH0", "テレイサ"),
    ("OLYMPICS'", "OW0 L IH1 M P IH0 K S", "オリンピックス"),
    ("NIEHAUS", "N IY1 HH AW2 S", "ニーハウス"),
    ("DOMINEERING", "D AA2 M AH0 N IH1 R IH0 NG", "ドミニーリング"),
    ("PROGRESSIVITY", "P R AA2 G R EH0 S IH1 V AH0 T IY0", "プログレッシビティー"),
    ("BOLIVAR", "B AA1 L AH0 V ER0", "ボリバー"),
    ("DAFFIN", "D AE1 F IH0 N", "ダッフィン"),
    ("EYMAN", "EY1 M AH0 N", "エイマン"),
    ("DURNEY", "D ER1 N IY0", "ダーニー"),
    ("FORIN", "F AO1 R IH0 N", "フォリン"),
    ("BLAMED", "B L EY1 M D", "ブレイムド"),
    ("BACKWATER", "B AE1 K W AO2 T ER0", "バックウォーター"),
    ("DISPARAGES", "D IH0 S P EH1 R IH0 JH IH0 Z", "ディスパラジズ"),
]
