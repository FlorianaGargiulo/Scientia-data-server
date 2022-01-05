# Scientia Data Server

## Define corpus

## Import data

To import data including large amount of data, the system needs a _data set folder_ to be uploaded in the `data` folder.
A _data set folder_ is a set of files which contains data from a common source and some settings about the source data format.

one data set folder by corpus contains:

- data files respecting the Scientia data structure specification
- optional elasticSearch settings:
  - mapping
  - analyzers

## Data model

Scientia needs the incoming data to respect a data model which is partly generic, partly corpus-specific.

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

## Query data

### ElasticSearch proxy

### Specific queries API?

## Tech Stack

- ElasticSearch server
- FTP server to feed data packages
- python script to import data
- python Flask API:
  - trigger data set import
  - trigger data set deletion (?)
  - ES proxy search queries
- Web application for visual exploration
