from langchain_core import documents
import logfire
import json
import argparse
import os

from langchain_core.documents import Document

def build_page_content(record: dict) -> str:
    """
    combine title , synonyms , and summary into one retriveal text block
    """
    with logfire.span("Parsing the JSon to document"):
        try:
            parts = [record["title"]]

            if record.get("also_called"):
                parts.append("Also called: " + ",".join(record["also_called"]))

            parts.append(record["full_summary"])

            return "\n\n".join(p for p in parts if p)
        except Exception as e:
            logfire.error("Failed to parse the document",error=e,record=record)
            return ""


def build_metadata(record: dict) -> dict:
    """ pull out fileds needed for filtering and citation sources later"""

    with logfire.span("Building metadata"):
        try:
            return{
                "id": record.get("id"),
                "title" : record.get("title"),
                "meta_desc": record.get("meta_decs"),
                "also_called": record.get("also_called")
            }
        except Exception as e:
            logfire.error("Failed to build metadata",error=e,record=record)
            return {}


def load_documnet(file_path : str) -> list[Document]:
    """
    load json file and return list of document 
    
    """
    loaded_docs = []
    with logfire.span("Loading JSON file"):
        try:
            with open(file_path, 'r', encoding = "utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)

                    doc = Document(
                        page_content = build_page_content(record),
                        metadata = build_metadata(record)
                    )
                    loaded_docs.append(doc)

        except Exception as e:
            logfire.error("Failed to load document",error=e,file_path=file_path)
        return loaded_docs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Load MedMentions",
        description="Load MedMentions dataset from JSONL file into Langchain Documents"
    )
    parser.add_argument("--input_file",required=True,help="Path to JSONL file")
    parser.add_argument("--output_file",required=True,help="Path to save the output file")

    args = parser.parse_args()

    logfire.configure()

    docs = load_documnet(args.input_file)

    os.makedirs(os.path.dirname(os.path.abspath(args.output_file)), exist_ok=True)
    with open(args.output_file, 'w', encoding = "utf-8") as f:
        json.dump(
            [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs],
            f, ensure_ascii=False, indent=2,
        )

    logfire.info("Successfully loaded documents", count=len(docs), file_path=args.input_file, output_file=args.output_file) 