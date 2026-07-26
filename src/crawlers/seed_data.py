"""Offline seed corpus used when remote APIs are unreachable."""

from __future__ import annotations

from typing import Any

BUDDHISM_SEEDS: list[dict[str, Any]] = [
    {
        "tradition": "buddhism",
        "corpus": "Pali Tipitaka seed (public-domain English + Pali excerpt; offline fallback)",
        "uid": "sn56.11",
        "title": "Dhammacakkappavattana Sutta",
        "primary_language": "pli",
        "editions": [
            {
                "language": "pli",
                "author_uid": "seed",
                "title": "Dhammacakkappavattana Sutta",
                "text": (
                    "Idaṃ kho pana, bhikkhave, dukkhaṃ ariyasaccaṃ: "
                    "jātipi dukkhā, jarāpi dukkhā, byādhipi dukkho, maraṇampi dukkhaṃ..."
                ),
                "source": "seed://pali/sn56.11",
            },
            {
                "language": "en",
                "author_uid": "seed",
                "title": "Setting in Motion the Wheel of Dhamma",
                "text": (
                    "Now this, bhikkhus, is the noble truth of suffering: birth is suffering, "
                    "aging is suffering, illness is suffering, death is suffering; union with "
                    "what is displeasing is suffering; separation from what is pleasing is "
                    "suffering; not to get what one wants is suffering; in brief, the five "
                    "aggregates subject to clinging are suffering.\n"
                    "Now this is the noble truth of the origin of suffering: it is this craving "
                    "which leads to renewed existence...\n"
                    "Now this is the noble truth of the cessation of suffering: it is the "
                    "remainderless fading away and cessation of that same craving...\n"
                    "Now this is the noble truth of the way leading to the cessation of "
                    "suffering: it is this Noble Eightfold Path..."
                ),
                "source": "seed://en/sn56.11",
            },
        ],
        "note": "Offline fallback seed for pilot runs when SuttaCentral is unreachable.",
    },
    {
        "tradition": "buddhism",
        "corpus": "Pali Tipitaka seed (offline fallback)",
        "uid": "an3.65",
        "title": "Kesamutti (Kalama) Sutta",
        "primary_language": "en",
        "editions": [
            {
                "language": "en",
                "author_uid": "seed",
                "title": "Kalama Sutta",
                "text": (
                    "Come, Kalamas, do not go by oral tradition, by lineage of teaching, by "
                    "hearsay, by a collection of scriptures, by logical reasoning, by "
                    "inferential reasoning, by reasoned cogitation, by the acceptance of a view "
                    "after pondering it, by the seeming competence of a speaker, or because you "
                    "think: 'The ascetic is our guru.' But when you know for yourselves: 'These "
                    "things are unwholesome; these things are blameworthy; these things are "
                    "censured by the wise; these things, if accepted and undertaken, lead to "
                    "harm and suffering,' then you should abandon them."
                ),
                "source": "seed://en/an3.65",
            }
        ],
        "note": "Offline fallback seed.",
    },
]

ISLAM_SEEDS: list[dict[str, Any]] = [
    {
        "tradition": "islam",
        "corpus": "Qur'an seed (Arabic Uthmani + English; offline fallback)",
        "ref": "1:1-7",
        "name": "Al-Fatihah",
        "surah": 1,
        "from_ayah": 1,
        "to_ayah": 7,
        "primary_language": "ar",
        "text_arabic": (
            "1. بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ\n"
            "2. ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ\n"
            "3. ٱلرَّحْمَٰنِ ٱلرَّحِيمِ\n"
            "4. مَٰلِكِ يَوْمِ ٱلدِّينِ\n"
            "5. إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ\n"
            "6. ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ\n"
            "7. صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ"
        ),
        "text_english": (
            "1. In the name of Allah, the Entirely Merciful, the Especially Merciful.\n"
            "2. All praise is due to Allah, Lord of the worlds.\n"
            "3. The Entirely Merciful, the Especially Merciful.\n"
            "4. Sovereign of the Day of Recompense.\n"
            "5. It is You we worship and You we ask for help.\n"
            "6. Guide us to the straight path.\n"
            "7. The path of those upon whom You have bestowed favor, not of those who have "
            "evoked [Your] anger or of those who are astray."
        ),
        "ayahs": [],
        "note": "Offline fallback seed when AlQuran Cloud is unreachable.",
    },
    {
        "tradition": "islam",
        "corpus": "Qur'an seed (offline fallback)",
        "ref": "112:1-4",
        "name": "Al-Ikhlas",
        "surah": 112,
        "from_ayah": 1,
        "to_ayah": 4,
        "primary_language": "ar",
        "text_arabic": (
            "1. قُلْ هُوَ ٱللَّهُ أَحَدٌ\n"
            "2. ٱللَّهُ ٱلصَّمَدُ\n"
            "3. لَمْ يَلِدْ وَلَمْ يُولَدْ\n"
            "4. وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ"
        ),
        "text_english": (
            "1. Say, He is Allah, [who is] One.\n"
            "2. Allah, the Eternal Refuge.\n"
            "3. He neither begets nor is born.\n"
            "4. Nor is there to Him any equivalent."
        ),
        "ayahs": [],
        "note": "Offline fallback seed.",
    },
    {
        "tradition": "islam",
        "corpus": "Qur'an seed (offline fallback)",
        "ref": "2:255-255",
        "name": "Ayat al-Kursi",
        "surah": 2,
        "from_ayah": 255,
        "to_ayah": 255,
        "primary_language": "ar",
        "text_arabic": (
            "255. ٱللَّهُ لَا إِلَٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ ۚ لَا تَأْخُذُهُۥ سِنَةٌ وَلَا نَوْمٌ ۚ "
            "لَّهُۥ مَا فِى ٱلسَّمَٰوَٰتِ وَمَا فِى ٱلْأَرْضِ"
        ),
        "text_english": (
            "255. Allah - there is no deity except Him, the Ever-Living, the Sustainer of "
            "existence. Neither drowsiness overtakes Him nor sleep. To Him belongs whatever is "
            "in the heavens and whatever is on the earth."
        ),
        "ayahs": [],
        "note": "Offline fallback seed.",
    },
]
