from index_data_in_ES import index_corpus
from validate_data import validate_iter_paper

# ewitch to proper test suite


def test_datafile_validation():
    valid = 0
    invalid = 0
    for paper in validate_iter_paper("../data/arxiv/Automata theory.csv.ndjson"):
        if paper:
            valid += 1
        else:
            invalid += 1
    print(f'parsed {valid} valid and {invalid} invalid')

# print(index_corpus(corpus, validate_iter_paper(filepath)))


if __name__ == "__main__":
    test_datafile_validation()
