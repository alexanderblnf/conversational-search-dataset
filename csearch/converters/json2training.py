from pandas import DataFrame
import pandas as pd
from csearch.models.agent_utterance import AgentUtterance


class JSON2Training:
    def __init__(self, json_data: dict, dataset_split: dict):
        self.json_data = json_data
        self.__index_split = self.__split_chronologically(dataset_split)
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

        for user_utterance in user_utterances:
            current_pos = user_utterance['utterance_pos']
            if current_pos == len(utterances):
                break

            first_utterance_pos = max(1, current_pos - 10)
            training_entry = ([1] + [utterance['utterance'] for utterance in utterances
                                     if first_utterance_pos <= utterance['utterance_pos'] <= current_pos + 1])

            self.__dialog_lookup_table[allocation].append(key)
            self.__training_set[allocation].append(training_entry)

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

    def convert(self) -> dict:
        """
        Converts all the dialogues contained in a json structure into a list of (label, context, response) triples
        :return:
        """
        current_dataset_allocation = 'train'
        for (key, dialogue) in self.json_data.items():
            if key == self.__index_split['dev_start_index']:
                current_dataset_allocation = 'dev'
            elif key == self.__index_split['test_start_index']:
                current_dataset_allocation = 'test'

            self.__process_dialogue(current_dataset_allocation, key, dialogue)

        return self.__training_set

