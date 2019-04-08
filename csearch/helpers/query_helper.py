import stanfordnlp
from spacy_stanfordnlp import StanfordNLPLanguage


class QueryHelper:
    def __init__(self):
        stanford_pipeline = stanfordnlp.Pipeline(lang='en')
        self.__pipeline = StanfordNLPLanguage(stanford_pipeline)

    def pre_process_for_bm25(self, query) -> list:
        doc = self.__pipeline(query)
        return [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]
