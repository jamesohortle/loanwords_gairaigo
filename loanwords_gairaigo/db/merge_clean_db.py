#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Merge and clean the entries from the testing and training data. """

import re
import string
import sqlite3
import logging
import itertools
import unicodedata
from typing import Set
from pathlib import Path

import unidecode

logging.basicConfig(level=logging.INFO)

# japanese_whitespace_punctuation = re.compile(r"[\s\u3000\u303f\u30fb]")
whitespace = re.compile(r"\s+")
jap_whitespace = re.compile(r"[\s・]+")
non_ascii = re.compile(r"[^A-Z.'\- ]")
non_katakana = re.compile(r"[^\u30a1-\u30fa\u30fc]")
pronunciation_alternative = re.compile(r"\(\d\)$")
bad_ends = r"[0-9\s!#\$%&\(\)\*\+,\-\./:;<=>\?@\[\\\]^_`{\|}~\u3000\u303f\u30fb]+"
bad_front = re.compile(r"^" + bad_ends)
bad_back = re.compile(bad_ends + r"$")


def norm_en(word: str) -> str:
    # Remove CMUdict's alternative pronunciation notation (e.g., "UPPER(1) -> UPPER").
    normalized_word = pronunciation_alternative.sub("", word)
    normalized_word = (
        "".join(
            c
            for c in unidecode.unidecode(unicodedata.normalize("NFKC", normalized_word))
        )
        .upper()
        .strip()
    )
    normalized_word = bad_front.sub("", bad_back.sub("", normalized_word))
    if non_ascii.search(normalized_word):
        normalized_word = ""
    if not normalized_word:
        logging.warning(f"{word} normalized to empty string!")
    return normalized_word


def norm_ja(word: str) -> str:
    return non_katakana.sub("", unicodedata.normalize("NFKC", word).strip())


HERE = Path(__file__).parent
TYPE_1_DB = HERE / "type_1.db"
TYPE_2_DB = HERE / "type_2.db"
MERGED_DB = HERE / "merged.db"

with sqlite3.connect(str(TYPE_1_DB.resolve())) as conn:
    type_1 = map(
        lambda ej: (norm_en(ej[0]), norm_ja(ej[1])),
        conn.execute(
            """
            SELECT
                english,
                final
            FROM
                type_1
            ;
        """
        ).fetchall(),
    )
conn.close()

with sqlite3.connect(str(TYPE_2_DB.resolve())) as conn:
    type_2 = map(
        lambda ej: (norm_en(ej[0]), norm_ja(ej[1])),
        conn.execute(
            """
                SELECT
                    english,
                    final
                FROM
                    type_2
                ;
            """
        ).fetchall(),
    )
conn.close()

merged = itertools.chain(type_1, type_2)

with sqlite3.connect(str(MERGED_DB.resolve())) as conn:
    conn.execute(
        """
            CREATE TABLE IF NOT EXISTS
                merged (
                    english TEXT UNIQUE,
                    japanese TEXT
                )
            ;
        """
    )
    englishes: Set[str] = set()
    for eng, jap in merged:
        if eng:
            # Split and align multi-phrase entries.
            eng_words = whitespace.split(eng.strip())
            jap_words = jap_whitespace.split(jap.strip())
            if len(eng_words) == len(jap_words):
                for e, j in zip(eng_words, jap_words):
                    if e not in englishes:
                        logging.info(f"Adding {e}, {j}.")
                        englishes.add(e)
                        conn.execute(
                            """
                                INSERT INTO
                                    merged
                                VALUES ( ?, ? )
                                ;
                            """,
                            (e, j),
                        )

    # Fix pronunciations for single letters.
    for kana_alphabet in zip(
        (
            "エー",
            "ビー",
            "シー",
            "ディー",
            "イー",
            "エフ",
            "ジー",
            "エイチ",
            "アイ",
            "ジェー",
            "ケー",
            "エル",
            "エム",
            "エヌ",
            "オー",
            "ピー",
            "キュー",
            "アール",
            "エス",
            "ティー",
            "ユー",
            "ブイ",
            "ダブリュー",
            "エックス",
            "ワイ",
            "ゼット",
        ),
        string.ascii_uppercase,
    ):
        conn.execute(
            """
                UPDATE
                    merged
                SET
                    japanese = ?
                WHERE
                    english
                IS
                    ?
                ;
            """,
            kana_alphabet,
        )
conn.close()
