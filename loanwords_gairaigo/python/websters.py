#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract headwords and their syllabifications (hyphenations?) from Webster's."""

import re
import sys
import sqlite3

from pathlib import Path
from html import unescape

from lxml import etree as ET
from bs4 import BeautifulSoup

# Filepaths.
ROOT_DIR = Path("..")
DATA_DIR = ROOT_DIR / "data"
DB_DIR = ROOT_DIR / "db"
DB_PATH = DB_DIR / "websters.db"
RAW_PATH = DATA_DIR / "websters-unabridged.html"
WEBSTER_PATH = DATA_DIR / "websters-unabridged-mod.html"

# XML tag definitions.
ENTRY_TAG = "h1"
SEGMENTATION_TAG = "hw"


def genInts():
    i = 0
    while True:
        yield i
        i += 1


unclosed = re.compile(r"<[^>/]+>\w+<[^>/]+>")


def findUnclosed():
    with RAW_PATH.open(mode="r", encoding="utf-8") as raw:
        for line in raw:
            for uncl in unclosed.finditer(line):
                print(uncl.group(0))


xpage = re.compile(r"<Xpage=(\d)>")
unclosedItalic = re.compile(r"<it?>([^<]+)<it?>")


def cleanDict():
    with RAW_PATH.open(mode="r", encoding="utf-8") as raw, WEBSTER_PATH.open(
        mode="w", encoding="utf-8"
    ) as web:
        for line in raw:
            print(line)
            match = xpage.match(line)
            if match:
                line = xpage.sub(line, f"<Xpage={match.group(1)}/>")

            while unclosedItalic.search(line):
                line = unclosedItalic.sub(
                    line, f"<i>{unclosedItalic.search(line).group(1)}</i>"
                )

            web.write(line)


def makeTable():
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
            PRAGMA ENCODING=UTF8;
         """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS
               websters (
                  entryid INTEGER UNIQUE,
                  headword TEXT,
                  segmentation TEXT
               )
            ;
         """
        )


