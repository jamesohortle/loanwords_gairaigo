#!env/bin/python
# -*- coding: utf-8 -*-
"""Use xml.etree.ElementTree to parse the English Wikipedia data and extract the relevant info."""

import re
import sys
import sqlite3
from pathlib import Path

from lxml import etree as ET

import mysql.connector
from mysql.connector import errorcode

WIKI_DB_PATH = Path("../db/wikipedia.db")

useCurr = True
currVer = "0.10"
testVer = "0.3"
ver = currVer if useCurr else testVer
DUMP_ENG = str(Path("../data/enwiki-latest-pages-articles.xml").resolve())
PAGE_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}page"
TITLE_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}title"
REVISION_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}revision"
TEXT_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}text"
ID_TAG = f"{{http://www.mediawiki.org/xml/export-{ver}/}}id"

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


def makeTable():
    with sqlite3.connect(str(WIKI_DB_PATH.resolve())) as conn:
        conn.execute(
            """
            PRAGMA ENCODING=UTF8;
            """
        )
        conn.execute(
            """
                CREATE TABLE IF NOT EXISTS
                    wikipedia (
                        pageid INTEGER UNIQUE,
                        english text,
                        japanese text
                    )
                ;
            """
        )


def getLanglinkIds():
    try:
        cnx = mysql.connector.connect(
            user="root",
            password="",
            database="langlinks_en",
            host="127.0.0.1",
            port=3306,
        )
        cursor = cnx.cursor()
    except mysql.connector.Error as e:
        print("MySQL is not cooperating...")
    else:
        query = """
            SELECT
                ll_from,
                ll_title
            FROM
                langlinks
            WHERE
                (ll_lang = %s)
            ;
        """
        params = (b"ja",)
        cursor.execute(query, params)

        with sqlite3.connect(str(WIKI_DB_PATH.resolve())) as conn:
            conn.execute(
                """
                    PRAGMA ENCODING=UTF8;
                """
            )
            sys.stdout.write("[")
            sys.stdout.flush()
            for pageid, ll_title in cursor:
                pageid, ll_title = int(pageid), removeParentheticals(str(ll_title))
                if ll_title and onlyKat(ll_title):
                    sys.stdout.write(f"({pageid}, {ll_title})")
                    sys.stdout.flush()

                    try:
                        conn.execute(
                            """
                                INSERT INTO
                                    wikipedia (
                                        pageid,
                                        japanese
                                    )
                                VALUES
                                    (?, ?)
                                ;
                            """,
                            (pageid, ll_title),
                        )
                    except sqlite3.IntegrityError:
                        conn.execute(
                            """
                                UPDATE
                                    wikipedia
                                SET
                                    japanese = ?
                                WHERE
                                    ßpageid = ?
                                ;
                            """,
                            (ll_title, pageid),
                        )
                    else:
                        conn.commit()
                else:
                    sys.stdout.write(".")
    finally:
        cursor.close()
        cnx.close()
        sys.stdout.write("]\n")
        sys.stdout.flush()


# Can't use jawiki to enwiki langlinks since page IDs are not unique across
# different Wikis. I.e., each Wiki keeps its own set of page IDs independent
# from other Wikis. Therefore, must scan Wiki...


def getEngTitles():
    with sqlite3.connect(str(WIKI_DB_PATH.resolve())) as conn:
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
                    wikipedia
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

                    sys.stdout.write(f"({pid}, {eng_title})")

                    conn.execute(
                        """
                            UPDATE
                                wikipedia 
                            SET
                                english = ?
                            WHERE
                                pageid = ?
                            ;
                        """,
                        (eng_title, pid),
                    )
                else:
                    sys.stdout.write(".")
                sys.stdout.flush()
            except ET.XMLSyntaxError as e:
                print("Skipping error: ", e)
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
        print("Done with the English dump!")


def cleanDb():
    with sqlite3.connect(str(WIKI_DB_PATH.resolve())) as conn:
        conn.execute(
            """
                DELETE FROM
                    wikipedia
                WHERE
                    japanese LIKE ''
                OR
                    english LIKE ''
                OR
                    japanese IS NULL
                OR
                    english IS NULL
                ;
            """
        )


if __name__ == "__main__":
    makeTable()
    getLanglinkIds()
    getEngTitles()
    cleanDb()
