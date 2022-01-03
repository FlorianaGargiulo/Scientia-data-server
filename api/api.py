from os import abort
from flask import Flask
from flask import request, Response
from elasticsearch import Elasticsearch, helpers, exceptions
from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT
import importlib
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
    module = request.args.get('module')
    method = request.args.get('method', 'index')
    if module:
        index_module = importlib.import_module(module)
        return getattr(index_module, method)()
    else:
        abort(404)
