import os
from model import Paper
import ndjson
import json


def validate_iter_paper(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf8') as datafile:
            reader = ndjson.reader(datafile)
            line = 0
            for doc in reader:
                line += 1
                try:
                    paper = Paper.validate(doc)
                    yield paper
                except Exception as e:
                    raise e
                except ValueError as e:
                    print(e.json())
                    print(f"invalid document line {line} file {filepath}")
                    pass
    else:
        raise Exception(f"file {filepath} could not be found.")
