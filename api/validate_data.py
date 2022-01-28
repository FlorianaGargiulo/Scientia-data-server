import os

from pydantic.types import Json
from model import Paper
import ndjson
import casanova
from flask import current_app


def validate_iter_paper(filepath, errors_collector: list[Json] = None):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf8') as datafile:
            reader = ndjson.reader(datafile)
            line = 0
            for doc in reader:
                line += 1
                try:
                    paper = Paper.validate(doc)
                    yield paper
                except ValueError as e:
                    if errors_collector is not None:

                        errors_collector.append(
                            f'In {filepath}, line {line}: {str(e)}')
                    current_app.logger.info(
                        f"invalid document line {line} file {filepath} see report for more information")
                    pass
                except Exception as e:
                    raise e
    else:
        raise Exception(f"file {filepath} could not be found.")


def iter_citations(filepath):
    current_app.logger.info([filepath, os.path.exists(filepath)])
    if os.path.exists(filepath):
        with casanova.reader(filepath) as reader:
            citing_pos = reader.headers.citing
            cited_pos = reader.headers.cited
            for citation in reader:
                yield {"citing": citation[citing_pos], "cited": citation[cited_pos]}
    else:
        raise Exception("Citation file can't be found")
