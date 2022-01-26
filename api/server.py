
from datetime import datetime
import json
from flask import Flask
from flask import request, abort
from elasticsearch import Elasticsearch
from pydantic.types import Json
from api.model import IndexationReport, PaperDataSet
from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT
from index_data_in_ES import index_corpus
from validate_data import validate_iter_paper
import os
app = Flask(__name__)


@app.route('/ping')
def ping():
    return 'pong'


@app.route('/search')
def search(method='GET'):
    # params
    search_body = request.data

    es = Elasticsearch('%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT))

    results = es.search(search_body)

    return results


@app.route('/import-paper-dataset')
def index_papers_dataset(method='GET'):
    # params
    # try:
    paper_dataset_filepath = request.args.get('filepath')
    reset = request.args.get('reset-source-index') != None

    if paper_dataset_filepath and os.path.exists(paper_dataset_filepath):
        # transform relative path to data to absolute
        with open(paper_dataset_filepath, 'r', encoding='utf8') as f:
            config = json.load(f)
            config = PaperDataSet.parse_obj(config | {"basePath": os.path.dirname(
                paper_dataset_filepath)})
            app.logger.info(
                f'indexing {config.papers_filepath} into {config.corpus}')
            nb_document_inserted = 0
            validation_errors: list[Json] = []
            try:
                nb_document_inserted = index_corpus(config.source,
                                                    config.corpus, validate_iter_paper(config.papers_filepath, validation_errors), reset)
            except Exception as e:
                app.logger.error(
                    f"indexation crashed with Exception {type(e)} {e=}")
                validation_errors.append(str(e))

            report = IndexationReport(date=datetime.now(), nb_document_inserted=nb_document_inserted,
                                      validation_errors=validation_errors if len(validation_errors) > 0 else None)
            app.logger.info(report.json(exclude_none=True))
            config.indexation_reports = [report] if not config.indexation_reports else [
                *config.indexation_reports, report]
        with open(paper_dataset_filepath, 'w', encoding='utf8') as f:
            # write reports to file
            f.write(config.json(exclude_none=True, indent=2))
        return report.json(exclude_none=True)
    else:
        abort(404)
    # except Exception as e:
    #     print(e)
    #     abort(500)
