from csearch.helpers.bm25_helper import BM25Helper
from math import floor


class JSON2Training:
    def __init__(self, json_data: dict, dataset_split: dict):
        self.json_data = json_data
        self.__index_split = self.__split_chronologically(dataset_split)

        self.__raw_agent_corpus = self.__build_raw_agent_corpus()

        self.__bm25_helper = None

        self.__training_set = {
            'train': [],
            'dev': [],
            'test': [],
        }
        self.__dialog_lookup_table = {
            'train': [],
            'dev': [],
            'test': []
        }

    @classmethod
    def __is_valid_dialogue(cls, dialogue) -> bool:
        """
        Checks whether a dialogue is valid to be added in the training set
        Rules:
        - There should be at least 1 turn
        - The dialogue should be grounded (at least one agent response should contain a link)
        :param dialogue:
        :return:
        """
        utterances = dialogue['utterances']
        user_utterances = list(
            filter(
                lambda utterance: utterance['actor_type'] == 'user', utterances
            )
        )

        # Discard conversations with just 1 turn
        if len(user_utterances) <= 1:
            return False

        agent_utterances = list(
            filter(
                lambda utterance: utterance['actor_type'] == 'agent', utterances
            )
        )

        # Check if at least one agent utterance is grounded (contains link)
        for agent_utterance in agent_utterances:
            if 'href' in agent_utterance['utterance']:
                return True

        return False

    def __build_bm25_helper(self, allocation: str, processed_agent_corpus: dict = None) -> BM25Helper:
        if processed_agent_corpus is None:
            return BM25Helper(allocation, self.__raw_agent_corpus[allocation])

        return BM25Helper(allocation, self.__raw_agent_corpus[allocation], processed_agent_corpus[allocation])

    def __build_raw_agent_corpus(self) -> dict:
        """
        Builds the agent corpus, which is used to generate additional dialogues using BM25
        :return:
        """
        current_dataset_allocation = 'train'
        corpus = {
            'train': [],
            'dev': [],
            'test': [],
        }

        for (key, dialogue) in self.json_data.items():
            if key == self.__index_split['dev_start_index']:
                current_dataset_allocation = 'dev'
            elif key == self.__index_split['test_start_index']:
                current_dataset_allocation = 'test'

            corpus[current_dataset_allocation] += (self.__process_agent_responses(dialogue))

        return corpus

    @classmethod
    def __process_agent_responses(cls, dialogue: dict) -> list:
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

    def __process_dialogue(self, allocation: str, key: str, dialogue: dict) -> None:
        """
        Given an entire dialogue, this function creates all the possible context-response entries
        :param allocation: The dataset to which the dialogue is allocated
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
            self.__dialog_lookup_table[allocation].append(key)
            self.__training_set[allocation].append(training_entry)

            negative_training_entry = ([0] + training_entry[1:len(training_entry) - 1])
            top_responses = self.__bm25_helper.get_top_responses(true_answer, 10)

            # First response is always identical to the true_answer
            del(top_responses[0])

            for top_response in top_responses:
                self.__dialog_lookup_table[allocation].append(int(key))
                self.__training_set[allocation].append(negative_training_entry + [top_response])

    def __split_chronologically(self, dataset_split: dict) -> dict:
        """
        Given a train/dev/test distribution, this function returns the indexes of the chronological split. The
        resulting split can deviate from the proposed percentages in case the index falls between dialogs occuring
        at the same time
        NOTE: The dataset is assumed to be already ordered, as the previous processes take care of that
        :param dataset_split: Should be a dict in the form
        {
            'train': 0.8,
            'dev': 0.1,
            'test': 0.1
        }
        :return:
        """
        dataset_length = len(self.json_data)
        dev_start_index = int(dataset_split['train'] * dataset_length)

        while (self.json_data[str(dev_start_index)]['dialog_time']
               == self.json_data[str(dev_start_index + 1)]['dialog_time']):
            dev_start_index += 1

        test_start_index = dev_start_index + int(dataset_split['dev'] * dataset_length)
        while (self.json_data[str(test_start_index)]['dialog_time']
               == self.json_data[str(test_start_index + 1)]['dialog_time']):
            test_start_index += 1

        return {
            'dev_start_index': str(dev_start_index),
            'test_start_index': str(test_start_index),
        }

    def get_index_split(self) -> dict:
        return self.__index_split

    def get_dialog_lookup_table(self) -> dict:
        return self.__dialog_lookup_table

    def get_processed_corpus(self) -> dict:
        return {
            'train': self.__bm25_helper['train'].processed_corpus,
            'dev': self.__bm25_helper['dev'].processed_corpus
        }

    def convert(self) -> dict:
        """
        Converts all the dialogues contained in a json structure into a list of (label, context, response) triples
        :return:
        """
        current_dataset_allocation = 'train'
        self.__bm25_helper = self.__build_bm25_helper(current_dataset_allocation)
        dataset_size = len(self.json_data.keys())
        progress_increment = floor(dataset_size / 100)

        print('Converting the json to training set')
        for (key, dialogue) in self.json_data.items():
            if int(key) % progress_increment == 0:
                print('Progress: ' + str(floor(int(key) / progress_increment)) + '%')

            if key == self.__index_split['dev_start_index']:
                current_dataset_allocation = 'dev'
                self.__bm25_helper = self.__build_bm25_helper(current_dataset_allocation)
            elif key == self.__index_split['test_start_index']:
                current_dataset_allocation = 'test'
                self.__bm25_helper = self.__build_bm25_helper(current_dataset_allocation)

            if self.__is_valid_dialogue(dialogue):
                self.__process_dialogue(current_dataset_allocation, key, dialogue)

        return self.__training_set
