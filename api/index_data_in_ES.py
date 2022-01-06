#!python
from typing import Iterable
from elasticsearch import Elasticsearch, helpers
import json
from api.model import Paper
from flask import current_app

from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT
DELETE_INDEX = True


def index_corpus(corpus, data_iterator: Iterable[Paper], specific_mappings=None, specific_settings=None):

    # TODO: handle generic/specific corpus

    current_app.logger.info("Starting data indexation")
    es = Elasticsearch('%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT))
    index = f'scientia_{corpus}'
    if es.indices.exists(index=index) and DELETE_INDEX:
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
    index_result, _ = helpers.bulk(es, ({
        "_op_type": "update",
        "doc_as_upsert": True,
        "_id": f"{corpus}_{paper.id}",
        'doc': paper.to_elasticsearch()}
        for paper in data_iterator),
        index=index)
    if index_result > 0:
        return(index_result)
