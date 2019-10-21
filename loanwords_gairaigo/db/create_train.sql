-- Create database.
-- CREATE DATABASE IF NOT EXISTS training;
PRAGMA ENCODING = "UTF-8";

-- Pre-cleaning.
DROP TABLE IF EXISTS britfone;
DROP TABLE IF EXISTS cmudict;
DROP TABLE IF EXISTS wiktionary;
DROP TABLE IF EXISTS unique_tokens;
DROP TABLE IF EXISTS train;

-- Britfone
ATTACH DATABASE '/Users/j-hortle/gairaigo/db/britfone.db' AS db_britfone;
CREATE TABLE IF NOT EXISTS
   britfone (
      english TEXT UNIQUE,
      prekana TEXT,
      final TEXT
   );
INSERT INTO
   britfone
SELECT
   english,
   prekana,
   final
FROM
   db_britfone.hand_mapping;
DETACH db_britfone;

-- CMUdict
ATTACH DATABASE '/Users/j-hortle/gairaigo/db/cmudict.db' AS db_cmudict;
CREATE TABLE IF NOT EXISTS
   cmudict(
      english TEXT UNIQUE,
      prekana TEXT,
      final TEXT
   );
INSERT INTO
   cmudict
SELECT
   english,
   prekana,
   final
FROM
   db_cmudict.hand_mapping;
DETACH db_cmudict;

-- Wiktionary
ATTACH DATABASE '/Users/j-hortle/gairaigo/db/wiktionary.db' AS db_wiktionary;
CREATE TABLE IF NOT EXISTS
   wiktionary(
      pageid INTEGER UNIQUE,
      english TEXT,
      prekana TEXT,
      final TEXT
   );
INSERT INTO
   wiktionary
SELECT
   pageid,
   title,
   prekana,
   final
FROM
   db_wiktionary.wiktionary;
-- Deduplicate (not smart, just choose lowest pageid).
DELETE FROM
   wiktionary
WHERE
   pageid NOT IN (
      SELECT
         MIN(pageid)
      FROM
         wiktionary
      GROUP BY
         english
   );
DETACH db_wiktionary;

-- Create training data.
CREATE TABLE IF NOT EXISTS
   unique_tokens(
      english TEXT UNIQUE
   );
INSERT INTO
   unique_tokens(
      english
   )
SELECT english FROM britfone
UNION
SELECT english FROM cmudict
UNION
SELECT UPPER(english) FROM wiktionary;

CREATE TABLE IF NOT EXISTS
   train
AS
SELECT 
   unique_tokens.english, -- 161,520 entries
   COALESCE(britfone.prekana, cmudict.prekana, wiktionary.prekana) AS prekana,
   COALESCE(britfone.final, cmudict.final, wiktionary.final) AS final
FROM
   unique_tokens
   LEFT JOIN britfone
      ON unique_tokens.english = britfone.english -- 16,205 entries
   LEFT JOIN cmudict
      ON unique_tokens.english = cmudict.english -- 133,797 entries
   LEFT JOIN wiktionary
      ON unique_tokens.english = wiktionary.english COLLATE NOCASE; -- 52,931 entries

-- Remove bad entries (54 of them).
-- SELECT COUNT(*) FROM
--    train
-- WHERE
DELETE FROM
   train
WHERE
   english IS NULL
   OR
   prekana IS NULL
   OR
   final IS NULL
   OR
   english LIKE ''
   OR
   prekana LIKE ''
   OR
   final LIKE '';

-- Leave only training data.
DROP TABLE IF EXISTS britfone;
DROP TABLE IF EXISTS cmudict;
DROP TABLE IF EXISTS wiktionary;
DROP TABLE IF EXISTS unique_tokens;

-- Should be left with
-- 202,933 total entries - 40,610 duplicates - 54 malformed
-- = 162,269 final entries.