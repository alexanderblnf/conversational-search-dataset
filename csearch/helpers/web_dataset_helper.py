from csearch.helpers.bm25_helper import BM25Helper


class WebDatasetHelper:
    def __init__(self, url_mapping: dict):
        self.url_mapping = url_mapping

    def __build_raw_web_document_corpus(self, json_data: dict) -> list:
        """
        Builds the agent corpus, which is used to generate additional dialogues using BM25
        :return:
        """
        corpus = []

        for (key, dialogue) in json_data.items():
            corpus += (self.__process_web_documents(dialogue))

        return corpus

    def __build_multi_topic_raw_web_document_corpus(self, json_data: dict) -> dict:
        """
        Builds the web document corpus, which is used to generate additional dialogues using BM25
        :return:
        """
        corpus = {}

        for (key, dialogue) in json_data.items():
            topic = dialogue['category']
            if topic not in corpus:
                corpus[topic] = []

            corpus[topic] += (self.__process_web_documents(dialogue))

        return corpus

    def build_bm25_helper(self, json_data: dict) -> BM25Helper:
        return BM25Helper(self.__build_raw_web_document_corpus(json_data))

    def build_multi_topic_bm25_helper(self, json_data: dict) -> dict:
        bm25_helper = {}
        raw_document_corpus = self.__build_multi_topic_raw_web_document_corpus(json_data)

        for topic, entry in raw_document_corpus.items():
            print('Building BM25 corpus for topic: ' + topic)
            bm25_helper[topic] = BM25Helper(entry)

        return bm25_helper

    def __process_web_documents(self, dialogue: dict) -> list:
        """
        For a given dialogue, generates a list of pre-processed web documents (ready for BM25)
        :param dialogue:
        :return:
        """
        utterances = dialogue['utterances']
        valid_agent_utterances = list(
            filter(
                lambda utterance: self.is_valid_utterance(utterance), utterances
            )
        )

        return [self.url_mapping[url]['text'].replace('\n', '.').replace('\r', '.') for utterance in valid_agent_utterances
                for url in list(filter(lambda url: url in self.url_mapping and len(self.url_mapping[url]['text'].split()) < 5000, utterance['urls']))]

    def is_valid_utterance(self, utterance):
        crawled_urls = list(
            filter(lambda url: url in self.url_mapping, utterance['urls'])
        )

        return utterance['actor_type'] == 'agent' and len(crawled_urls) > 0

