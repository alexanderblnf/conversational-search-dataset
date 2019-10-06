import csv
from csearch.helpers.bm25_helper import BM25Helper
from statistics import mean
import scipy.stats as ss
from tqdm import tqdm
import math
import copy

def load_corpus(filename: str):
    filereader = csv.reader(open(filename, 'r'), delimiter='\t')
    data = [row for row in filereader]
    test_context_corpus = []
    last_context = '.'.join(data[0][1:-1])
    test_context_corpus.append(last_context)

    for index, conversation in enumerate(data):
        current_context = '.'.join(conversation[1:-1])

        if conversation[0] == '1' and index > 0 and current_context != last_context:
            test_context_corpus.append(current_context)
            last_context = copy.deepcopy(current_context)

    return data, test_context_corpus


if __name__ == '__main__':
    # _, train_context_corpus = load_corpus('stackexchange_dump/data_train_easy.tsv')
    # _, dev_context_corpus = load_corpus('stackexchange_dump/data_dev_easy.tsv')
    # data, test_context_corpus = load_corpus('stackexchange_dump/data_test_easy.tsv')
    _, train_context_corpus = load_corpus('stackexchange_dump/mantis_web/data_test_easy_corrected.tsv')
    # responses = [conversation[-1] for conversation in data]
    # index_offset = len(train_context_corpus + dev_context_corpus)
    # helper = BM25Helper(train_context_corpus + dev_context_corpus + test_context_corpus)

    all_ranks = []
    responses = []
    true_docs_per_group = []
    current_true_responses = []
    current_negative_responses = []

    helper = BM25Helper(train_context_corpus)
    del train_context_corpus
    test_data, test_context_corpus = load_corpus('stackexchange_dump/mantis_web/data_test_easy_corrected.tsv')
    last_context = '.'.join(test_data[0][1:-1])

    for index, conversation in enumerate(test_data):
        current_context = '.'.join(conversation[1:-1])

        if conversation[0] == '1' and index > 0 and current_context != last_context:
            responses.append(current_true_responses + current_negative_responses[0:(10 - len(current_true_responses))])
            true_docs_per_group.append(len(current_true_responses))
            current_true_responses = []
            current_negative_responses = []
            last_context = copy.deepcopy(current_context)

        if conversation[0] == '1':
            current_true_responses.append(conversation[-1])
        else:
            current_negative_responses.append(conversation[-1])

    with tqdm(total=len(responses)) as pbar:
        for i, grouped_responses in enumerate(responses):
            scores = []
            for response in grouped_responses:
                preprocessed_response = helper.bm25_pre_process_utterance(response)
                scores.append(-helper.model.get_score(preprocessed_response, i))
            true_docs_ranks = ss.rankdata(scores)[0:true_docs_per_group[i]]
            true_docs_ranks.sort()
            all_ranks.append(true_docs_ranks)
            pbar.update(1)

    aps = []
    ndcgs = []
    for ranks in all_ranks:
        aps.append(mean([(i + 1) / entry for i, entry in enumerate(ranks)]))
        dcg = sum([1 / math.log(entry + 1, 2) for entry in ranks])
        ideal_dcg = sum([1 / math.log(entry + 2, 2) for entry in range(len(ranks))])
        ndcgs.append(dcg / ideal_dcg)

    # mrr = (1 / len(ranks)) * sum([1/rank for rank in ranks])
    # cg_10 = [1 / math.log(rank + 1, 2) if rank <= 10 else 0 for rank in ranks]
    # ndcg_10 = (1 / len(ranks)) * sum(cg_10)
    print('MAP: ' + str(mean(aps)))
    print('NDCG: ' + str(mean(ndcgs)))



