#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract the IPA from the Wiktionary dump."""

import re
import sys
import sqlite3
from pathlib import Path
from itertools import chain
from functools import lru_cache
from unicodedata import normalize

from lxml import etree as ET


DB_PATH = Path("../db/wiktionary.db")

useCurr = True
currVer = "0.10"
testVer = "0.3"
ver = currVer if useCurr else testVer
DUMP_ENG = str(Path("../data/enwiktionary-latest-pages-articles.xml").resolve())
PAGE_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}page"
TITLE_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}title"
REVISION_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}revision"
TEXT_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}text"
ID_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}id"


def alterTable():
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        try:
            conn.execute(
                """
                    ALTER TABLE
                        wiktionary
                    ADD COLUMN
                        ipa TEXT
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
                        arpa TEXT
                    ;
                """
            )
        except sqlite3.OperationalError:
            pass


halfwidth_parenthetical = re.compile(r"\([^)]*\)[ \u3000\u303f]?")
fullwidth_parenthetical = re.compile(r"（[^）]*）[ \u3000\u303f]?")


def removeParentheticals(s):
    s = halfwidth_parenthetical.sub("", s).strip()
    s = fullwidth_parenthetical.sub("", s).strip()
    return s


commaQualifier = re.compile(r", .+$")


def removeCommaQualifier(s):
    s = commaQualifier.sub("", s).strip()
    return s


def getTitle(page):
    return removeCommaQualifier(
        removeParentheticals("".join(page.find(TITLE_TAG).itertext()))
    )


def getText(page):
    return "".join(page.find(REVISION_TAG).find(TEXT_TAG).itertext())


def getId(page):
    return int("".join(page.find(ID_TAG).itertext()))


not_kat_regex = re.compile(r"[^\u30a0-\u30ff\u31f0-\u31ff]")


def onlyKat(s):
    return True if not_kat_regex.search(s) is None else False


def ipaLettersMap(ipa):
    ipas = map(lambda s: s.strip().strip("'").strip(), ipa.split("|"))
    letterMap = {
        "A": "eɪ",
        "B": "biː",
        "C": "siː",
        "D": "diː",
        "E": "iː",
        "F": "ɛf",
        "G": "dʒiː",
        "H": "eɪtʃ",
        "I": "aɪ",
        "J": "dʒeɪ",
        "K": "keɪ",
        "L": "ɛl",
        "M": "ɛm",
        "N": "ɛn",
        "O": "oʊ",
        "P": "piː",
        "Q": "kjuː",
        "R": "ɑr",
        "S": "ɛs",
        "T": "tiː",
        "U": "juː",
        "V": "viː",
        "W": "ˈdʌbəl juː",
        "X": "ɛks",
        "Y": "waɪ",
        "Z": "ziː",
    }
    return " ".join(letterMap.get(i, "") for i in ipas)


ipaSlashes = re.compile(r"(/)([^/]+)(/)")
ipaBrackets = re.compile(r"(\[)([^]]+)(\])")
ipaLetters = re.compile(r"(\|[A-Z']{1,2})+")
ipaPipes = re.compile(r"(\|)([^\|]+)(\|)")


def extractIpa(s):
    ipa = ""
    if "/" in s:
        ipa = ipaSlashes.search(s).group(2)
    elif "[" in s:
        ipa = ipaBrackets.search(s).group(2)
    else:
        if "IPA letters" in s:
            ipa = ipaLettersMap(ipaLetters.search(s).group(0))
        else:
            ipa = ipaPipes.search(s).group(2)

    return ipa if ipa else None


pronunciationSectionTag = re.compile(r"={2,}Pronunciation={2,}")
ipaTag = re.compile(r"{{IPA[^}]*(lang=)?en[^}]*}}")
audioIpaTag = re.compile(r"{{audio-IPA[^}]*(lang=)?en[^}]*}}")
acronymTag = re.compile(r"{{IPA letters[^}]*(lang=)?en[^}]*}}")


def getPronunciation(page):
    page_text = getText(page)
    hasPronSect = True if pronunciationSectionTag.search(page_text) else False
    ipas = ";".join(
        set(
            map(
                extractIpa,
                map(
                    lambda match: match.group(0),
                    chain(
                        ipaTag.finditer(page_text),
                        audioIpaTag.finditer(page_text),
                        acronymTag.finditer(page_text),
                    ),
                ),
            )
        )
    ).strip()

    if hasPronSect and ipas:
        return ipas
    elif ipas and not hasPronSect:
        return ipas  # "No pron" + ipas
    elif hasPronSect and not ipas:
        return None  # "Regex Failed" + ipas
    else:
        return None  # "N/A" + ipas


