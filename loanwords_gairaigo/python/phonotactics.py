#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phonotactics à la Wikipedia."""

"""
 " English phonotactics typically follow (C)3V(C)5 structure for a syllable,
 " i.e., up to 3 consonants/semivowels then a vowel then up to 5 consonants/semivowels.
 " Wikipedia lists the following as [onsets](https://en.wikipedia.org/wiki/English_phonology#Onset):
 " ;
 " and the folling as [codas](https://en.wikipedia.org/wiki/English_phonology#Coda):
 " .
 " Therefore, there are as many as xyz consonant clusters.
"""

# Fix the copy-pastes from Wikipedia.
def fix(s):
    s = s.translate(
        {
            0x0261: "G",
            0x03B8: "TH",
            0x0283: "SH",
            0x0292: "ZH",
            0x014B: "NG",
            0x00F0: "DH",
        }
    )
    return '"' + '", "'.join(s.replace("/", "").upper().split(", ")) + '"'


onsets = {
    "M",
    "P",
    "B",
    "F",
    "V",
    "TH",
    "DH",
    "N",
    "T",
    "D",
    "S",
    "Z",
    "L",
    "CH",
    "JH",
    "SH",
    "ZH",
    "R",
    "Y",
    "K",
    "G",
    "W",
    "HH",  # any consonant except NG
    "P L",
    "B L",
    "K L",
    "G L",
    "P R",
    "B R",
    "T R",
    "D R",
    "K R",
    "G R",
    "T W",
    "D W",
    "G W",
    "K W",
    "P W",  # stop plus approximant other than Y
    "F L",
    "S L",
    "TH L",
    "F R",
    "TH R",
    "SH R",
    "H W",
    "S W",
    "TH W",
    "V W",  # voiceless fricative or V plus approximant other than Y
    "P Y",
    "B Y",
    "T Y",
    "D Y",
    "K Y",
    "G Y",
    "M Y",
    "N Y",
    "F Y",
    "V Y",
    "TH Y",
    "S Y",
    "Z Y",
    "H Y",
    "L Y",  # consonant plus Y
    "S P",
    "S T",
    "S K",  # S plus voiceless stop
    "S M",
    "S N",  # S plus nasal other than NG
    "S F",
    "S TH",  # S plus voiceless fricative
    "S P L",
    "S K L",
    "S P R",
    "S T R",
    "S K R",
    "S K W",
    "S M Y",
    "S P Y",
    "S T Y",
    "S K Y",  # S plus voiceless stop plus approximant
    "S F R",  # S plus voiceless fricative plus approximant
}

# Uninflected codas (see below).
uninf_codas = {
    "M",
    "P",
    "B",
    "F",
    "V",
    "TH",
    "DH",
    "N",
    "T",
    "D",
    "S",
    "Z",
    "L",
    "CH",
    "JH",
    "SH",
    "ZH",
    "R",
    "NG",
    "K",
    "G",  # the single consonant phonemes except HH, W and Y
    "L P",
    "L B",
    "L T",
    "L D",
    "L CH",
    "L JH",
    "L K",  # lateral approximant plus stop or affricate
    "R P",
    "R B",
    "R T",
    "R D",
    "R CH",
    "R JH",
    "R K",
    "R G",  # R plus stop or affricate:
    "L F",
    "L V",
    "L TH",
    "L S",
    "L Z",
    "L SH",  # lateral approximant plus fricative
    "R F",
    "R V",
    "R TH",
    "R S",
    "R Z",
    "R SH",  # R plus fricative
    "L M",
    "L N",  # lateral approximant plus nasal
    "R M",
    "R N",
    "R L",  # R plus nasal or lateral
    "M P",
    "N T",
    "N D",
    "N CH",
    "N JH",
    "NG K",  # nasal plus homorganic stop or affricate
    "M F",
    "M TH",
    "N TH",
    "N S",
    "N Z",
    "NG TH",  # nasal plus fricative
    "F T",
    "S P",
    "S T",
    "S K",  # voiceless fricative plus voiceless stop
    "F TH",  # two voiceless fricatives
    "P K",
    "K T",  # two voiceless stops
    "P TH",
    "P S",
    "T TH",
    "T S",
    "D TH",
    "K S",  # stop plus voiceless fricative
    "L P T",
    "L P S",
    "L F TH",
    "L T S",
    "L S T",
    "L K T",
    "L K S",  # lateral approximant plus two consonants
    "R M TH",
    "R P T",
    "R P S",
    "R T S",
    "R S T",
    "R K T",  # R plus two consonants
    "M P T",
    "M P S",
    "N D TH",
    "NG K T",
    "NG K S",
    "NG K TH",  # nasal plus homorganic stop plus stop or fricative
    "K S TH",
    "K S T",  # three obstruents
}

# All codas can theoretically take a +S or +Z to represent plural or genitive
# (except those ending in S, Z, SH, ZH, CH or JH),
# or a +T or +D to represent past tense
# (except those ending in T or D.)
codas = uninf_codas  # + ?? Too hard for now...
