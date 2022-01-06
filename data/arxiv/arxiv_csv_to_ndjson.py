# we use Python typing
from typing import Dict
# csv to read incoming file
import csv
# to cast the string date
from datetime import datetime
# system utils for file management
import os
import ndjson
import json

# the important part: Scientia Data Model classes
from api.model import Paper, PaperDataSet


def transform_doc(doc: Dict):
    # this method takes CSV doc into Scientia ready dict

    # simply copy as is compatible data fields
    keep_columns_as_is = set(["id", "title", "abstract"])
    new_doc = dict((k, v) for k, v in doc.items() if k in keep_columns_as_is)

    # split multivalue field
    new_doc["keywords"] = doc["categories"].split(";")
    # use the scientia model for author
    new_doc["authors"] = [{"fullname": fullname}
                          for fullname in doc["authors"].split(";") if fullname != ""]
    try:
        # cast the date
        new_doc["date"] = datetime.strptime(
            doc["created"], "%d %B, %Y").date().isoformat()
    except:
        # if no date can be cast date field will be empty
        pass
    return new_doc


def papers_from_csv(filename):
    # this methods create an iterator from the CSV lines and tries to cast the line into a Scientia Paper
    with open(os.path.join(os.path.dirname(__file__), filename), 'r', encoding='utf8') as doc_f:
        docs = csv.DictReader(doc_f)
        line = 0
        for doc in docs:
            line += 1
            # first do the transformation
            paper = transform_doc(doc)
            try:
                # run data validation
                if Paper.validate(paper):
                    # return paper one by one to avoid memory overflow with huge files
                    yield Paper.parse_obj(paper)
            except ValueError as e:
                # validation errors are printed in the console but don't block the complete process
                print(e.json())
                print(f"invalid document line {line} file {filename}")


def automata_theory():
    filepath = 'Automata theory.csv'
    corpus = "automata_theory"
    # generate ndjson file
    create_arxiv_corpus(filepath, corpus)


def nlp():
    create_arxiv_corpus('Natural language processing.csv', "nlp")


def create_arxiv_corpus(filename: str, corpus: str):
    # generic function to create a corpus from arxiv CSV file

    # create the NDJSON file
    with open(os.path.join(os.path.dirname(__file__), filename.replace(".csv", ".ndjson")), 'w', encoding='utf8') as output_f:
        writer = ndjson.writer(
            output_f, ensure_ascii=False)
        # write paper one by one into the NDJson format
        for paper in papers_from_csv(filename):
            writer.writerow(
                # we use the data model json function to create the right serialization
                json.loads(paper.json(exclude_none=True)))

    # create the dataset config file
    # this config file points to the data file and contains the mandatory corpus metadata
    # it will also be used to store indexation reports
    config: PaperDataSet = PaperDataSet(
        corpus=corpus, source="arxiv", papers_filepath=filename.replace('.csv', '.ndjson'))
    with open(f"{corpus}_corpus.json", "w", encoding="utf8") as f:
        f.write(config.json(exclude_none=True, ensure_ascii=False, indent=2))


# when running this file, trigger data transformation for two different corpus from the same arxiv source.
if __name__ == '__main__':
    automata_theory()
    nlp()
