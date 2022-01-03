#!python
from elasticsearch import Elasticsearch, helpers
import csv
import ast
import json
from itertools import groupby
import os

from .config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT
DELETE_INDEX = True


def index_corpus(corpus, data_iterator, specific_mapping=None, specific_settings=None):

    # TODO: handle generic/specific corpus

    print("Starting data indexation")
    es = Elasticsearch('%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT))

    for index in [corpus]:
        if es.indices.exists(index=index) and DELETE_INDEX:
            print('index %s deleted' % index)
            es.indices.delete(index=index)
        if not es.indices.exists(index=index):
            es.indices.create(index=index)
            es.indices.close(index=index)

    if specific_settings:
        es.indices.put_settings(index=corpus, body=specific_settings)

    if specific_mapping:
        es.indices.put_mapping(index=corpus,
                               body=specific_mapping)

    for index in [corpus]:
        es.indices.open(index=index)

    # index batch to ES
    index_result, _ = helpers.bulk(es, ({
        "_op_type": "update",
        "doc_as_upsert": True,
        "_id": f"{corpus}_{doc['id']}" % doc,
        'doc': doc}
        for doc in data_iterator),
        index=corpus)
    if index_result > 0:
        return("%s documents inserted" % (index_result))
