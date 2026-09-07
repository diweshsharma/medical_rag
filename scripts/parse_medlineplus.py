"""
parse_medlineplus.py

Parses the MedlinePlus Health Topic XML file into clean, per-topic
JSONL records ready for chunking + embedding in the RAG pipeline.

Extracts: id, title, url, meta_desc, language, date_created,
also_called (synonyms), see_references, mesh_terms, groups,
primary_institute, full_summary (HTML stripped to plain text).

Deliberately skips <site>, <related-topic>, <language-mapped-topic>,
and <other-language> — these are outbound links / cross-references,
not content, and aren't needed for retrieval.

Usage:
    python parse_medlineplus.py --input data/raw/mplus_topics.xml --output data/processed/mplus_topics.jsonl
"""

import argparse
import json
import re
from pathlib import Path

from lxml import etree
from bs4 import BeautifulSoup
from tqdm import tqdm


def clean_html(raw_html: str) -> str:
    """Strip HTML tags from full-summary text and normalize whitespace."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_topic(elem) -> dict:
    """Extract structured fields from a single <health-topic> element."""
    topic_id = elem.get("id")
    title = elem.get("title")
    url = elem.get("url")
    meta_desc = elem.get("meta-desc")
    language = elem.get("language")
    date_created = elem.get("date-created")

    full_summary = ""
    also_called = []
    see_references = []
    mesh_terms = []
    groups = []
    primary_institute = None

    for child in elem:
        tag = etree.QName(child).localname

        if tag == "full-summary":
            # full-summary contains inline HTML (<p>, <ul>, <a>, etc.)
            raw = child.text or ""
            raw += "".join(etree.tostring(c, encoding="unicode") for c in child)
            full_summary = clean_html(raw)

        elif tag == "also-called":
            if child.text:
                also_called.append(child.text.strip())

        elif tag == "see-reference":
            if child.text:
                see_references.append(child.text.strip())

        elif tag == "mesh-heading":
            descriptor = child.find("descriptor")
            if descriptor is not None and descriptor.text:
                mesh_terms.append({
                    "id": descriptor.get("id"),
                    "term": descriptor.text.strip(),
                })

        elif tag == "group":
            groups.append({
                "id": child.get("id"),
                "url": child.get("url"),
                "name": (child.text or "").strip(),
            })

        elif tag == "primary-institute":
            primary_institute = (child.text or "").strip()

        # <site>, <related-topic>, <language-mapped-topic>,
        # <other-language> intentionally skipped — not content.

    return {
        "id": topic_id,
        "title": title,
        "url": url,
        "meta_desc": meta_desc,
        "language": language,
        "date_created": date_created,
        "also_called": also_called,
        "see_references": see_references,
        "mesh_terms": mesh_terms,
        "groups": groups,
        "primary_institute": primary_institute,
        "full_summary": full_summary,
    }


def parse_medlineplus_xml(input_path: str, output_path: str, english_only: bool = True) -> dict:
    """
    Stream-parse the MedlinePlus XML and write one JSON record per line.
    Uses iterparse so the whole 29MB tree is never held in memory at once.
    Returns counts for a quick sanity check after the run.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped_no_summary = 0
    skipped_language = 0

    context = etree.iterparse(input_path, events=("end",), tag="health-topic")

    with open(output_path, "w", encoding="utf-8") as out_f:
        for event, elem in tqdm(context, desc="Parsing topics"):
            if english_only and elem.get("language") != "English":
                skipped_language += 1
            else:
                record = extract_topic(elem)
                if record["full_summary"]:
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    written += 1
                else:
                    skipped_no_summary += 1

            # free memory: clear this element and drop preceding siblings
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

    return {
        "written": written,
        "skipped_no_summary": skipped_no_summary,
        "skipped_language": skipped_language,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse MedlinePlus health topic XML into JSONL.")
    parser.add_argument("--input", default="data/raw/mplus_topics.xml", help="Path to raw MedlinePlus XML file")
    parser.add_argument("--output", default="data/processed/mplus_topics.jsonl", help="Path to write parsed JSONL")
    parser.add_argument("--include-spanish", action="store_true", help="Keep Spanish-language topics too (default: English only)")
    args = parser.parse_args()

    stats = parse_medlineplus_xml(args.input, args.output, english_only=not args.include_spanish)

    print(f"\nDone.")
    print(f"  Written:              {stats['written']}")
    print(f"  Skipped (no summary): {stats['skipped_no_summary']}")
    print(f"  Skipped (language):   {stats['skipped_language']}")
    print(f"  Output: {args.output}")