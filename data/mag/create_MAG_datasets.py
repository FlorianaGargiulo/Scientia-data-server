# we use Python typing
from calendar import c
from pathlib import Path
from sys import path
from typing import Dict
# csv to read incoming file
import csv
# to cast the string date
from datetime import datetime
# system utils for file management
import os
import ndjson
import json
import json_stream
import time

# the important part: Scientia Data Model classes
from api.model import Affiliation, Author, Journal, Paper, PaperDataSet


def transform_doc(doc: Dict, authors_index: Dict[str, Author], journals_index: Dict[str, Journal]) -> Dict:
    # this method takes CSV doc into Scientia ready dict
    translated_keys = {
        "Abstract": "abstract",
        "publicationDate": "date"

    }
    # simply copy as is compatible data fields
    paper_doc = {}
    for k, v in doc.items():
        # general cleaning
        k = k.strip()
        v = v.strip().strip('"') if isinstance(v, str) else v
        # AUTHORS
        if k == "authors":
            paper_doc["authors"] = []
            for author_id in v:
                if str(author_id) in authors_index:
                    paper_doc["authors"].append(authors_index[str(author_id)])
                else:
                    paper_doc["authors"].append({'id': str(v)})
        # JOURNAL
        elif k == "appearsinJournal":
            if v in journals_index:
                paper_doc["journal"] = journals_index[v]
            else:
                paper_doc["journal"] = {"id": v}
        # KEEP EVERYTHING ELSE
        else:
            paper_doc[k if not k in translated_keys else translated_keys[k]] = v

    return paper_doc


def mag_papers(corpus_path: Path):
    # this methods create an iterator from the CSV lines and tries to cast the line into a Scientia Paper
    print("indexing authors")
    authors_index = index_authors(corpus_path)
    print(f'{len(authors_index)} authors indexed')
    print('indexing Journals')
    journals_index = index_journals(corpus_path)
    print(f'{len(journals_index)} journals indexed')
    filepath = os.path.join(os.path.dirname(__file__), corpus_path, "papers.json")
    with open(filepath, 'r', encoding='utf8') as doc_f:
        line = 0
        for doc in json_stream.load(doc_f):
            line += 1
            # first do the transformation
            paper = transform_doc(doc, authors_index, journals_index)
            try:
                # run data validation
                # return paper one by one to avoid memory overflow with huge files
                yield Paper.parse_obj(paper)
            except ValueError as e:
                # validation errors are printed in the console but don't block the complete process
                print(e.json())
                print(f"invalid document line {line} file {filepath}")
    del(authors_index)
    del(journals_index)


def index_affiliations(corpus_path: Path) -> Dict[str, Affiliation]:
    with open(os.path.join(corpus_path, "affiliations.json"), "r") as f:
        affiliations = json.load(f)
        aff_index: Dict[str, Affiliation] = {}
        for aff in affiliations:
            affiliation = Affiliation(id=aff['affiliation_id'], name=aff["name"])
            if 'homepage' in aff:
                affiliation.homepage = aff['homepage']
            if 'grid' in aff:
                affiliation.grid = aff['grid']
            aff_index[affiliation.id] = affiliation
        return aff_index


def index_journals(corpus_path: str) -> Dict[str, Journal]:
    with open(os.path.join(corpus_path, "journals.csv"), "r") as f:
        journals = csv.DictReader(f)
        index: Dict[str, Journal] = {}
        for j in journals:
            journal = Journal(id=j['journalId'], name=j["name"], ISSN=j['issn'] if 'issn' in j else None)
            index[journal.id] = journal
        return index


def index_authors(corpus_path: Path) -> Dict[str, Author]:

    affiliations_index = index_affiliations(corpus_path)

    with open(os.path.join(corpus_path, "authorId_name_affiliation.csv"), "r") as f:
        authors = csv.DictReader(f)
        index: Dict[str, Author] = {}
        for a in authors:
            author = Author(id=a['authorId'], fullname=a["name"], affilition=affiliations_index[a['affiliation']] if a['affiliation'] in affiliations_index else None, queryLevel=a['queryLevel'])
            index[author.id] = author
        del(affiliations_index)
        return index


def create_mag_corpus(path: str, corpus: str):
    # generic function to create a corpus from arxiv CSV file

    # create the NDJSON file
    filepath = os.path.join(os.path.dirname(__file__), f"{corpus}.ndjson")
    with open(filepath, 'w', encoding='utf8') as output_f:
        start = time.time()
        nb_buffer_written = 0
        buffer_size = 10000
        buffer = []
        # write paper one by one into the NDJson format
        for paper in mag_papers(path):
            # we use the data model json function to create the right serialization
            buffer.append(f'{paper.json(exclude_none=True)}\n')
            if len(buffer) >= buffer_size:
                nb_buffer_written += 1
                output_f.writelines(buffer)
                end = time.time()
                print(f"written buffer {nb_buffer_written}, {nb_buffer_written*buffer_size} papers in total ({buffer_size/(end - start)}doc/s)")
                start = time.time()
                buffer = []
                break
        # flush buffer
        nb_paper = (nb_buffer_written) * buffer_size + len(buffer)
        output_f.writelines(buffer)
        end = time.time()
        print(f"written buffer {nb_buffer_written}, {nb_paper} papers in total ({len(buffer)/(end - start)}doc/s)")

    # create the dataset config file
    # this config file points to the data file and contains the mandatory corpus metadata
    # it will also be used to store indexation reports
    config: PaperDataSet = PaperDataSet(corpus=corpus, source="microsoft_academic_graph", papers_filepath=f"{corpus}.ndjson", nb_paper=nb_paper)
    with open(f"{corpus}_corpus.json", "w", encoding="utf8") as f:
        f.write(config.json(exclude_none=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    create_mag_corpus("sociology", "sociology")
