

from collections import defaultdict
import itertools
from elasticsearch import Elasticsearch, helpers
from flask import current_app
import networkx as nx

from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT
from api.model import Paper


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


def generate_coreferences_network(search_body):
    es = Elasticsearch('%s:%s' % (ELASTICSEARCH_HOST, ELASTICSEARCH_PORT))
    network = nx.Graph()
    # retrieve papers
    papers = []

    network.add_nodes_from((result['_id'], format_node_for_network(result['_source'])) for result in helpers.scan(es, search_body))
    # retrieve references
    # TODO: terms list is limited to 65k we must check that limit
    citations_query = {
        "query": {
            "bool": {
                "filter": {
                    "terms": {"cited.raw": list(network.nodes())}
                },
            }
        }
    }
    coref_clicks = defaultdict(set)
    for citation in helpers.scan(es, citations_query, preserve_order=True):
        coref_clicks[citation['_source']['citing']].add(citation['_source']['cited'])
    for coref, paper_ids in coref_clicks.items():
        if len(paper_ids) > 0:
            edges = ((source, target, 1 + network[source][target].get("weight", 0) if network.has_edge(source, target) else 1) for source, target in itertools.combinations(paper_ids, 2))
            network.add_weighted_edges_from(edges)
    return nx.generate_gexf(network)