def scanDict():
    """Dictionary is malformed HTML, so this will keep breaking until the dictionary itself is fixed."""
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
                PRAGMA ENCODING=UTF8;
            """
        )

    entries = ET.iterparse(
        str(WEBSTER_PATH.resolve()),
        tag=(ENTRY_TAG, SEGMENTATION_TAG),
        # events=("start", "end",),
        html=True,
        recover=True,
    )
    entry_ids = genInts()
    while True:
        try:
            _, entry = next(entries)
            print("".join(entry.itertext()))
            if entry.tag == ENTRY_TAG:
                entry_text = "".join(entry.itertext())
                while entry.tag != SEGMENTATION_TAG:
                    _, entry = next(entries)
                segmentation_text = "".join(entry.itertext())
                entry_id = next(entry_ids)
                print(entry_id, entry_text, segmentation_text)
                with conn:
                    try:
                        conn.execute(
                            """
                                INSERT INTO 
                                    websters (
                                        entryid,
                                        headword,
                                        segmentation
                                    )
                                VALUES (
                                    ?, ?, ?
                                )
                                ;
                            """,
                            (entry_id, entry_text, segmentation_text),
                        )
                    except sqlite3.IntegrityError:
                        conn.execute(
                            """
                                UPDATE
                                    websters
                                SET
                                    headword = ?,
                                    segmentation = ?
                                WHERE
                                    entryid = ?
                                ;
                            """,
                            (entry_text, segmentation_text, entry_id),
                        )
        except StopIteration:
            break


# A custom version of IBM codepage 437, it seems.
strange_escapes = {
    "\\'80": "C",  # "Ç",
    "\\'81": "u",  # "ü",
    "\\'82": "e",  # "é",
    "\\'83": "a",  # "â",
    "\\'84": "a",  # "ä",
    "\\'85": "a",  # "à",
    # "\\'86": "", # "å", doesn't appear in headwords
    "\\'87": "c",  # "ç",
    "\\'88": "e",  # "ê",
    "\\'89": "e",  # "ë",
    "\\'8a": "e",  # "è",
    "\\'8b": "i",  # "ï",
    "\\'8c": "i",  # "î",
    "\\'90": "E",  # "É",
    "\\'91": "e",  # "æ",
    "\\'92": "E",  # "Æ",
    "\\'93": "o",  # "ô",
    "\\'94": "o",  # "ö",
    # "\\'95": "", # "ò", doesn't appear in headwords
    "\\'96": "u",  # "û",
    "\\'97": "u",  # "ù",
    "\\'a4": "n",  # "ñ",
    "\\'b5": "",  # ??
    "\\'c6": "i",  # "ī",
    "\\'d1": "E",  # "Œ",
    "\\'d2": "e",  # "œ",
    "\\'d8": "",  # ??,
    "\\'ee": "a",  # "ã"
}
# strange_escape = re.compile(r"\\\'[\d\w]{2,2}")
start_multi_headword = re.compile(r"<mhw>")
end_multi_headword = re.compile(r"</mhw>", re.MULTILINE)
multi_headword = re.compile(r"<mhw>(.*?)</mhw>", re.MULTILINE)
entry_regex = re.compile(r"<h1>(.+?)</h1>")
segementation_regex = re.compile(r"<hw>(.*)</hw>")
multi_split_regex = re.compile(r",|∨")
non_greedy_segmentation_regex = re.compile(r"(^<hw>|<hw>|^)(.+?)(</hw>|$)")


def scanDictWithRegex():
    """Have to use regexes since dictionary's HTML is malformed."""
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
                PRAGMA ENCODING=UTF8;
            """
        )
    entry_ids = genInts()

    with WEBSTER_PATH.open(mode="r", encoding="utf-8") as web:
        buffer = ""
        lines = iter(web)
        # strange_escapes = set()
        while True:
            try:
                line = unescape(next(lines))
                for key in strange_escapes.keys():
                    line = line.replace(key, strange_escapes[key])
                # for item in map(lambda match: match.group(0), strange_escape.finditer(line)):
                #    strange_escapes.add(item)
                # print(line)
                if start_multi_headword.match(line):
                    while not end_multi_headword.search(line):
                        line += next(lines)
                    continue

                if entry_regex.match(line):
                    buffer += entry_regex.match(line).group(1)
                elif segementation_regex.match(line):
                    buffer += "・" + segementation_regex.match(line).group(1)
                    sys.stdout.write(buffer + "\n")
                    sys.stdout.flush()
                    entry_text, segmentation_text = buffer.split("・")

                    # Multiple segmentations.
                    multi_entries = list(
                        map(lambda x: x.strip(), multi_split_regex.split(entry_text))
                    )
                    if len(multi_entries) > 1:
                        multi_segmentation = list(
                            map(
                                lambda x: x.group(2),
                                non_greedy_segmentation_regex.finditer(
                                    segmentation_text
                                ),
                            )
                        )

                        # Reset failures.
                        if len(multi_entries) != len(multi_segmentation):
                            multi_segmentation = [segmentation_text] * len(
                                multi_entries
                            )
                    else:
                        multi_segmentation = [segmentation_text]

                    with conn:
                        for i, e in enumerate(multi_entries):
                            entry_id = next(entry_ids)
                            sys.stdout.write(
                                "  ".join(
                                    (str(entry_id), e, multi_segmentation[i], "\n")
                                )
                            )
                            sys.stdout.flush()
                            try:
                                conn.execute(
                                    """
                                    INSERT INTO 
                                        websters (
                                            entryid,
                                            headword,
                                            segmentation
                                        )
                                    VALUES (
                                        ?, ?, ?
                                    )
                                    ;
                                """,
                                    (entry_id, e, multi_segmentation[i]),
                                )
                            except sqlite3.IntegrityError:
                                conn.execute(
                                    """
                                    UPDATE
                                        websters
                                    SET
                                        headword = ?,
                                        segmentation = ?
                                    WHERE
                                        entryid = ?
                                    ;
                                """,
                                    (e, multi_segmentation[i], entry_id),
                                )
                    buffer = ""
                else:
                    continue
            except StopIteration:
                break

        # print(len(strange_escapes))
        # print("\n".join(sorted(list(strange_escapes))))


def cleanDb():
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
                PRAGMA ENCODING=UTF8;
            """
        )

        conn.execute(
            """
                DELETE FROM
                    websters
                WHERE
                    headword LIKE ""
                OR
                    headword IS NULL
                OR
                    segmentation LIKE ""
                OR
                    segmentation IS NULL
                OR
                    headword LIKE "%\%"
                OR
                    segmentation LIKE "%\%" 
                OR
                    headword LIKE "%<%" 
                OR
                    segmentation LIKE "%<%" 
                OR
                    headword LIKE "%>%" 
                OR
                    segmentation LIKE "%>%"
                ;
            """
        )


nonAlpha = re.compile(r"[^a-zA-Z\- \']")


def getNumEasy():
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
                PRAGMA ENCODING=UTF8;
            """
        )

        results = conn.execute(
            """
                SELECT
                    entryid,
                    headword,
                    segmentation
                FROM
                    websters
                ;
            """
        )
        cumSum = totalSum = 0
        badEntries = []
        for entryid, headword, segmentation in results:
            totalSum += 1
            if not nonAlpha.search(headword):
                cumSum += 1
                # print(headword, segmentation)
            else:
                badEntries.append(entryid)
        query = (
            """
            SELECT
                *
            FROM
                websters
            WHERE
                entryid
            IN
                ("""
            + ", ".join(["?"] * len(badEntries))
            + ")"
            + """
            ORDER BY
                entryid
            ;
        """
        )
        results = conn.execute(query, tuple(badEntries))

        for r in results:
            print(*r)
        print(f"{totalSum} - {cumSum} = {totalSum - cumSum}")
        print(f"{cumSum} / {totalSum} = {cumSum / totalSum}")


if __name__ == "__main__":
    # findUnclosed()
    # cleanDict()
    makeTable()
    # scanDict()
    scanDictWithRegex()
    cleanDb()
    getNumEasy()
