#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert ARPABET into katakana for Wiktionary entries."""

import sqlite3
from pathlib import Path
from cmu import arpa_to_prekana, arpa_to_kana

ROOT_DIR = Path("..")
DATA_DIR = ROOT_DIR / "data"
DB_DIR = ROOT_DIR / "db"
DB_PATH = DB_DIR / "wiktionary.db"

if __name__ == "__main__":
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
                PRAGMA ENCODING=UTF8;
            """
        )

        try:
            conn.execute(
                """
                    ALTER TABLE
                        wiktionary
                    ADD COLUMN
                        prekana TEXT
                    ;
                """
            )
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(
                """
                    ALTER TABLE
                        wiktionary
                    ADD COLUMN
                        transcription TEXT
                    ;
                """
            )
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(
                """
                    ALTER TABLE
                        wiktionary
                    ADD COLUMN
                        final TEXT
                    ;
                """
            )
        except sqlite3.OperationalError:
            pass

        entries = conn.execute(
            """
                SELECT 
                    pageid,
                    title,
                    arpa
                FROM 
                    wiktionary
                ;
            """
        )

        for pageid, title, arpa in entries:
            conn.execute(
                """
                    UPDATE
                        wiktionary
                    SET
                        prekana = ?,
                        transcription = ?,
                        final = ?
                    WHERE
                        pageid = ?
                    ;
                """,
                (
                    arpa_to_prekana(arpa),
                    arpa_to_kana(arpa),
                    arpa_to_kana(arpa, title.upper()),
                    pageid,
                ),
            )
