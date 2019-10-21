#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quickly check which words still contain errors."""

import re
import sqlite3
from pathlib import Path

from prekana_map import prekana_to_kana

ROOT_DIR = Path("..")
DATA_DIR = ROOT_DIR / "data"
DB_DIR = ROOT_DIR / "db"
# DB_PATH = DATA_DIR / "cmudict.db"
DB_PATH = DB_DIR / "britfone.db"

not_kat_regex = re.compile(r"[^\u30a0-\u30ff\u31f0-\u31ff]")


def onlyKat(s):
    return True if not_kat_regex.search(s) == None else False


with sqlite3.connect(str(DB_PATH.resolve())) as conn:
    conn.execute(
        """
         PRAGMA ENCODING=UTF8;
      """
    )

    errors = conn.execute(
        """
         SELECT
            prekana
         FROM
            hand_mapping
         WHERE
            INSTR(transcription, '？') > 0
         OR
            INSTR(transcription, '⚠️') > 0
         ;
      """
    )

    erroneous_symbs = set()
    for e in errors:
        symbs = e[0].split(" ")

        for s in symbs:
            if prekana_to_kana.get(s) in {"？", "⚠", None}:
                erroneous_symbs.add(s)

    error_count = {symb: None for symb in erroneous_symbs}
    for symb in erroneous_symbs:
        these_errors = conn.execute(
            """
            SELECT
               *
            FROM
               hand_mapping
            WHERE
               INSTR(prekana, ?) > 0
            OR
               INSTR(transcription, '⚠️') > 0
            ;
         """,
            (symb,),
        )
        error_count[symb] = len(these_errors.fetchall())

    print(
        f"Found {len(erroneous_symbs)} symbols that don't map anywhere with occurrences:"
    )
    print(
        sorted(error_count.items(), key=lambda kv: (kv[1], kv[0]), reverse=True) or "{}"
    )

    results = conn.execute(
        """
         SELECT
            english,
            pronunciation,
            prekana,
            transcription,
            final
         FROM
            hand_mapping
         ;
      """
    )

    print("Bad Final transcriptions:")
    how_many = 0
    for r in results:
        if not onlyKat(r[-1]):
            print(r)
            how_many += 1
    print(f"{how_many} rows returned.")
