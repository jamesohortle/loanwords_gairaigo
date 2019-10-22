#!/bin/bash
# Process all the data resources.

# Type 1 resources.
python3 jmdict.py && \
python3 wikipedia.py

# Type 2 resources.
python3 britfone_to_kana.py && \
python3 cmu_to_db.py && \
python3 cmu_to_kana.py && \
python3 wiktionary_to_db.py && \
python3 wiktionary_to_kana.py