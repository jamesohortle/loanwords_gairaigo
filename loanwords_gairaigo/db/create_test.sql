-- Create database.
-- CREATE DATABASE IF NOT EXISTS test;
PRAGMA ENCODING = "UTF-8";

-- Pre-cleaning.
DROP TABLE IF EXISTS lrec2014;
DROP TABLE IF EXISTS jmdict;
DROP TABLE IF EXISTS wikipedia;
DROP TABLE IF EXISTS unique_tokens;
DROP TABLE IF EXISTS test;

-- LREC2014
-- Bilingual Dictionary Construction with Transliteration Filtering; Richardson, Nakazawa, Kurohashi (2014).
-- http://www.lrec-conf.org/proceedings/lrec2014/pdf/102_Paper.pdf
ATTACH DATABASE '/Users/j-hortle/gairaigo/db/lrec2014.db' AS db_lrec2014;
CREATE TABLE IF NOT EXISTS
   lrec2014(
      confidence REAL,
      english TEXT,
      final TEXT
   );
INSERT INTO
   lrec2014
SELECT
   confidence,
   english,
   japanese
FROM
   db_lrec2014.lrec2014
GROUP BY -- For quick and dirty deduplication.
   english;
-- Deduplicate...
-- Choose highest confidence? Duplicates seem to always have same confidences...
-- Choose first entry? Typically tends to prefer German reading (エネルギー).
DELETE FROM
   lrec2014
WHERE
   confidence NOT IN (
      SELECT
         MAX(confidence)
      FROM
         lrec2014
      GROUP BY
         english
   );
DETACH db_lrec2014;

-- JTCA 外来語（カタカナ）表記ガイドライン 第3版
ATTACH DATABASE '/Users/j-hortle/gairaigo/db/jtca.db' AS db_jtca;
CREATE TABLE IF NOT EXISTS
   jtca (
      english TEXT UNIQUE,
      final TEXT
   );
INSERT INTO
   jtca
SELECT
   english,
   japanese
FROM
   db_jtca.katakana_guide;
-- No need to deduplicate.
DETACH db_jtca;

-- JMdict
ATTACH DATABASE '/Users/j-hortle/gairaigo/db/jmdict.db' AS db_jmdict;
CREATE TABLE IF NOT EXISTS
   jmdict (
      entry_sequence INTEGER UNIQUE,
      english TEXT,
      final TEXT
   );
INSERT INTO
   jmdict
SELECT
   entry_sequence,
   COALESCE(strict_eng, wasei, gloss),
   reading
FROM
   db_jmdict.gairaigo_combined
WHERE
   db_jmdict.gairaigo_combined.ok=1;
-- Deduplicate (not smart, just choose lowest entry_sequence).
DELETE FROM
   jmdict
WHERE
   entry_sequence NOT IN (
      SELECT
         MIN(entry_sequence)
      FROM
         jmdict
      GROUP BY
         english
   );
DETACH db_jmdict;


-- Wikipedia
ATTACH DATABASE '/Users/j-hortle/gairaigo/db/wikipedia.db' AS db_wikipedia;
CREATE TABLE IF NOT EXISTS
   wikipedia(
      pageid INTEGER UNIQUE,
      english TEXT,
      final TEXT
   );
INSERT INTO
   wikipedia
SELECT
   pageid,
   english,
   japanese
FROM
   db_wikipedia.wikipedia;
-- Deduplicate (not smart, just choose lowest pageid).
DELETE FROM
   wikipedia
WHERE
   pageid NOT IN (
      SELECT
         MIN(pageid)
      FROM
         wikipedia
      GROUP BY
         english
   );
DETACH db_wikipedia;



-- Create training data.
CREATE TABLE IF NOT EXISTS
   unique_tokens(
      english TEXT UNIQUE
   );
INSERT INTO
   unique_tokens(
      english
   )
SELECT UPPER(english) FROM lrec2014
UNION
SELECT UPPER(english) FROM jtca
UNION
SELECT UPPER(english) FROM wikipedia
UNION
SELECT UPPER(english) FROM jmdict;

CREATE TABLE IF NOT EXISTS
   test
AS
SELECT 
   unique_tokens.english, -- 365,203 entries
   COALESCE(lrec2014.final, jtca.final, jmdict.final, wikipedia.final) AS final
FROM
   unique_tokens
   LEFT JOIN lrec2014
      ON unique_tokens.english = lrec2014.english COLLATE NOCASE -- 162,963 entries
   LEFT JOIN jtca
      ON unique_tokens.english = jtca.english COLLATE NOCASE -- 762 entries
   LEFT JOIN jmdict
      ON unique_tokens.english = jmdict.english COLLATE NOCASE -- 25,557 entries
   LEFT JOIN wikipedia
      ON unique_tokens.english = wikipedia.english COLLATE NOCASE;-- 203,374 entries

-- Remove bad entries (0 of them!).
-- SELECT COUNT(*) FROM
--    test
-- WHERE
DELETE FROM
   test
WHERE
   english IS NULL
   OR
   final IS NULL
   OR
   english LIKE ''
   OR
   final LIKE '';

-- Leave only training data.
DROP TABLE IF EXISTS lrec2014;
DROP TABLE IF EXISTS jtca;
DROP TABLE IF EXISTS jmdict;
DROP TABLE IF EXISTS wikipedia;
DROP TABLE IF EXISTS unique_tokens;

-- Should be left with
-- 392656 total entries - 36,180 duplicates
-- = 365,476 final entries.