#!python
from typing import Iterable
from elasticsearch import Elasticsearch, helpers
import json
from api.model import Paper
from flask import current_app

from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT


def create_upsert_action(data_iterator: Iterable[Paper], corpus: str):
    counter = 0
    for paper in data_iterator:
        if counter % 10000 == 0:
            current_app.logger.info(f'indexed {counter} papers')
        yield {
            "_op_type": "update",
            '_id': paper.id,
            'upsert': paper.to_elasticsearch() | {"corpus": [corpus]},
            'script': {
                "source": """
                    if (!ctx._source.corpus.contains(params.corpus))
                        ctx._source.corpus.add(params.corpus)
                """.replace('\n', ' '),
                "lang": "painless",
                "params": {
                    "corpus": corpus
                }
            }, }
        counter += 1


def index_corpus(source, corpus, data_iterator: Iterable[Paper], reset=False, specific_mappings=None, specific_settings=None):

    # TODO: handle generic/specific corpus

    current_app.logger.info("Starting data indexation")
    es = Elasticsearch('%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT))
    index = f'scientia_{source}'
    if es.indices.exists(index=index) and reset:
        current_app.logger.info('index %s deleted' % index)
        es.indices.delete(index=index)
    if not es.indices.exists(index=index):
        with open("es_index_configuration.json", "r", encoding="utf8") as f:
            index_config = json.load(f)
            if specific_settings:
                index_config["settings"] = index_config["settings"] | specific_settings
            if specific_mappings:
                index_config["mappings"] = index_config["mappings"] | specific_mappings
            es.indices.create(
                index=index, body=index_config)
            es.indices.close(index=index)

    es.indices.open(index=index)

    # index batch to ES
    index_result, _ = helpers.bulk(es, create_upsert_action(data_iterator, corpus), index=index)
    if index_result > 0:
        return(index_result)
