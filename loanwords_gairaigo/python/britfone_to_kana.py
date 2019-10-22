#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Use the CMU dictionary data to create a mapping from English phonemes to Japanese katakana."""

import re
import sqlite3
from pathlib import Path
from functools import lru_cache

from phonotactics import onsets, codas
from prekana_map import prekana_to_kana
from britfone_utils import (
    vowels,
    semivowels,
    consonants,
    non_geminating,
    symb_to_prekana,
)

digits = re.compile(r"\d+")


def remove_stress(phoneme_list):
    return [re.sub(digits, "", p) for p in phoneme_list]


parenthetical = re.compile(r"\([^)]*\) ?")


def removeParentheticals(s):
    return parenthetical.sub("", s).strip()


multiLongVowel = re.compile(r"ー{2,}")


def removeMultiLongVowels(s):
    return multiLongVowel.sub("ー", s).strip()


def group_japonically(clusters):
    """Group clusters into either
    " - lone vowel
    " - consonant + vowel
    " - semivowel + vowel
    " - consonant + semivowel + vowel.
    """
    new_clusters = []
    ks = consonants.keys()
    ss = semivowels.keys()
    vs = vowels.keys()
    for c in clusters:
        if len(c) == 1:
            prev_coda = []
            cluster = c
        elif len(c) == 2:
            largest_cluster = c
            if largest_cluster[-2] in (ks | ss) and largest_cluster[-1] in vs:
                # We have kv or sv.
                prev_coda = []
                cluster = c[-2:]
            elif largest_cluster[-1] in vs:
                # We have lone v.
                prev_coda = c[:-1]
                cluster = c[-1:]
            else:
                # Must be on a consonant only coda.
                prev_coda = c
                cluster = []
        else:  # len(c) > 2
            largest_cluster = c[-3:]
            if (
                largest_cluster[-3] in ks
                and largest_cluster[-2] in ss
                and largest_cluster[-1] in vs
            ):
                # We have ksv.
                prev_coda = c[:-3]
                cluster = largest_cluster
            elif largest_cluster[-2] in (ks | ss) and largest_cluster[-1] in vs:
                # We have kv or sv.
                prev_coda = c[:-2]
                cluster = c[-2:]
            elif largest_cluster[-1] in vs:
                # We have lone v.
                prev_coda = c[:-1]
                cluster = c[-1:]
            else:
                # Must be on a consonant only coda.
                prev_coda = c
                cluster = []
        if prev_coda:
            new_clusters.append(prev_coda)
        if cluster:
            new_clusters.append(cluster)

    # Now, break up or replace consonant clusters not ending in vowels.
    old_clusters = new_clusters.copy()
    new_clusters = []
    for i, c in enumerate(old_clusters):
        if c == ["t", "s"]:
            new_clusters.append(["TS", None])
        elif (
            (i != len(old_clusters) - 1)
            and c == ["t"]
            and old_clusters[i + 1][0] == "s"
        ):
            old_clusters[i + 1][0] = "TS"  # Update the next cluster.
        elif c == ["m", "p"]:
            new_clusters.append(["NP", None])
        elif (
            (i != len(old_clusters) - 1)
            and c == ["m"]
            and old_clusters[i + 1][0] == "p"
        ):
            new_clusters.append(["NN", None])
        elif c == ["m", "b"]:
            new_clusters.append(["NB", None])
        elif (
            (i != len(old_clusters) - 1)
            and c == ["m"]
            and old_clusters[i + 1][0] == "b"
        ):
            new_clusters.append(["NN", None])
        elif c[0:2] == ["d", "w"]:
            new_clusters.append(["d", None])
            new_clusters.append(c[1:])
        elif c[-1] not in vs:
            for consonant in c:
                new_clusters.append([consonant, None])
        else:
            new_clusters.append(c)

    return new_clusters


def fix_rhoticity(clusters):
    """ Check ER and R phones and make the following fixes.
    " - R + vowel ==> R + vowel (no change)
    " - cons + R + cons ==> cons + R + cons (no change)
    " - cons + R + vowel ==> cons + R + vowel (no change)
    " - ER + vowel ==> ア + R + vowel (fishery ==> フィシャリー)
    " - vowel + R + end ==> vowel + ア + end (remove rhotic final) (more ==> モア)
    " - ER + end ==> アー + end (remove rhotic final and make long) (her ==> ハー)
    " - vowel + R + cons ==> vowel + ー + cons (remove rhotic and make long) (born ==> ボーン)
    " - ER + cons ==> アー + cons (remove rhotic and make long) (burn ==> バーン)
    " - R + W + vowel ==> ア + W + vowel (firewall ==> ファイアウォール)
    """
    if clusters[-1] == ["R", None]:
        clusters[-1] = ["a"]

    if clusters[-1][-1] == "ER":
        clusters[-1][-1] = "a -"

    new_clusters = []
    for i, cluster in enumerate(clusters):
        new_cluster = cluster.copy()
        if cluster[-1] == "ER" and clusters[i + 1][0] not in vowels.keys():
            new_cluster[-1] = "a -"
        elif cluster[-1] == "ER" and clusters[i + 1][0] in vowels.keys():
            new_cluster[-1] = "a"
            clusters[i + 1].insert(0, "R")
        elif cluster == ["R", None] and clusters[i + 1][0] not in vowels.keys():
            new_cluster = ["-"]
        else:
            pass

        # Avoid rw + vowel.
        if new_cluster[0:2] == ["R", "W"]:
            new_cluster = ["a ", "W"] + new_cluster[-1:]

        new_clusters.append(new_cluster)

    return new_clusters


