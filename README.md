# Loanwords 外来語

In modern Japanese, a vast array of loanwords are employed in everyday life. These words are commonly written in *katakana*, one of the three primary scripts used to write Japanese. Although some words such as コーヒー *kōhī,* and パン *pan* are from sources other than English (Dutch *koffie* and Portuguese *pão*, respectively), the majority of loanwords in use today are derived from English. In addition to calques from English, there are also terms and phrases that have been coined by the Japanese using English roots; these are known as 和製英語 *wasei eigo* ("English made in Japan") and typically do not translate directly: e.g., メールマガジン *mēru magajin* ("mail magazine") for an e-mail newsletter.

This repository contains primarily some Python scripts for scraping various resources in order to create a set of (primarily English) loanwords in Japanese and some SQL scripts to merge the data. At the moment, there are 221,587 English-Japanese vocabulary pairs.

This serves two main purposes:

1. As a resource for learners and researchers of Japanese who wish to study the phonetic changes that occur for (English) calques in Japanese and as a reference for vocabulary study.
2. As a resource for data science and machine learning practitioners who may wish to improve their systems (e.g., by allowing speech synthesis technologies to handle English text embedded in Japanese sentences).

On a personal note, the code here was developed primarily with the second purpose in mind and is being released in the interest of goodwill towards the community of researchers and practitioners who have made it possible.

## Resources リソース

This project makes use of the following resources.

- Dumps from Wikipedia ([EN](https://en.wikipedia.org/wiki/), [JA](https://ja.wikipedia.org/wiki))
- Dumps from Wiktionary ([EN](https://en.wiktionary.org/wiki), [JA](https://ja.wiktionary.org/wiki))
- The [Japanese-Multilingual dictionary (JMdict)](http://www.edrdg.org/jmdict/edict_doc.html#IREF03)
- The [CMU pronouncing dictionary (CMUdict)](http://www.speech.cs.cmu.edu/cgi-bin/cmudict)
- Jose Llarena's [Britfone repository](https://github.com/JoseLlarena/Britfone).
- The data created for the research paper [*Richardson J, Nakazawa T, Kurohashi S. Bilingual Dictionary Construction with Transliteration Filtering. In: Proceedings of the Ninth International Conference on Language Resources and Evaluation (LREC'14) (2014)*](http://www.lrec-conf.org/proceedings/lrec2014/index.html)
- The Japan Technical Communicators Association's (JTCA) publication [外来語（カタカナ）表記ガイドライン 第3版 (2015)](https://www.jtca.org/standardization/katakana_guide_3_20171222.pdf)

The resources above can be divided into two types: those that provide an English-katakana mapping and those that provide an English-phonetic mapping.

Resources of the first type (Wikipedia, JMdict, LREC'14, JTCA) remain largely unmodified. Some basic tricks are employed to align source and target words, but katakana are otherwise unchanged.

Resources of the second type (Wiktionary, CMUdict, Britfone) are heavily processed in order to systematically transform phonetic and surface forms into more or less natural katakana.

## Systematic mappings from English to katakana フロム英語、ツーカタカナのシステマティックなマッピング

One may wish to imagine that English words are transcribed perfectly phonetically into katakana. Alas, the unfortunate truth is that this is often not the case. Phenomena such as the introduction of loanwords when Japanese and/or English phonology was different, misreadings or misinterpretations of the English source words or precedence given to the written form of the English word over its pronunciation have led to cases such as モンキー *monkī* for English "monkey", which would be phonetically transcribed more accurately as マンキー *mankī*.

Therefore, we begin by transcribing phonetically and then correct these transcriptions based on some common graphemes. For example, English words starting with `MO` that have been transcribed as `マ` are corrected to `モ` (except for words beginning in `MOTHER`).

## Deciding on canonical mappings カノニカルなマッピングをジャッジ

Another complicating factor is the presence of multiple transcription systems and therefore transcriptions for a single English term. Some systems employ ウィ and ウェ to transcribe *wi* and *we*, while others may prefer ウイ or ウエ. Similarly, newer transcriptions allows ヴ *vu* to represent the voiced labiodental fricative *v* which does not exist in Japanese (it is still pronounced like a *b*) or combinations like クィ *kwi* or スィ *swi* for words like "queen" or "sweets".

We let the data speak for themselves and accept mappings based on the reliability of the resource.

For resources of type one, we choose the ordering `LREC'14 > JTCA > JMdict > Wikipedia`. Firstly, both Wikipedia and JMdict are open source, however JMdict with its etymology and *wasei* tags allow us to make better guesses as to the correct alignments. Furthermore, while Wikipedia gives us a large resource it is relatively low quality, suffering from inconsistent transcriptions and nicknames, etc. The relative ordering of LREC'14 and JTCA is debatable: LREC'14 provides many good scientific and technical vocabulary but is only backed by three authors and many English-katakana pairs collapse to a single item after normalization, while JTCA provides far fewer vocabulary items but is endorsed by an industry association.

For resources of type two, we choose the ordering `Britfone > CMUdict > Wiktionary`. Wiktionary's transcriptions were so volatile and low-quality that, despite the large number of terms it contributed, it may be worth dropping the resource altogether. Both Britfone and CMUdict provide high-quality, canonical transcriptions for Britsh and American English (received pronunciation (RP) and general American (GA), respectively). However, RP is typically the model for the import of loanwords and so transcriptions from RP tend to be better. In more recent years, however, loandwords from GA have seen a rise, but this is unlikely to overtake the large bulk of RP-based terms that already exist in Japanese in the near future.

After extracting transcriptions from resources of both types, we then merge them to create the final dataset. In this final merge, we prefer type one to type two. The full ordering is then `LREC'14 > JTCA > JMdict > Wikipedia > Britfone > CMUdict > Wiktionary`.

Aside from this, there remain English homonyms like "wind", which could be ウィンド *windo* or ワインド *waindo*. We do not deal with this and simply list whichever transcription appears first in the ordering.

## Licence ライセンス

TBD
