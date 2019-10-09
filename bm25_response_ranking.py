import csv
from csearch.helpers.bm25_helper import BM25Helper
from gensim.summarization.bm25 import BM25
import scipy.stats as ss
from tqdm import tqdm
import numpy as np
import math
import itertools as it
from multiprocessing import Pool


def load_corpus(filename: str):
    filereader = csv.reader(open(filename, 'r'), delimiter='\t')
    data = [row for row in filereader]
    return data, ['.'.join(conversation[1:-1]) for conversation in data if conversation[0] == '1']


def get_score_custom(document, index, bm25_model: BM25, k1, b):
    """Computes BM25 score of given `document` in relation to item of corpus selected by `index`.

    Parameters
    ----------
    document : list of str
        Document to be scored.
    index : int
        Index of document in corpus selected to score with `document`.

    Returns
    -------
    float
        BM25 score.

    """
    score = 0
    doc_freqs = bm25_model.doc_freqs[index]
    for word in document:
        if word not in doc_freqs:
            continue
        score += (bm25_model.idf[word] * doc_freqs[word] * (k1 + 1)
                  / (doc_freqs[word] + k1 * (1 - b + b * bm25_model.doc_len[index] / bm25_model.avgdl)))
    return score


def worker(work_num):
    entry = combinations[work_num]
    print('Combination ' + str(work_num + 1) + '/' + str(len(combinations)))
    print(entry)
    for i, grouped_responses in enumerate(responses):
        scores = []
        for response in grouped_responses:
            preprocessed_response = helper.bm25_pre_process_utterance(response)
            k1 = entry['k1']
            b = entry['b']
            score = get_score_custom(preprocessed_response, i, helper.model, k1, b)
            # scores.append(-helper.model.get_score(preprocessed_response, i))
            scores.append(-score)
        ranks.append(ss.rankdata(scores)[0])

    mrr = (1 / len(ranks)) * sum([1 / rank for rank in ranks])
    cg_10 = [1 / math.log(rank + 1, 2) if rank <= 10 else 0 for rank in ranks]
    ndcg_10 = (1 / len(ranks)) * sum(cg_10)
    print('MAP: ' + str(mrr))
    print('NDCG: ' + str(ndcg_10))
    return [work_num, mrr, ndcg_10]


if __name__ == '__main__':
    # _, train_context_corpus = load_corpus('stackexchange_dump/data_train_easy.tsv')
    # _, dev_context_corpus = load_corpus('stackexchange_dump/data_dev_easy.tsv')
    data, test_context_corpus = load_corpus('stackexchange_dump/data_test_easy.tsv')
    # data, test_context_corpus = load_corpus('stackexchange_dump/data_test_easy.tsv')
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
            responses.append(current_grouped_responses[0:10])
            current_grouped_responses = []
        current_grouped_responses.append(conversation[-1])

    del data

    param_grid = {
        # 'k1': [0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7, 1.9, 2.1],
        # 'b': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        'k1': [0.5],
        'b': [0.2],
    }
    all_keys = list(param_grid.keys())
    combinations = [{'k1': entry[0], 'b': entry[1]} for entry in list(it.product(*(param_grid[name] for name in all_keys)))]
    p = Pool(processes=16)
    data = p.map(worker, [i for i in range(len(combinations))])
    p.close()
    np.savetxt('bm25_result.out', data)