def fix_gemination(clusters):
    """ Gemination (ッ) cannot occur in the following positions:
    " - at the start of a word;
    " - at the end of a word;
    " - before voiced, nasal or liquid consonants;
    " - before vowels.
    " In our case, we only have AE ==> a x, and AE cannot occur in initial position.
    " Hence, need only check second, third and fourth cases.
    """

    if clusters[-1][-1] in {"ˈæ", "ˌæ"}:
        clusters[-1][-1] = "a"
    elif clusters[-1][-1] in {"ˈɒ", "ˌɒ"}:
        clusters[-1][-1] = "o"

    for i, cluster in enumerate(clusters):
        if cluster[-1] in {"ˈæ", "ˌæ", "ˈɒ", "ˌɒ"}:
            if clusters[i + 1][0] in non_geminating.keys():
                cluster[-1] = "a" if cluster[-1] in {"ˈæ", "ˌæ"} else "o"

    return clusters


def fix_final_DZ_TS(clusters):
    if clusters[-2:] == [["d", None], ["z", None]]:
        clusters = clusters[:-2] + [["z", None]]
    elif clusters[-2:] == [["t", None], ["s", None]]:
        clusters = clusters[:-2] + [["ts", None]]
    return clusters


def group_by_cluster(phoneme_list):
    # Find vowel indexes.
    vowel_indexes = [i for i, p in enumerate(phoneme_list) if p in vowels.keys()]

    # Make slice indexes.
    slice_indexes = [0] + list(map(lambda i: i + 1, vowel_indexes))

    # Make clusters.
    clusters = []
    for i in range(len(slice_indexes) - 1):
        clusters.append(phoneme_list[slice_indexes[i] : slice_indexes[i + 1]])

    # Get the last ones, if needed.
    if slice_indexes[-1] != len(phoneme_list):
        clusters.append(phoneme_list[slice_indexes[-1] :])

    # Group into syllables with v, kv, sv or ksv structure where
    # v = vowel, k = consonant, s = semivowel.
    clusters = group_japonically(clusters)

    ## Do we even need to fix rhoticity for RP?
    # Fix how R and ER are interpreted.
    # clusters = fix_rhoticity(clusters)

    # Fix where gemination ッ can occur.
    # print(clusters)
    clusters = fix_gemination(clusters)

    # Final ["D", None], ["Z", None] to just ["Z", None] and
    # final ["T", None], ["S", None] to just ["TS", None].
    clusters = fix_final_DZ_TS(clusters)

    return clusters


def symbs_to_prekana(clusters):
    prekanas = []
    for c in clusters:
        prekana = ""
        for symb in c:
            prekana += symb_to_prekana.get(symb, symb)
        prekanas.append(prekana)

    return " ".join(prekanas)


@lru_cache()
def ipa_to_prekana(ipa_string):
    if not ipa_string:
        return ""
    phonemes = ipa_string.split(" ")
    # phonemes = remove_stress(phonemes)
    clusters = group_by_cluster(phonemes)

    return symbs_to_prekana(clusters)


