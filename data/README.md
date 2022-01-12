# Data folder

/!\ WORK IN PROGRESS

To import data including large amount of data, the system needs a _data set folder_.

one data set folder consists in:

- one Scientia data set config file
- one papers data file
- optional citations data file
- optional elasticSearch settings:
  - mapping
  - analyzers

Format of those files are describe in the [data model specification](../api/model.py).
This model can be used to prepare and validate data.

## Add data to Scientia

To add a corpus to the scientia platform, one must:

- provide compatible data files to the platform
- trigger an indexation

Scientia is based on a data model which describes research papers.
Incoming data must respect this model to be indexed.
On top of specified field, it's possible to add extra field in which case their type will be guess at indexation time. It's not possible to import complex format such as date that way.
It's still possible to enhance scientia data model but this requires modifying an deploying scientia data server source code.

Ways to add data file to the platform depends on the hosting constraints. FTP might be the way to go.

## Build compatible data files

To build a compatible data file, one can use any scripting environment.
This being said, we provide a python environment to ease scientia data model validation and export in ndjson.

We crafted an import script example to [convert arxiv CSV to scientia NDJson](./arxiv_csv_to_ndjson.py).

To run it we must provide arxiv CSV and create the compatible virtual env.

```bash
$ git clone scientiarepo
$ cd scientia-data-server
$ pyenv install 3.10.1
$ pyenv virtualenv 3.10.1 scientia-data-server
$ pyenv activate scientia-data-server
(scientia-data-server)$ pip install -e .
(scientia-data-server)$ cd data/arxiv
(scientia-data-server)$ python arxiv_csv_to_ndjson.py
```

## data model

### Generic part

This set of fields are the common trunk of information shared by all the corpus.

- corpus
- id_in_corpus
- title
- authors: string[]
- abstract
- date
- keywords: string[]

### data model by corpus

## corpus metadata file

## supported format

So far only ndjson (Newline Delimited Json) is supported.
We might add more formats (zip container option, regular JSON...) in future.
CSV is not option as it would require to add parsing logic into the server which is easier to deal upstream in data preparation phase.
