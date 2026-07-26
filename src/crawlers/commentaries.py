"""
Later interpretive works (commentaries / tafsir / shastra) for contrast.

These are curated public-domain / widely cited excerpts used as comparison
anchors against the model's chain-of-thought reading of the primary text.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import RAW_DIR, ensure_data_dirs

COMMENTARIES: dict[str, list[dict[str, Any]]] = {
    "buddhism": [
        {
            "id": "buddhaghosa_satipatthana",
            "author": "Buddhaghosa",
            "work": "Visuddhimagga / Atthakatha tradition (Satipatthana)",
            "era": "5th century CE",
            "aligns_to": ["mn10", "dn22"],
            "text": (
                "In the commentarial tradition associated with Buddhaghosa, satipatthana is "
                "elaborated as a systematic path of purification: mindfulness of body, feeling, "
                "mind, and dhammas is framed within sila–samadhi–pañña, with detailed analysis of "
                "hindrances, aggregates, sense bases, and the Four Noble Truths. The sutta's "
                "concise instructions are expanded into a complete map of insight practice, "
                "emphasizing that right mindfulness is inseparable from ethical restraint and "
                "clear comprehension (sampajañña)."
            ),
            "stance": "systematic Abhidhamma-inflected commentarial expansion",
        },
        {
            "id": "nagarjuna_emptiness",
            "author": "Nagarjuna",
            "work": "Mulamadhyamakakarika (emptiness hermeneutic)",
            "era": "c. 2nd–3rd century CE",
            "aligns_to": ["sn56.11", "an3.65"],
            "text": (
                "Nagarjuna's Madhyamaka reading presses dependent arising toward emptiness "
                "(sunyata): doctrines such as the Four Noble Truths are upheld conventionally "
                "while denying inherent existence (svabhava). Later Mahayana hermeneutics thus "
                "re-read early teaching not as affirming substantial realities, but as skillful "
                "means that dissolve clinging to views—including clinging to 'Buddhist' views."
            ),
            "stance": "Madhyamaka deconstructive re-reading",
        },
    ],
    "christianity": [
        {
            "id": "augustine_genesis",
            "author": "Augustine of Hippo",
            "work": "De Genesi ad litteram / Confessions (creation hermeneutic)",
            "era": "4th–5th century CE",
            "aligns_to": ["Genesis 1:1-5", "John 1:1-18"],
            "text": (
                "Augustine insists that Genesis must be read in ways that do not contradict "
                "demonstrated truth, distinguishing literal and figurative senses. Creation by "
                "the Word is coordinated with the Johannine Logos: 'In the beginning' is not "
                "merely temporal succession but the eternal Word through whom all things are made. "
                "Light and darkness become both cosmic and spiritual categories—illumination of "
                "the intellect ordered to God."
            ),
            "stance": "patristic multi-sense exegesis",
        },
        {
            "id": "aquinas_romans",
            "author": "Thomas Aquinas",
            "work": "Super Epistolam ad Romanos / Summa Theologiae",
            "era": "13th century CE",
            "aligns_to": ["Romans 3:21-26", "Matthew 5:1-12"],
            "text": (
                "Aquinas reads justification in Romans through the categories of grace, faith "
                "formed by charity, and the justice of God revealed apart from the Law yet "
                "fulfilling the Law's end. The righteousness of God is both God's own justice and "
                "the justice whereby God makes the sinner just. Later scholastic commentary thus "
                "systematizes Paul's dense soteriology into metaphysical and moral theology."
            ),
            "stance": "scholastic systematic theology",
        },
        {
            "id": "calvin_psalm23",
            "author": "John Calvin",
            "work": "Commentary on the Psalms",
            "era": "16th century CE",
            "aligns_to": ["Psalm 23"],
            "text": (
                "Calvin treats Psalm 23 as a confession of providence: the shepherd image "
                "assures the believer of God's particular care amid want and death's shadow. "
                "Reformation commentary stresses personal trust and the sufficiency of God's "
                "word and care over ritual security, reading the psalm devotionally and "
                "ecclesially as comfort for the persecuted church."
            ),
            "stance": "Reformation pastoral-theological commentary",
        },
    ],
    "islam": [
        {
            "id": "tabari_fatihah",
            "author": "al-Tabari",
            "work": "Jami' al-Bayan (Tafsir al-Tabari)",
            "era": "9th–10th century CE",
            "aligns_to": ["1:1-7"],
            "text": (
                "Al-Tabari compiles early exegetical reports on Al-Fatihah: debates on whether "
                "the basmala is a verse of the surah, the meanings of al-Rahman/al-Rahim, "
                "sirat al-mustaqim as the path of those favored (often identified with prophets "
                "and the righteous), and the contrast with those who incur anger or go astray. "
                "Classical tafsir here privileges transmitted athar alongside linguistic analysis."
            ),
            "stance": "classical encyclopedic tafsir (riwaya + diraya)",
        },
        {
            "id": "ibn_kathir_kursi",
            "author": "Ibn Kathir",
            "work": "Tafsir al-Qur'an al-Azim",
            "era": "14th century CE",
            "aligns_to": ["2:255-255", "112:1-4"],
            "text": (
                "Ibn Kathir's treatment of Ayat al-Kursi emphasizes tawhid and divine attributes: "
                "Allah's living, self-subsisting nature, ownership of heavens and earth, and the "
                "limits of intercession. On Al-Ikhlas he stresses absolute oneness and the "
                "negation of lineage, partnership, and likeness—using hadith that equate the "
                "surah's reward with one-third of the Qur'an to highlight creedal centrality."
            ),
            "stance": "hadith-forward Sunni tafsir",
        },
        {
            "id": "razī_light",
            "author": "Fakhr al-Din al-Razi",
            "work": "Mafatih al-Ghayb (Tafsir al-Kabir)",
            "era": "12th–13th century CE",
            "aligns_to": ["24:35-35"],
            "text": (
                "Al-Razi's philosophical-theological tafsir unfolds the Light Verse through "
                "layered metaphors: God as light of heavens and earth; niche, lamp, glass, "
                "blessed tree, and oil as graded symbols of intellect, prophecy, and guidance. "
                "Later kalam-philosophical commentary thus moves beyond lexical sense into "
                "metaphysics of illumination and epistemology of guidance."
            ),
            "stance": "philosophical-kalam esoteric-exoteric synthesis",
        },
    ],
}


def load_commentaries(tradition: str | None = None) -> dict[str, list[dict[str, Any]]]:
    ensure_data_dirs()
    selected = COMMENTARIES if tradition is None else {tradition: COMMENTARIES[tradition]}
    for trad, items in selected.items():
        out = RAW_DIR / trad / "commentaries.json"
        out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return selected


def commentaries_for(tradition: str, scripture_key: str) -> list[dict[str, Any]]:
    items = COMMENTARIES.get(tradition, [])
    key = scripture_key.lower()
    matched = []
    for item in items:
        for align in item.get("aligns_to", []):
            if align.lower() in key or key in align.lower():
                matched.append(item)
                break
    return matched or items[:1]
