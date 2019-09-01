import csv
from csearch.helpers.bm25_helper import BM25Helper
import scipy.stats as ss
import numpy as np
import math

def load_corpus(filename: str):
    filereader = csv.reader(open(filename, 'r'), delimiter='\t')
    data = [row for row in filereader]
    return data, ['.'.join(conversation[1:-1]) for conversation in data if conversation[0] == '1']

if __name__ == '__main__':
    # _, train_context_corpus = load_corpus('stackexchange_dump/data_train_easy.tsv')
    # _, dev_context_corpus = load_corpus('stackexchange_dump/data_dev_easy.tsv')
    # data, test_context_corpus = load_corpus('stackexchange_dump/data_test_easy.tsv')
    data, test_context_corpus = load_corpus('stackexchange_dump/data_test.tsv')
    # responses = [conversation[-1] for conversation in data]
    # index_offset = len(train_context_corpus + dev_context_corpus)
    # helper = BM25Helper(train_context_corpus + dev_context_corpus + test_context_corpus)

    ranks = []
    responses = []
    current_grouped_responses = []

    helper = BM25Helper(test_context_corpus)
    del test_context_corpus

    for index, conversation in enumerate(data):
        if conversation[0] == '1' and index > 0:
            responses.append(current_grouped_responses)
            current_grouped_responses = []
        current_grouped_responses.append(conversation[-1])

    for i, grouped_responses in enumerate(responses):
        scores = []
        for response in grouped_responses:
            scores.append(helper.model.get_score(response, i))
        ranks.append(ss.rankdata(scores)[0])

    mrr = (1 / len(ranks)) * sum([1/rank for rank in ranks])
    cg_10 = [1 / math.log(rank + 1, 2) if rank <= 10 else 0 for rank in ranks]
    ndcg_10 = (1 / len(ranks)) * sum(cg_10)
    print('MAP: ' + str(mrr))
    print('NDCG: ' + str(ndcg_10))



