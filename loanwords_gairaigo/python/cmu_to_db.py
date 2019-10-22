#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Read the CMU dictionary data into an SQLite database. """

import sqlite3
import string
from pathlib import Path

ROOT_DIR = Path("..")
DATA_DIR = ROOT_DIR / "data"
DB_DIR = ROOT_DIR / "db"
PYTH_DIR = ROOT_DIR / "python"

DB_PATH = DB_DIR / "cmudict.db"
CMU_PATH = DATA_DIR / "cmudict-0.7b.txt"
PHONE_PATH = DATA_DIR / "cmudict-0.7b.phones.txt"
SYMB_PATH = DATA_DIR / "cmudict-0.7b.symbols.txt"


# Only take lines that start with letters or maybe an apostrophe (e.g., "'twas").
non_starters = tuple(
    list(string.punctuation.replace("'", ""))
    + [
        "'APOSTROPHE",
        "'END-QUOTE",
        "'END-INNER-QUOTE",
        "'END-QUOTE",
        "'INNER-QUOTE",
        "'QUOTE",
        "'SINGLE-QUOTE",
    ]
)

# fmt: off
with sqlite3.connect(str(DB_PATH.resolve())) as conn, \
    CMU_PATH.open(mode="r", encoding="cp437") as cmu_dict, \
    PHONE_PATH.open(mode="r") as phone_file, \
    SYMB_PATH.open(mode="r") as symbols_file:
# fmt: on
    conn.execute(
        """
            PRAGMA ENCODING=UTF8;
        """
    )

    conn.execute(
        """
            CREATE TABLE IF NOT EXISTS main (
                english text UNIQUE,
                pronunciation text
            )
            ;
        """
    )

    pairs = [
        tuple(line.strip().split("  "))
        for line in cmu_dict.readlines()
        if not line.startswith(non_starters)
    ]

    for p in pairs:
        print(p)
        try:
            conn.execute(
                """
                INSERT INTO main (
                    english,
                    pronunciation
                )
                VALUES (
                    ?,
                    ?
                )
                ;
                """,
                p,
            )
        except sqlite3.IntegrityError:
            conn.execute(
                """
                UPDATE main
                SET pronunciation = ?
                WHERE english = ?
                ;
                """,
                tuple(reversed(p)),
            )

    conn.execute(
        """
            CREATE TABLE IF NOT EXISTS phones (
                phone text UNIQUE,
                class text
            )
        """
    )

    phones = [tuple(ph.strip().split("\t")) for ph in phone_file.readlines()]

    for ph in phones:
        print(ph)
        try:
            conn.execute(
                """
                    INSERT INTO phones (
                        phone,
                        class
                    )
                    VALUES (
                        ?,
                        ?
                    )
                    ;
                """,
                ph,
            )
        except sqlite3.IntegrityError:
            conn.execute(
                """
                    UPDATE phones
                    SET class = ?
                    WHERE phone = ?
                    ;
                """,
                tuple(reversed(ph)),
            )

    conn.execute(
        """
            CREATE TABLE IF NOT EXISTS symbols (
                symbol text UNIQUE
            )
            ;
        """
    )

    symbs = [(symb.strip(),) for symb in symbols_file.readlines()]

    for symb in symbs:
        print(symb)
        try:
            conn.execute(
                """
                    INSERT INTO symbols (
                        symbol
                    )
                    VALUES (
                        ?
                    )
                    ;
                """,
                symb,
            )
        except sqlite3.IntegrityError:
            pass