def getIpa():
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
                PRAGMA ENCODING=UTF8;
            """
        )

        results = conn.execute(
            """
                SELECT
                    pageid
                FROM
                    wiktionary
                ;
            """
        )

        pageids = {int(r[0]) for r in results}

    sys.stdout.write("[")
    sys.stdout.flush()
    pages = ET.iterparse(DUMP_ENG, tag=PAGE_TAG, huge_tree=True, recover=True)
    while pageids:
        try:
            _, page = next(pages)
            pid = getId(page)
            if pid in pageids:
                pageids.remove(pid)
                eng_title = getTitle(page)
                ipa = getPronunciation(page)
                sys.stdout.write(f"({pid}, {eng_title}, {ipa})")

                with conn:
                    conn.execute(
                        """
                            UPDATE
                                wiktionary
                            SET
                                ipa = ?
                            WHERE
                                pageid = ?
                            ;
                        """,
                        (ipa, pid),
                    )
            else:
                sys.stdout.write(".")
            sys.stdout.flush()
        except ET.XMLSyntaxError as e:
            print("Skipping error:", e)
            continue
        except StopIteration:
            break
        else:
            conn.commit()
        finally:
            try:
                page.clear()
            except:
                pass
    sys.stdout.write("]\n")
    sys.stdout.flush()
    print("Done with the dump!")


nonArpa = re.compile(r"[^ A-Z;()]")
multiWhitespace = re.compile(r"\W+")


def cleanArpa(arpa):
    if not arpa or nonArpa.search(arpa):
        return None
    else:
        return multiWhitespace.sub(" ", arpa).strip()


splitters = re.compile(r";|,|⁓|~")


def cleanDb():
    offset = 10 ** 7
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        conn.execute(
            """
                PRAGMA ENCODING=UTF8;
            """
        )

        # Split up multiple pronunciations so they each have a separate entry.
        results = conn.execute(
            """
                SELECT
                    pageid,
                    title,
                    ipa,
                    arpa
                FROM
                    wiktionary
                WHERE
                    ipa
                LIKE
                    "%;%"
                ;
            """
        )

        for pageid, title, ipa, arpa in results:
            ipa_variants = re.split(splitters, ipa) if ipa else []
            arpa_variants = re.split(splitters, arpa) if arpa else []
            for i, ipa in enumerate(ipa_variants):
                try:
                    conn.execute(
                        """
                            INSERT INTO
                                wiktionary (
                                pageid,
                                title,
                                ipa,
                                arpa
                                )
                            VALUES
                                (?, ?, ?, ?)
                            ;
                        """,
                        ((i * offset) + pageid, title, ipa, arpa_variants[i]),
                    )
                except sqlite3.IntegrityError:
                    conn.execute(
                        """
                            UPDATE
                                wiktionary
                            SET
                                title = ?,
                                ipa = ?,
                                arpa = ?
                            WHERE
                                pageid = ?
                            ;
                        """,
                        (title, ipa, arpa_variants[i], (i * offset) + pageid),
                    )
                except IndexError:
                    print(pageid, title)
                    break

        # Clean all results so that they are convertible.
        results = conn.execute(
            """
                SELECT
                    pageid,
                    arpa
                FROM
                    wiktionary
                    ;
            """
        )

        for pageid, arpa in results:
            if not arpa:
                continue
            else:
                conn.execute(
                    """
                        UPDATE
                            wiktionary
                        SET
                            arpa = ?
                        WHERE
                            pageid = ?
                        ;
                    """,
                    (cleanArpa(arpa), pageid),
                )

        # Set arpa to null where there are unconverted IPA.
        results = conn.execute(
            """
                SELECT
                    pageid,
                    arpa
                FROM
                    wiktionary
                ;
            """
        )

        for pageid, arpa in results:
            if not arpa or nonArpa.search(arpa):
                conn.execute(
                    """
                    UPDATE
                        wiktionary
                    SET
                        arpa = ?
                    WHERE
                        pageid = ?
                    ;
                """,
                    (None, pageid),
                )


digraphAW = re.compile(r"aʊ")
digraphAY = re.compile(r"aɪ")
digraphEY = re.compile(r"eɪ")
digraphOW = re.compile(r"oʊ")
digraphOY = re.compile(r"ɔɪ")
digraphAO = re.compile(r"əʊ")
digraphCCedilla = re.compile(r"c\u0327")  # ç
digraphCH = re.compile(r"t\u0361?ʃ")  # t͡ʃ
digraphJH = re.compile(r"d\u0361?ʒ")  # d͡ʒ
digraphNT = re.compile(r"\u027e\u0303")  # ɾ̃
digraphNAH = re.compile(r"\u027d\u0303")  # ɽ̃
digraphSyllabicL = re.compile(r"l\u0329")  # l̩
digraphSyllabicM = re.compile(r"m\u0329")  # m̩
digraphSyllabicN = re.compile(r"n\u0329")  # n̩
primaryStressMark = re.compile(r"ˈ")
secondaryStressMark = re.compile(r"ˌ")
syllableMarks = re.compile(r"[. ]")


@lru_cache()
def convertIpa(s):
    if not s:
        return ""
    else:
        # \u02b0 = ʰ Modifier letter small H (aspiration).
        # \u1d4a = ᵊ Modifier letter small schwa (reduced schwa or syllabic consonant?).
        # \u02b7 = ʷ Modifier letter small W (labialisation).
        # \u02c0 = ˀ Modifier letter glottal stop (?).
        s = normalize(
            "NFKD",
            s.replace("\u02b0", "")
            .replace("\u1d4a", "")
            .replace("\u027b", "")
            .replace("\u02c0", ""),
        )

    vowels = {
        "aɪ": "AY",
        "1": "AY",
        "eɪ": "EY",
        "2": "EY",
        "oʊ": "OW",
        "3": "OW",
        "ɔɪ": "OY",
        "4": "OY",
        "əʊ": "OW",
        "5": "OW",
        "a": "AE",
        "ɑ": "AA",
        "ɒ": "AO",
        "ɐ": "AH",
        "æ": "AE",
        "ʌ": "AH",
        "ɯ": "AH",
        "ɔ": "AO",
        "aʊ": "AW",
        "0": "AW",
        "ə": "AH",
        "ɚ": "ER",
        "e": "EH",
        "ɛ": "EH",
        "ɝ": "ER",
        "ɜ": "ER",
        "ɪ": "IH",
        "ɨ": "IH",
        "i": "IY",
        "o": "AO",
        "ʊ": "UH",
        "u": "UW",
        "ʉ": "UW",
        "ʋ": "UH",
        "\u0303": "N",  # Nasalisation diacritic.
    }
    foreign_vowels = {
        "ɞ": "AH",
        "ø": "AH",
        "ɵ": "AH",
        "y": "Y UW",
        "ʏ": "UW",
        "ɘ": "EH",
        "œ": "AH",
    }
    consonants = {
        "!": "",
        "ç": "HH",
        "+": "HH",
        "tʃ": "CH",
        "t͡ʃ": "CH",
        "!": "CH",
        "l̩": "AH L",
        "$": "AH L",
        "m̩": "AH M",
        "%": "AH M",
        "n̩": "AH N",
        "&": "AH N",
        "dʒ": "JH",
        "d͡ʒ": "JH",
        '"': "JH",
        "ɾ̃": "N T",
        "#": "N T",
        "ɽ̃": "N AH",
        "¥": "N AH",
        "b": "B",
        "ɓ": "B",
        "ʙ": "B R R",
        "c": "K",
        "ɕ": "HH",
        "d": "D",
        "ð": "DH",
        "ɾ": "T",  # Intervocalic T, D or R?
        "f": "F",
        "ɸ": "F",
        "ɡ": "G",
        "h": "HH",
        "ɦ": "HH",
        "k": "K",
        "l": "L",
        "ɫ": "L",
        "ɬ": "L",
        "ɭ": "L",
        "m": "M",
        "ɱ": "M",
        "n": "N",
        "ŋ": "NG",
        "ɲ": "N Y",
        "p": "P",
        "q": "K",
        "ʔ": "",
        "r": "R",
        "ɹ": "R",
        "ʀ": "R",
        "ʁ": "R",
        "ɽ": "R",
        "ɻ": "R",
        "s": "S",
        "ʃ": "SH",
        "t": "T",
        "ʈ": "T",
        "θ": "TH",
        "v": "V",
        "w": "W",
        "ʍ": "HH W",
        "ɥ": "W",
        "x": "HH",
        "χ": "HH",
        "j": "Y",
        "z": "Z",
        "ʒ": "ZH",
        "ʑ": "HH",
        "\u02de": "R",  # ˞ Modifier letter rhotic hook (rhoticity).
    }
    prosody = {
        "ˈ": "",  # Primary stress.
        "ˌ": "",  # Secondary stress.
        "\u0329": "",  # ̩ Combining vertical line below (secondary stress).
        ".": "",  # Syllable boundary.
        "ˑ": "",  # ˑ Modifier letter half triangular colon (semi-long vowel).
        "ː": "",  # ː Modifier letter triangular colon (long vowel).
        "\u0263": "",  # ˠ Modifier letter small gamma (\u02e0) converts to ɣ Latin small letter gamma (\u0263) after NFKD (velarisation).
        "\u02bc": "",  # ʼ Modifier letter apostrophe.
        "\u02c1": "",  # ˁ Modifier letter reverse glottal stop (pharyngealised).
        "\u02e5": "",  # ˥ Modifier letter extra-high tone bar.
        "\u02e7": "",  # ˧ Modifier letter mid tone bar.
        "\u02e9": "",  # ˩ Modifier letter extra-low tone bar.
        "\u203f": "",  # ‿ Undertie (linking).
        "\u035c": "",  # ͜ Combining double breve below (linking).
        "\u0361": "",  # ͡ Combining double inverted breve (affricate/double articulation).
        "\u032f": "",  # ̯ Combining inverted breve below (non-syllabic).
        "\u030c": "",  # ̌ Combining caron (rising tone).
        "\u031a": "",  # ̚ Combining left angle above (no audible release).
        "\u032a": "",  # ̪ Combining bridge below (dental).
        "\u0308": "",  # ̈ Combining diaresis (centralised).
        "\u032c": "",  # ̬ Combining caron below (voiced).
        "\u0306": "",  # ̆ Combining breve (extra short vowel).
        "\u0320": "",  # ̠ Combining minus sign below (retracted).
        "\u0302": "",  # ̂ Combining circumflex accent (falling tone).
        "\u0330": "",  # ̰ Combining tilde below (creaky voice).
        "\u0304": "",  # ̄ Combining macron (mid tone level).
        "\u031e": "",  # ̞ Combining down tack below (lowered).
        "\u0325": "",  # ̥ Combining ring below (voiceless).
        "\u0319": "",  # ̙ Combining right tack below (retracted tongue root).
        "\u031d": "",  # ̝ Combining up tack below (raised).
        "\u0347": "",  # ͇ Combining equals sign below (alveolar?).
        "\u0301": "",  # ́ Combining acute accent (high tone level).
    }
    punctuation = {
        "'": "",  # Apostrophe (boldface in wiki markup, contractions).
        "-": "",  # Hyphen (abbreviations or affixes).
        ";": ";",
        ",": ";",
        "~": ";",
        "⁓": ";",  # ~ → ⁓ after NFKD.
    }
    mapping = {**vowels, **foreign_vowels, **consonants, **prosody, **punctuation}

    # Preprocess string for digraphs.
    s = digraphAW.sub("0", s)
    s = digraphAY.sub("1", s)
    s = digraphEY.sub("2", s)
    s = digraphOW.sub("3", s)
    s = digraphOY.sub("4", s)
    s = digraphAO.sub("5", s)
    s = digraphCH.sub("!", s)
    s = digraphJH.sub('"', s)
    s = digraphNT.sub("#", s)
    s = digraphNAH.sub("¥", s)
    s = digraphCCedilla.sub("+", s)
    s = digraphSyllabicL.sub("$", s)
    s = digraphSyllabicM.sub("%", s)
    s = digraphSyllabicN.sub("&", s)
    # Preprocess string for syllable markers.
    # TODO: conserve stress marks for later use.
    # s = secondaryStressMark.sub(".", primaryStressMark.sub(".", s))

    # Split along syllable markers: spaces, periods.
    # " ".join(re.split(syllableMarks, s))

    candidates = " ".join(mapping.get(char, char) for char in s).strip()
    return candidates
    # return ";".join(cand for cand in candidates.split(";") if not nonArpa.search(cand))


def makeArpabet():
    with sqlite3.connect(str(DB_PATH.resolve())) as conn:
        results = conn.execute(
            """
                SELECT
                    pageid,
                    title,
                    ipa
                FROM
                    wiktionary
                ;
            """
        )

        for pageid, title, ipa in results:
            conn.execute(
                """
                    UPDATE
                        wiktionary
                    SET
                        arpa = ?
                    WHERE
                        pageid = ?
                    ;
                """,
                (convertIpa(ipa), pageid),
            )
            print(pageid, title, ipa, convertIpa(ipa))


if __name__ == "__main__":
    # alterTable()
    getIpa()
    makeArpabet()
    cleanDb()
