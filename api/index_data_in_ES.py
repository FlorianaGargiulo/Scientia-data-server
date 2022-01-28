#!python
from typing import Iterable
from elasticsearch import Elasticsearch, helpers
import json
from api.model import Citation, Paper
from flask import current_app

from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT


def create_paper_upsert_action(data_iterator: Iterable[Paper], corpus: str):
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


def index_papers(source, corpus, data_iterator: Iterable[Paper], reset=False, specific_mappings=None, specific_settings=None):

    # TODO: handle generic/specific corpus

    current_app.logger.info("Starting papers indexation")
    es = Elasticsearch('%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT))
    index = f'scientia_{source}_papers'
    if es.indices.exists(index=index) and reset:
        current_app.logger.info('index %s deleted' % index)
        es.indices.delete(index=index)
    if not es.indices.exists(index=index):
        with open("es_paper_index_configuration.json", "r", encoding="utf8") as f:
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
    index_result, _ = helpers.bulk(es, create_paper_upsert_action(data_iterator, corpus), index=index)
    if index_result > 0:
        return(index_result)


def create_citation_upsert_action(citation_iterator: Iterable[Citation], corpus: str, index: str):
    counter = 0
    for citation in citation_iterator:
        if counter % 10000 == 0:
            current_app.logger.info(f'indexed {counter} citations')
        yield {
            '_index': index,
            '_id': f"{citation['citing']}-{citation['cited']}"
        } | citation
        counter += 1


def index_citations(source, corpus, citation_iterator: Iterable[Citation], reset=False, specific_mappings=None, specific_settings=None):
    current_app.logger.info("Starting citations indexation")
    es = Elasticsearch('%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT))
    index = f'scientia_{source}_citations'
    if es.indices.exists(index=index) and reset:
        current_app.logger.info('index %s deleted' % index)
        es.indices.delete(index=index)
    if not es.indices.exists(index=index):
        with open("es_citation_index_configuration.json", "r", encoding="utf8") as f:
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
    index_result = 0
    for success, info in helpers.streaming_bulk(es, create_citation_upsert_action(citation_iterator, corpus, index), chunk_size=1000):
        if success:
            index_result += 1
        else:
            current_app.logger.debug(info)
    if index_result > 0:
        return(index_result)
