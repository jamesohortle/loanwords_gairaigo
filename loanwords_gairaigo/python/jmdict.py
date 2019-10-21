#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan JMdict for things that look like 外来語."""

import re
import sys
import sqlite3
from pathlib import Path

from lxml import etree as ET

DB_PATH = Path("../db/jmdict.db")
JMDICT = str(Path("../data/JMdict_e").resolve())

SEQUENCE_TAG = "ent_seq"
ENTRY_TAG = "entry"
KANJI_ELEMENT = "k_ele"
SURFACE_FORM = "keb"
READING_ELEMENT = "r_ele"
SPOKEN_FORM = "reb"
SENSE_TAG = "sense"
GLOSS_TAG = "gloss"
MISC_TAG = "misc"
LSOURCE_TAG = "lsource"


def makeTable():
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS
               gairaigo (
                  entry_sequence INTEGER UNIQUE,
                  japanese TEXT,
                  reading TEXT,
                  gloss TEXT,
                  strict_eng TEXT,
                  wasei TEXT
               )
            ;
         """
        )


def getSequence(entry):
    return int(entry.find(SEQUENCE_TAG).text)


def getSurface(entry):
    kanji_element = entry.find(KANJI_ELEMENT)
    if kanji_element is not None:
        return "".join(kanji_element.find(SURFACE_FORM).itertext())
    else:
        return None


def getReading(entry):
    reading_element = entry.find(READING_ELEMENT)
    if reading_element is not None:
        return "".join(reading_element.find(SPOKEN_FORM).itertext())
    else:
        return None


parenthetical = re.compile(r"\([^)]*\) ?")


def removeParentheticals(s):
    return parenthetical.sub("", s).strip()


def getGloss(entry):
    # Find gloss tag.
    sense = entry.find(SENSE_TAG)
    gloss = sense.find(
        GLOSS_TAG
    )  # What about multiple glosses? Shouldn't happen for 外来語.
    return removeParentheticals("".join(gloss.itertext()))


def getStrictEng(entry):
    # For strict glosses, take the gloss given in <lsource xml:lang="eng"> tags.
    sense = entry.find(SENSE_TAG)
    for lsource in sense.iterfind(LSOURCE_TAG):
        lang_attrib = lsource.xpath("./@xml:lang")  # Returns a(n empty) list
        if lang_attrib == ["eng"]:
            return removeParentheticals("".join(lsource.itertext()))


def getWasei(entry):
    # For wasei glosses, take the gloss given in <lsource ls_wasei="y"> tags.
    sense = entry.find(SENSE_TAG)
    for lsource in sense.iterfind(LSOURCE_TAG):
        lang_attrib = lsource.xpath("./@ls_wasei")  # Returns a(n empty) list
        if lang_attrib == ["y"]:
            return removeParentheticals("".join(lsource.itertext()))


not_kat_regex = re.compile(r"[^\u30a0-\u30ff\u31f0-\u31ff]")


def onlyKat(s):
    return True if not_kat_regex.search(s) == None else False


def quickExclude(entry):
    for sense in entry.iterfind(SENSE_TAG):
        # If it's 擬音語 or 擬態語, skip.
        miscs = sense.iterfind(MISC_TAG)
        for misc in miscs:
            if "".join(misc.itertext()) == "&on-mim;":
                return True

        # Exclude non-English sources.
        lsources = sense.iterfind(LSOURCE_TAG)
        for source in lsources:
            if source.xpath("./@xml:lang") != ["eng"]:
                return True

    # No English glosses ==> None.
    return False


def scan_dict():
    """Iteratively find pages in the dump and extract the first paragraph if the title matches."""
    entries = ET.iterparse(JMDICT, tag=ENTRY_TAG, huge_tree=True, recover=True)
    sys.stdout.write("[")
    while True:
        try:
            _, entry = next(entries)
            if quickExclude(entry):
                continue
            reading = getReading(entry)
            if reading and onlyKat(reading):
                entry_sequence = getSequence(entry)
                surface_form = getSurface(entry) or reading
                gloss = getGloss(entry)
                strict_eng = getStrictEng(entry)
                wasei = getWasei(entry)
                sys.stdout.write(
                    f"({entry_sequence}, {reading}, {gloss}, {strict_eng}, {wasei})"
                )
                sys.stdout.flush()
                with sqlite3.connect(str(DB_PATH.resolve())) as conn:
                    try:
                        conn.execute(
                            f"""
                        INSERT INTO
                           gairaigo (
                              entry_sequence,
                              japanese,
                              reading,
                              gloss,
                              strict_eng,
                              wasei
                           )
                           VALUES
                              (?, ?, ?, ?, ?, ?)
                           ;
                     """,
                            (
                                entry_sequence,
                                surface_form,
                                reading,
                                gloss,
                                strict_eng,
                                wasei,
                            ),
                        )
                    except sqlite3.IntegrityError:
                        conn.execute(
                            f"""
                        UPDATE
                           gairaigo
                        SET
                           japanese = ?,
                           reading = ?,
                           gloss = ?,
                           strict_eng = ?,
                           wasei = ?
                        WHERE
                           entry_sequence = ?
                     """,
                            (
                                surface_form,
                                reading,
                                gloss,
                                strict_eng,
                                wasei,
                                entry_sequence,
                            ),
                        )
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
        except ET.XMLSyntaxError as e:
            print("Skipping error: ", e)
            continue
        except StopIteration:
            break
        finally:
            try:
                entry.clear()
            except:
                pass
    sys.stdout.write("]\n")
    sys.stdout.flush()
    print("Done with the dump!")


if __name__ == "__main__":
    makeTable()
    scan_dict()
