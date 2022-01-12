# Scientia Data Server

## Data store

This server stores and indexes bibliographic data used for the Scientia research project.
Papers are organized by source and by corpus.
Sources are the name of the databases used to retrieve bibliographic data such as arxiv, Pubmed, Microsoft Academic Graph...
Corpus are thematic groups of papers from one source which were retrieved using a common query.

There can be multiple corpus created from the same source.

Data are stored into Elasticsearch using one index by source.
If the same paper is present in different corpus from the same source, it will not be duplicated and its corpus field will list the corpus it was found in.
Paper deduplication is based on the paper source id. There are no deduplication across sources.

Scientia needs the incoming data to respect a data model which is partly generic, partly corpus-specific.
Paper main data fields should be formatted under the Scientia data model (see [the data README](data/README.md]). It's possible to add extra fields not listed in Scientia data model. Extra fields are indexed as string.

## Import Data

To import data, you need to store a Scientia compatible data-set on the server filesystem.
To learn more on the format and how to create such data-set see [the data README](data/README.md).

The import API route is `import-paper-dataset`.
A GET request on this route requires a filepath parameter which must be an absolute filepath to the paper dataset config file.
Importing a data-set add the paper into the ElasticSearch source index (named `scientia_{source}`).
An optional GET parameter `reset-source-index` can be used to reset the source index, i.e. removing all existing documents from this source before importing the file.

Example:

```
http://localhost:5000/import-paper-dataset?filepath=/data/arxiv/nlp_corpus.json&reset-source-index
```

This request returns an indexation report which is also added to the data-set config file.

## Query data

### Search proxy

The API serves a proxy to the search ElasticSearch API.

The `search` route can be used with a GET request with a JSON body containing the query.
The query must follow the [ElasticSearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html).
In this example, we retrieve papers which contain "intelligence" in the automata_theory from the arxiv source (note that the filter on the source is only required if the corpus name might be used in other sources).
The ElasticSearch DSL let you define data aggregations. Here we ask for the main authors for the retrieve papers and counting results by year.

```json
{
  "query": {
    "bool": {
      "must": {
        "simple_query_string": {
          "query": "intelligence"
        }
      },
      "filter": {
        "bool": {
          "must": [
            {
              "term": {
                "_index": "scientia_arxiv"
              }
            },
            {
              "term": {
                "corpus": "automata_theory"
              }
            }
          ]
        }
      }
    }
  },
  "aggregations": {
    "authors": {
      "terms": {
        "field": "authors.fullname.raw"
      }
    },
    "time": {
      "date_histogram": {
        "field": "date.date",
        "interval": "year",
        "format": "YYYY"
      }
    }
  }
}
```

### Specific queries API?

## Explore data

## Tech Stack

- ElasticSearch server
- FTP server to feed data packages
- python script to import data
- python Flask API:
  - trigger data set import
  - trigger data set deletion (?)
  - ES proxy search queries
- Web application for visual exploration
