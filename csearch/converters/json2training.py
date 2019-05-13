from csearch.helpers.bm25_helper import BM25Helper
from math import floor


class JSON2Training:
    def __init__(self, json_data: dict, build=True):
        self.json_data = json_data
        self.raw_agent_corpus = None
        self.bm25_helper = None

        if build:
            self.raw_agent_corpus = self.build_raw_agent_corpus()
            self.bm25_helper = self.build_bm25_helper()

        self.training_set = []
        self.dialog_lookup_table = []

    def build_bm25_helper(self) -> BM25Helper:
        """
        Build the bm25 helper, that will be used to perform negative sampling
        :return:
        """
        return BM25Helper(self.raw_agent_corpus)

    def build_raw_agent_corpus(self) -> list:
        """
        Builds the agent corpus, which is used to generate additional dialogues using BM25
        :return:
        """
        corpus = []

        for (key, dialogue) in self.json_data.items():
            corpus += (self.process_agent_responses(dialogue))

        return corpus

    @classmethod
    def process_agent_responses(cls, dialogue: dict) -> list:
        """
        For a given dialogue, generates a list of pre-processed agent responses (ready for BM25)
        :param dialogue:
        :return:
        """
        utterances = dialogue['utterances']
        agent_utterances = list(
            filter(
                lambda utterance: utterance['actor_type'] == 'agent', utterances
            )
        )

        return [utterance['utterance'] for utterance in agent_utterances]

    def process_dialogue(self, key: str, dialogue: dict) -> None:
        """
        Given an entire dialogue, this function creates all the possible context-response entries
        :param key:
        :param dialogue:
        :return:
        """
        utterances = dialogue['utterances']
        user_utterances = list(
            filter(
                lambda utterance: utterance['actor_type'] == 'user', utterances
            )
        )

        # Discard smallest context (with just 1 turn)
        del(user_utterances[0])

        for user_utterance in user_utterances:
            current_pos = user_utterance['utterance_pos']

            if current_pos == len(utterances):
                break

            first_utterance_pos = max(1, current_pos - 10)
            training_entry = ([1] + [utterance['utterance'] for utterance in utterances
                                     if first_utterance_pos <= utterance['utterance_pos'] <= current_pos + 1])
            true_answer = training_entry[-1]

            self.dialog_lookup_table.append(key)
            self.training_set.append(training_entry)

            negative_training_entry = ([0] + training_entry[1:len(training_entry) - 1])
            top_responses = self.bm25_helper.get_negative_samples(true_answer, 51)

            index_to_delete = 0
            if true_answer in top_responses:
                index_to_delete = top_responses.index(true_answer)

            del(top_responses[index_to_delete])

            for top_response in top_responses:
                self.dialog_lookup_table.append(int(key))
                self.training_set.append(negative_training_entry + [top_response])

    def get_dialog_lookup_table(self) -> list:
        return self.dialog_lookup_table

    def convert(self) -> list:
        """
        Converts all the dialogues contained in a json structure into a list of (label, context, response) triples
        :return:
        """
        dataset_size = len(self.json_data.keys())
        progress_increment = floor(dataset_size / 100)

        print('Converting the json to training set')
        for (key, dialogue) in self.json_data.items():
            if int(key) % progress_increment == 0:
                print('Progress: ' + str(floor(int(key) / progress_increment)) + '%')

                self.process_dialogue(key, dialogue)

        return self.training_set


class Json2EasyTraining(JSON2Training):
    """
    Class to help build the "easy" training task, which creates 10 negative samples for each query, taking
    samples only from the same domain as the original query
    """
    def __init__(self, json_data: dict):
        super().__init__(json_data, False)
        self.raw_agent_corpus = self.build_raw_agent_corpus()
        self.bm25_helper = self.build_bm25_helper()

    def build_raw_agent_corpus(self) -> dict:
        corpus = {}

        for (key, dialogue) in self.json_data.items():
            topic = dialogue['category']
            if topic not in corpus:
                corpus[topic] = []

            corpus[topic] += (JSON2Training.process_agent_responses(dialogue))

        return corpus

    def build_bm25_helper(self) -> dict:
        bm25_helper = {}

        for topic, entry in self.raw_agent_corpus.items():
            print('Building BM25 corpus for topic: ' + topic)
            bm25_helper[topic] = BM25Helper(entry)

        return bm25_helper

    def process_dialogue(self, key: str, dialogue: dict):
        utterances = dialogue['utterances']
        topic = dialogue['category']
        user_utterances = list(
            filter(
                lambda utterance: utterance['actor_type'] == 'user', utterances
            )
        )

        # Discard smallest context (with just 1 turn)
        del (user_utterances[0])

        for user_utterance in user_utterances:
            current_pos = user_utterance['utterance_pos']

            if current_pos == len(utterances):
                break

            first_utterance_pos = max(1, current_pos - 10)
            training_entry = ([1] + [utterance['utterance'] for utterance in utterances
                                     if first_utterance_pos <= utterance['utterance_pos'] <= current_pos + 1])
            true_answer = training_entry[-1]

            self.dialog_lookup_table.append(key)
            self.training_set.append(training_entry)

            negative_training_entry = ([0] + training_entry[1:len(training_entry) - 1])
            top_responses = self.bm25_helper[topic].get_negative_samples(true_answer, 11)

            index_to_delete = 0
            if true_answer in top_responses:
                index_to_delete = top_responses.index(true_answer)

            del (top_responses[index_to_delete])

            for top_response in top_responses:
                self.dialog_lookup_table.append(int(key))
                self.training_set.append(negative_training_entry + [top_response])
