import stanfordnlp
import numpy as np
from spacy_stanfordnlp import StanfordNLPLanguage
from gensim.summarization.bm25 import BM25


class BM25Helper:
    def __init__(self, allocation: str, raw_corpus: list = None, processed_corpus: list = None):
        if raw_corpus is None and processed_corpus is None:
            raise Exception('Please specify one of raw_corpus or processed_corpus')

        stanford_pipeline = stanfordnlp.Pipeline(lang='en')
        self.__pipeline = StanfordNLPLanguage(stanford_pipeline)

        self.__allocation = allocation
        self.raw_corpus = [] if raw_corpus is None else raw_corpus
        self.processed_corpus = self.__pre_process_corpus() if processed_corpus is None else processed_corpus
        self.model = BM25(self.processed_corpus)

    def __bm25_pre_process_utterance(self, query: str) -> list:
        doc = self.__pipeline(query)
        return [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]

    def __pre_process_corpus(self) -> list:
        processed_corpus = []

        print('Pre-processing the' + self.__allocation + ' agent corpus in order to apply BM25...')

        for utterance in self.raw_corpus:
            processed_corpus.append(self.__bm25_pre_process_utterance(utterance))

        return processed_corpus

    def get_top_responses(self, query: str,  n: int) -> list:
        processed_query = self.__bm25_pre_process_utterance(query)

        scores = self.model.get_scores(processed_query)
        top_indexes = np.argpartition(np.array(scores), -n)[-n:]

        return self.raw_corpus[top_indexes]


