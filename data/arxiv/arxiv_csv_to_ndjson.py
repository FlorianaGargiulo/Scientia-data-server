from logging import debug
from typing import Dict
import csv
from datetime import datetime
import os
import ndjson
import json
from api.model import Paper


def transform_doc(doc: Dict):
    keep_columns_as_is = set(["id", "title", "abstract"])
    new_doc = dict((k, v) for k, v in doc.items() if k in keep_columns_as_is)
    new_doc["keywords"] = doc["categories"].split(";")
    new_doc["authors"] = [{"fullname": fullname}
                          for fullname in doc["authors"].split(";") if fullname != ""]
    try:
        new_doc["date"] = datetime.strptime(
            doc["created"], "%d %B, %Y").date().isoformat()
    except:
        pass
    return new_doc


def papers_from_csv(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), 'r', encoding='utf8') as doc_f:
        docs = csv.DictReader(doc_f)
        line = 0
        for doc in docs:
            line += 1
            paper = transform_doc(doc)
            try:
                if Paper.validate(paper):
                    yield Paper.parse_obj(paper)
            except ValueError as e:
                print(e.json())
                print(f"invalid document line {line} file {filename}")


def automata_theory():
    return _csv_to_json('Automata theory.csv', "automata_theory")


def nlp():
    return _csv_to_json('Natural language processing.csv', "nlp")


def _csv_to_json(filename, corpus):
    with open(os.path.join(os.path.dirname(__file__), filename+".ndjson"), 'w', encoding='utf8') as output_f:
        writer = ndjson.writer(
            output_f, ensure_ascii=False)
        for doc in papers_from_csv(filename):
            writer.writerow(
                json.loads(doc.json(exclude_none=True)))


if __name__ == '__main__':
    automata_theory()
    nlp()