def ipa_to_kana(ipa_string, english_string=""):
    prekanas = ipa_to_prekana(ipa_string)
    kanas = "".join([prekana_to_kana.get(p, p) for p in prekanas.split(" ")])

    # Fix some common transcriptions that are based on English spelling.
    # TODO: This is a bottleneck due to all the cases.
    # See if we can't transform it into a regex, perhaps, and make it faster.
    if english_string:
        english_string = removeParentheticals(english_string)

        #########################################
        # Words starting/ending with "WOOD(S)". #
        #########################################
        if english_string.startswith("WOODS") and kanas.startswith("ウドズ"):
            kanas = "ウッズ" + kanas[3:]
        elif english_string.endswith(("WOODS", "WOOD'S")) and kanas.endswith("ウズ"):
            kanas = kanas[:-2] + "ウッズ"
        elif english_string.startswith("WOOD") and kanas.startswith("ウド"):
            kanas = "ウッド" + kanas[2:]
        elif english_string.endswith("WOOD") and kanas.endswith("ウド"):
            kanas = kanas[:-2] + "ウッド"

        ################################
        # Words with initial o sounds. #
        ################################
        if not english_string[1:3].startswith(("OW", "OU", "OO")):
            if english_string.startswith(("CO", "KO")) and kanas.startswith("カ"):
                kanas = "コ" + kanas[1:]

            elif english_string.startswith("GO") and kanas.startswith("ガ"):
                kanas = "ゴ" + kanas[1:]

            elif (
                english_string.startswith("SO")
                and not english_string.startswith("SOMM")
                and english_string
                not in [
                    "SON-OF-A-BITCH",
                    "SONS-IN-LAW",
                    "SON-IN-LAW",
                    "SONNY",
                    "SONNY'S",
                    "SON'S",
                    "SONS'",
                    "SONS",
                    "SON",
                ]
                and kanas.startswith("サ")
            ):
                kanas = "ソ" + kanas[1:]

            # ZOW- does not exist in the data.
            elif english_string.startswith("ZO") and kanas.startswith("ザ"):
                kanas = "ゾ" + kanas[1:]

            elif (
                english_string.startswith("TO")
                and not english_string.startswith("TOBACCO")
                and kanas.startswith("タ")
            ):
                kanas = "ト" + kanas[1:]

            elif (
                english_string.startswith("NO")
                and not english_string.startswith(("NOTHIN", "NOTHER"))
                and kanas.startswith("ナ")
            ):
                kanas = "ノ" + kanas[1:]

            elif (
                english_string.startswith("HO")
                and not english_string.startswith("HONEY")
                and kanas.startswith("ハ")
            ):
                kanas = "ホ" + kanas[1:]

            elif english_string.startswith("FO") and kanas.startswith("ファ"):
                kanas = "フォ" + kanas[1:]

            elif english_string.startswith("BO") and kanas.startswith("バ"):
                kanas = "ボ" + kanas[1:]

            elif english_string.startswith("PO") and kanas.startswith("パ"):
                kanas = "ポ" + kanas[1:]

            elif (
                english_string.startswith("MO")
                and not english_string.startswith("MOTHER")
                and kanas.startswith("マ")
            ):
                kanas = "モ" + kanas[1:]

            elif english_string.startswith("YO") and kanas.startswith("ヤ"):
                kanas = "ヨ" + kanas[1:]

            elif (
                english_string.startswith(("LO", "RO"))
                and not english_string.startswith("LOVE")
                and kanas.startswith("ラ")
            ):
                kanas = "ロ" + kanas[1:]

            elif (
                english_string.startswith("WO")
                and not english_string.startswith(
                    ("WORSHIP", "WONDER", "WORLD", "WORST", "WORSE", "WORD", "WORK")
                )
                and kanas.startswith("ワ")
            ):
                kanas = "ウォ" + kanas[1:]

        ###############################
        # Words with certain endings. #
        ###############################
        if english_string.endswith("ION"):
            if kanas.endswith("シャン"):
                kanas = kanas[:-3] + "ション"
            elif kanas.endswith("ジャン"):
                kanas = kanas[:-3] + "ジョン"
        elif english_string.endswith("NG") and kanas.endswith("ン"):
            kanas += "グ"
        elif english_string.endswith("ISM"):
            if kanas.endswith("イザム"):
                kanas = kanas[:-3] + "イズム"
            elif kanas.endswith("ザム"):
                kanas = kanas[:-2] + "ズム"
        elif english_string.endswith("MENT") and kanas.endswith("マント"):
            kanas = kanas[:-3] + "メント"
        # Not sure if this is correct, seems there is no consensus.
        # elif english_string.endswith("ED") and kanas.endswith("ティド"):
        #    ?kanas = kanas[:-3] + "テド"
        #    ?kanas = kanas[:-3] + "ティッド"
        #    leave alone?

    # Remove multiple 長音符.
    kanas = removeMultiLongVowels(kanas)

    return kanas


# for t in test_data:
#    print(t[0])
#    print(t[1])
#    prekanas = arpa_to_prekana(t[1])
#    print(prekanas)
#    print("".join([prekana_to_kana[p] for p in prekanas.split(" ")]))

ROOT_DIR = Path("..")
DATA_DIR = ROOT_DIR / "data"
DB_DIR = ROOT_DIR / "db"
DB_PATH = DB_DIR / "britfone.db"

if __name__ == "__main__":
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
                PRAGMA ENCODING=UTF8;
            """
        )

        conn.execute(
            """
                CREATE TABLE IF NOT EXISTS
                    hand_mapping (
                        english text UNIQUE,
                        pronunciation text,
                        prekana text,
                        transcription text,
                        final TEXT
                    )
                ;
            """
        )

        entries = conn.execute(
            """
                SELECT 
                    english, ipa
                FROM 
                    main
                ;
            """
        )

        for e in entries:
            try:
                conn.execute(
                    """
                        INSERT INTO
                            hand_mapping (
                            english,
                            pronunciation,
                            prekana,
                            transcription,
                            final
                        )
                        VALUES
                            (?, ?, ?, ?, ?)
                        ;
                    """,
                    (
                        e[0],
                        e[1],
                        ipa_to_prekana(e[1]),
                        ipa_to_kana(e[1]),
                        ipa_to_kana(e[1], e[0]),
                    ),
                )
            except sqlite3.IntegrityError:
                conn.execute(
                    """
                        UPDATE
                            hand_mapping
                        SET
                            prekana = ?,
                            transcription = ?,
                            final = ?
                        WHERE
                            english = ?
                        ;
                    """,
                    (
                        ipa_to_prekana(e[1]),
                        ipa_to_kana(e[1]),
                        ipa_to_kana(e[1], e[0]),
                        e[0],
                    ),
                )
