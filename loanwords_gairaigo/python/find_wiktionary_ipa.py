#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find all Wiktionary pages in Category:English terms with IPA pronunciation."""

import sqlite3
import requests
from time import sleep
from pathlib import Path

ROOT_DIR = Path("..")
DATA_DIR = ROOT_DIR / "data"
DB_DIR = ROOT_DIR / "db"
DB_PATH = DB_DIR / "wiktionary.db"

with sqlite3.connect(str(DB_PATH.resolve())) as conn:
    conn.execute(
        """
         PRAGMA ENCODING=UTF8;
      """
    )

    conn.execute(
        """
         CREATE TABLE IF NOT EXISTS
            wiktionary (
               pageid INTEGER UNIQUE,
               title TEXT
            )
         ;
      """
    )

S = requests.Session()

URL = "https://en.wiktionary.org/w/api.php"

PARAMS = {
    "action": "query",
    "list": "categorymembers",
    "cmtitle": "Category:English terms with IPA pronunciation",
    "cmlimit": 500,
    "format": "json",
}
p = PARAMS.copy()


# Wiktionary has (as of 24/05/2019) 52,894 words in this category.
# This means that this script takes about 2 minutes to run (assuming no latency).
while True:
    sleep(1)
    DATA = S.get(url=URL, params=p).json()

    for page in DATA["query"]["categorymembers"]:
        print(page["pageid"], page["title"])
        with conn:
            try:
                conn.execute(
                    """
                  INSERT INTO
                     wiktionary (
                        pageid,
                        title
                     )
                  VALUES (
                     ?, ?
                  )
                  ;
               """,
                    (page["pageid"], page["title"]),
                )
            except sqlite3.IntegrityError:
                conn.execute(
                    """
                  UPDATE
                     wiktionary
                  SET
                     title = ?
                  WHERE
                     pageid = ?
                  ;
               """,
                    (page["title"], page["pageid"]),
                )

    if "continue" in DATA:
        p = PARAMS.copy()
        p.update(DATA["continue"])
    else:
        break
