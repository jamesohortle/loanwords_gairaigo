#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure statistics for the data we have gathered."""

import json
import sqlite3
from pathlib import Path

ROOT = Path("..")
DATA_DIR = ROOT / "data"
DB_DIR = ROOT / "db"
PYTHON_DIR = ROOT / "python"
TRAIN_DB = DB_DIR / "train.db"
TRAIN_TBL = "train"
TEST_DB = DB_DIR / "test.db"
TEST_TBL = "test"
ENGLISH_COL = "english"
PREKANA_COL = "prekana"
FINAL_COL = "final"
TRAIN_JSON = PYTHON_DIR / "train.json"
TEST_JSON = PYTHON_DIR / "test.json"

# Training data statistics.
train_stats = dict()
with sqlite3.connect(str(TRAIN_DB.resolve())) as conn:
    count = conn.execute(
        f"""
            SELECT
                COUNT(*)
            FROM
                {TRAIN_TBL}
            ;
        """
    ).fetchone()
    print(count)
    train_stats["count"] = count

    max_english = conn.execute(
        f"""
            SELECT
                LENGTH({ENGLISH_COL}), *
            FROM
                {TRAIN_TBL}
            ORDER BY
                LENGTH({ENGLISH_COL})
            DESC LIMIT 10
            ;
        """
    ).fetchall()
    print(max_english)
    train_stats["max_english"] = max_english

    max_prekana = conn.execute(
        f"""
            SELECT
                LENGTH({PREKANA_COL}), *
            FROM
                {TRAIN_TBL}
            ORDER BY
                LENGTH({PREKANA_COL})
            DESC LIMIT 10
            ;
        """
    ).fetchall()
    print(max_prekana)
    train_stats["max_prekana"] = max_prekana

    max_final = conn.execute(
        f"""
            SELECT
                LENGTH({FINAL_COL}), *
            FROM
                {TRAIN_TBL}
            ORDER BY
                LENGTH({FINAL_COL})
            DESC LIMIT 10
            ;
        """
    ).fetchall()
    print(max_final)
    train_stats["max_final"] = max_final

    english_rows = conn.execute(
        f"""
            SELECT
                {ENGLISH_COL}
            FROM
                {TRAIN_TBL}
            ;
        """
    )
    english_char_counts = dict()
    for row in english_rows.fetchall():
        chars = list(row[0])
        for c in chars:
            if c not in english_char_counts:
                english_char_counts[c] = 1
            else:
                english_char_counts[c] += 1
    print(len(english_char_counts), english_char_counts)
    train_stats["english_char_counts"] = english_char_counts

    prekana_rows = conn.execute(
        f"""
            SELECT
                {PREKANA_COL}
            FROM
                {TRAIN_TBL}
            ;
        """
    )
    prekana_token_counts = dict()
    for row in prekana_rows.fetchall():
        tokens = row[0].split(" ")
        for t in tokens:
            if t not in prekana_token_counts:
                prekana_token_counts[t] = 1
            else:
                prekana_token_counts[t] += 1
    print(len(prekana_token_counts), prekana_token_counts)
    train_stats["prekana_token_counts"] = prekana_token_counts

    final_rows = conn.execute(
        f"""
            SELECT
                {FINAL_COL}
            FROM
                {TRAIN_TBL}
            ;
        """
    )
    final_char_counts = dict()
    for row in final_rows.fetchall():
        chars = list(row[0])
        for c in chars:
            if c not in final_char_counts:
                final_char_counts[c] = 1
            else:
                final_char_counts[c] += 1
    print(len(final_char_counts), final_char_counts)
    train_stats["final_char_counts"] = final_char_counts

with TRAIN_JSON.open(mode="w", encoding="utf8") as train_json:
    json.dump(train_stats, train_json)

# Test data statistics.
test_stats = dict()
with sqlite3.connect(str(TEST_DB.resolve())) as conn:
    count = conn.execute(
        f"""
            SELECT
                COUNT(*)
            FROM
                {TEST_TBL}
            ;
        """
    ).fetchone()
    print(count)
    train_stats["count"] = count

    max_english = conn.execute(
        f"""
            SELECT
                LENGTH({ENGLISH_COL}), *
            FROM
                {TEST_TBL}
            ORDER BY
                LENGTH({ENGLISH_COL})
            DESC LIMIT 10
            ;
        """
    ).fetchall()
    print(max_english)
    test_stats["max_english"] = max_english

    max_final = conn.execute(
        f"""
            SELECT
                LENGTH({FINAL_COL}), *
            FROM
                {TEST_TBL}
            ORDER BY
                LENGTH({FINAL_COL})
            DESC LIMIT 10
            ;
        """
    ).fetchall()
    print(max_final)
    test_stats["max_final"] = max_final

    english_rows = conn.execute(
        f"""
            SELECT
                {ENGLISH_COL}
            FROM
                {TEST_TBL}
            ;
        """
    )
    english_char_counts = dict()
    for row in english_rows.fetchall():
        chars = list(row[0])
        for c in chars:
            if c not in english_char_counts:
                english_char_counts[c] = 1
            else:
                english_char_counts[c] += 1
    print(len(english_char_counts), english_char_counts)
    test_stats["english_char_counts"] = english_char_counts

    final_rows = conn.execute(
        f"""
            SELECT
                {FINAL_COL}
            FROM
                {TEST_TBL}
            ;
        """
    )
    final_char_counts = dict()
    for row in final_rows.fetchall():
        chars = list(row[0])
        for c in chars:
            if c not in final_char_counts:
                final_char_counts[c] = 1
            else:
                final_char_counts[c] += 1
    print(len(final_char_counts), final_char_counts)
    test_stats["final_char_counts"] = final_char_counts

with TEST_JSON.open(mode="w", encoding="utf8") as test_json:
    json.dump(test_stats, test_json)
