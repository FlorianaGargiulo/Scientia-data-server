
from flask import Flask
from flask import request, Response, abort
from elasticsearch import Elasticsearch, helpers, exceptions
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


@app.route('/index')
def index(method='GET'):
    # params
    # try:
    filepath = request.args.get('filepath')
    corpus = request.args.get('corpus')
    print(f'indexing {filepath} into {corpus}')
    if filepath and os.path.exists(filepath):
        results = index_corpus(corpus, validate_iter_paper(filepath))
        return results
    else:
        abort(404)
    # except Exception as e:
    #     print(e)
    #     abort(500)
