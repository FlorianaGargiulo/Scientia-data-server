
from datetime import datetime
import json
from flask import Flask, current_app
from flask import request, abort
from elasticsearch import Elasticsearch, helpers
from pydantic.types import Json
from api.model import Citation, IndexationReport, Paper, PaperDataSet
from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT
from index_data_in_ES import index_citations, index_papers
from validate_data import iter_citations, validate_iter_paper
import os
import networkx as nx
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
    skip_paper = request.args.get('skip-papers') != None

    # report variables
    nb_document_inserted = 0
    nb_citations_inserted = 0
    validation_errors: list[Json] = []

    if paper_dataset_filepath and os.path.exists(paper_dataset_filepath):
        # transform relative path to data to absolute
        with open(paper_dataset_filepath, 'r', encoding='utf8') as f:
            config = json.load(f)
            config = PaperDataSet.parse_obj(config | {"basePath": os.path.dirname(
                paper_dataset_filepath)})

            # papers
            if not skip_paper:
                app.logger.info(
                    f'indexing {config.papers_filepath} into {config.corpus}')

                try:
                    nb_document_inserted = index_papers(config.source,
                                                        config.corpus, validate_iter_paper(config.papers_filepath, validation_errors), reset)
                except Exception as e:
                    app.logger.error(
                        f"indexation crashed with Exception {type(e)} {e=}")
                    validation_errors.append(str(e))
            # citations
            if config.citations_filepath:
                # try:
                nb_citations_inserted = index_citations(config.source, config.corpus, iter_citations(config.citations_filepath))
                # except Exception as e:
                #     app.logger.error(
                #         f"indexation crashed with Exception {type(e)} {e=}")
                #     validation_errors.append(str(e))

            report = IndexationReport(date=datetime.now(), nb_document_inserted=nb_document_inserted, nb_citations_inserted=nb_citations_inserted,
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

# Create a network
# - network type : citation, coreference
# - search query
# - nb_paper_limit
# rational:
# get the list of paper through search up to the limit
# get their links
# compute the network
# in case of citation : should we drop target not in the first list? Option to include targets only over a degree threshold? up or in the limit ?
# in case of coreference : targets are used as links?

# TODO: move this in model as utils for CSV?
# TODO: add field selection as input


def format_node_for_network(obj: dict):
    paper = Paper.from_elasticsearch(obj)
    date = {"date": paper.date.text} if paper.date else {}
    authors = {"authors": ", ".join((a.fullname for a in paper.authors))} if paper.authors else {}
    return paper.dict(exclude_none=True) | authors | date


def generate_citations_network(search_body):
    es = Elasticsearch('%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT))
    network = nx.DiGraph()
    # retrieve papers
    papers = []

    network.add_nodes_from((result['_id'], format_node_for_network(result['_source'])) for result in helpers.scan(es, search_body))
    # retrieve citations
    # TODO: terms list is limited to 65k we must check that limit
    citations_query = {"query": {
        "bool": {
            "filter": {
                "terms": {"citing": list(network.nodes())}
            }, }}}
    for citation in helpers.scan(es, citations_query):
        if citation['_source']['cited'] in network:
            network.add_edge(citation['_source']['citing'], citation['_source']['cited'])
    return nx.generate_gexf(network)


@app.route('/citations_network.gexf')
def citations_network_gexf(method='GET'):
    # params
    size = request.args.get('size', 1000)
    source = request.args.get('source', None)
    search_body = json.loads(request.data)
    current_app.logger.debug(search_body)
    search_body['size'] = size
    search_body['_source'] = ['_id', 'title', 'authors', 'date']

    return app.response_class(generate_citations_network(search_body), mimetype='text/xml')
