# Scientia Data Server

## Define corpus

## Import data

To import data including large amount of data, the system needs a _data set folder_ to be uploaded in the `data` folder.
A _data set folder_ is a set of files which contains data from a common source and the necessary script to import it.

one data set folder by corpus contains:

- data files (any format)
- one import python script which uses standard python lib to import the data set
- an optional elasticSearch mapping file for the corpus index

A standard python library has been developed to standardize and ease the import data script.

## data model

### generic data model

- corpus
- id_in_corpus
- title
- authors: string[]
- abstract
- date

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
