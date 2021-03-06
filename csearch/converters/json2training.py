from csearch.helpers.bm25_helper import BM25Helper
from csearch.helpers.file_helper import FileHelper
from math import floor
from tqdm import tqdm

class JSON2Training:
    def __init__(self, json_data: dict, bm25_helper, file_helper: FileHelper):
        self.json_data = json_data
        self.bm25_helper = bm25_helper
        self.training_set = []
        self.dialog_lookup_table = []
        self.file_helper = file_helper

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

            self.dialog_lookup_table.append(int(key))
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

    def write_and_clear_training(self):
        self.file_helper.write_tsv('.tsv', self.training_set, append=True)
        self.training_set = []
        self.file_helper.write_array('_lookup.txt', self.dialog_lookup_table, append=True)
        self.dialog_lookup_table = []

    def convert_and_write(self) -> None:
        """
        Converts all the dialogues contained in a json structure into a list of (label, context, response) triples
        :return:
        """
        dataset_size = len(self.json_data.keys())
        progress_increment = floor(dataset_size / 100)

        print('Converting the json to training set')
        with tqdm(total=len(self.json_data)) as pbar:
            for (key, dialogue) in self.json_data.items():
                if len(self.json_data) < 30000 or int(key) > 40459:
                    if int(key) % progress_increment == 0:
                        self.write_and_clear_training()

                    self.process_dialogue(key, dialogue)
                pbar.update(1)

        self.write_and_clear_training()


class Json2EasyTraining(JSON2Training):
    """
    Class to help build the "easy" training task, which creates 10 negative samples for each query, taking
    samples only from the same domain as the original query
    """
    def __init__(self, json_data: dict, bm_25_helper):
        super().__init__(json_data, bm_25_helper)
        self.bm25_helper = bm_25_helper

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

            self.dialog_lookup_table.append(int(key))
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


class WebJson2Training(JSON2Training):
    def __init__(self, json_data: dict, url_mapping: dict, bm_25_helper, file_helper):
        super().__init__(json_data, bm_25_helper, file_helper)
        self.bm25_helper = bm_25_helper
        self.url_mapping = url_mapping

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
                                     if first_utterance_pos <= utterance['utterance_pos'] <= current_pos])

            # current_pos starts index from 1 instead of 0
            true_answer_urls = list(filter(lambda url: url in self.url_mapping, utterances[current_pos]['urls']))

            if not true_answer_urls:
                continue

            true_documents = [self.url_mapping[url]['text'].replace('\n', '.').replace('\r', '.') for url in true_answer_urls]
            negative_samples = []

            for true_document in true_documents:
                negative_samples += self.process_url(training_entry, true_documents, negative_samples, key, true_document)

    def process_url(self, training_entry: list, true_documents: list, negative_samples: list, key: str, true_document: str) -> list:
        url_training_entry = training_entry + [true_document]

        self.dialog_lookup_table.append(int(key))
        self.training_set.append(url_training_entry)

        negative_training_entry = ([0] + training_entry[1:])
        top_responses = self.bm25_helper.get_negative_samples(true_document, 50 + len(true_documents),
                                                              existing_negative_samples=negative_samples)

        top_responses_without_true_documents = list(
            filter(lambda response: response not in true_documents, top_responses)
        )

        top_responses_without_true_documents = top_responses_without_true_documents[0:50]

        for top_response in top_responses_without_true_documents:
            self.dialog_lookup_table.append(int(key))
            self.training_set.append(negative_training_entry + [top_response])

        return top_responses_without_true_documents


class WebJson2EasyTraining(JSON2Training):
    def __init__(self, json_data: dict, url_mapping:dict, bm_25_helper, file_helper):
        super().__init__(json_data, bm_25_helper, file_helper)
        self.bm25_helper = bm_25_helper
        self.url_mapping = url_mapping

    def process_dialogue(self, key: str, dialogue: dict) -> None:
        """
        Given an entire dialogue, this function creates all the possible context-response entries
        :param key:
        :param dialogue:
        :return:
        """
        utterances = dialogue['utterances']
        topic = dialogue['category']
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
                                     if first_utterance_pos <= utterance['utterance_pos'] <= current_pos])

            # current_pos starts index from 1 instead of 0
            true_answer_urls = list(filter(lambda url: url in self.url_mapping, utterances[current_pos]['urls']))

            if not true_answer_urls:
                continue

            true_documents = [self.url_mapping[url]['text'].replace('\n', '.').replace('\r', '.') for url in true_answer_urls]

            for true_document in true_documents:
                self.process_url(training_entry, true_documents, topic, key, true_document)

    def process_url(self, training_entry: list, true_documents: list, topic: str, key: str, true_document: str) -> None:
        url_training_entry = training_entry + [true_document]

        self.dialog_lookup_table.append(int(key))
        self.training_set.append(url_training_entry)

        negative_training_entry = ([0] + training_entry[1:])
        top_responses = self.bm25_helper[topic].get_negative_samples(true_document, 10 + len(true_documents))

        top_responses_without_true_documents = list(
            filter(lambda response: response not in true_documents, top_responses)
        )

        top_responses_without_true_documents = top_responses_without_true_documents[0:10]

        for top_response in top_responses_without_true_documents:
            self.dialog_lookup_table.append(int(key))
            self.training_set.append(negative_training_entry + [top_response])
