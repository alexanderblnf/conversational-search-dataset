import json
import csv
from csearch.converters.json2training import WebJson2Training
from csearch.helpers.web_dataset_helper import WebDatasetHelper


class WebTrainingSetBuilder:
    def __init__(self, json_location):
        self.__json_location: str = json_location
        self.__json_data_prefix: str = 'merged_'
        self.__url_mapping_prefix: str = 'url_mapping_'

    def __write_tsv(self, file_name: str, data: list) -> None:
        """
        Given a filename and a list, this function writes the list in tsv format
        :param file_name:
        :param data:
        :return:
        """
        with open(self.__json_location + '/' + file_name, 'w',) as tsv_file:
            writer = csv.writer(tsv_file, delimiter='\t', lineterminator='\n')
            for entry in data:
                writer.writerow(entry)

    def __write_array(self, file_name: str, data:list) -> None:
        with open(self.__json_location + '/' + file_name, 'w') as f:
            for entry in data:
                f.write('%s\n' % entry)

    def __build_bm25_helper(self):
        allocations = ['train', 'dev']
        json_data_for_bm25 = {}
        current_index = 0
        url_mapping = {}

        for allocation in allocations:
            with open(self.__json_location + self.__json_data_prefix + allocation + '_urls.json', 'r') as f:
                json_data = json.load(f)
            with open(self.__json_location + self.__url_mapping_prefix + allocation + '.json', 'r') as f:
                url_mapping_allocation = json.load(f)

            for i, dialogue in json_data.items():
                json_data_for_bm25[current_index] = dialogue
                current_index += 1

            url_mapping = {**url_mapping, **url_mapping_allocation}

        dataset_helper = WebDatasetHelper(url_mapping)

        return dataset_helper.build_multi_topic_bm25_helper(json_data_for_bm25)

    def build(self) -> None:
        """
        Given a json structure, this function builds a tsv containing all possible (label, context, document) triples
        that can be obtained from the dialogues
        :return:
        """
        allocations = ['train', 'dev', 'test']

        bm25_helper = self.__build_bm25_helper()

        for allocation in allocations:
            with open(self.__json_location + self.__json_data_prefix + allocation + '_urls.json', 'r') as f:
                json_data = json.load(f)

            with open(self.__json_location + self.__url_mapping_prefix + allocation + '.json', 'r') as f:
                url_mapping_allocation = json.load(f)

            json2training_converter = WebJson2Training(json_data, url_mapping_allocation, bm25_helper)

            training_set = json2training_converter.convert()
            dialog_lookup_table = json2training_converter.get_dialog_lookup_table()

            output_file_name = 'data_' + allocation + '_web'
            self.__write_tsv(output_file_name + '.tsv', training_set)
            self.__write_array(output_file_name + '_lookup' '.txt', dialog_lookup_table)