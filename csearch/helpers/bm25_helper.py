import numpy as np
import spacy
from gensim.summarization.bm25 import BM25
from math import floor


class BM25Helper:
    def __init__(self, allocation: str, raw_corpus: list, processed_corpus: list = None):
        self.__pipeline = spacy.load('en_core_web_sm', disable=["parser", "tagger", "ner"])
        self.__allocation = allocation
        self.raw_corpus = raw_corpus
        self.processed_corpus = self.__pre_process_corpus() if processed_corpus is None else processed_corpus
        self.raw_corpus = np.array(self.raw_corpus)
        self.model = BM25(self.processed_corpus)

    def __bm25_pre_process_utterance(self, query: str) -> list:
        doc = self.__pipeline(query)
        return [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]

    def __pre_process_corpus(self) -> list:
        processed_corpus = []

        print('Pre-processing the ' + self.__allocation + ' agent corpus in order to apply BM25...')

        corpus_size = len(self.raw_corpus)
        progress_increment = floor(corpus_size / 100)
        i = 0

        for doc in self.__pipeline.pipe(self.raw_corpus):
            if i % progress_increment == 0:
                print('Progress: ' + str(floor(i / progress_increment)) + '%')

            processed_corpus.append([token.text.lower() for token in doc if not token.is_stop and not token.is_punct])
            i += 1

        return processed_corpus

    def get_top_responses(self, query: str,  n: int) -> list:
        processed_query = self.__bm25_pre_process_utterance(query)

        scores = np.array(self.model.get_scores(processed_query))
        top_indexes = np.argpartition(scores, -n)[-n:]

        return self.raw_corpus[top_indexes[np.argsort(scores[top_indexes])[::-1]]].tolist()