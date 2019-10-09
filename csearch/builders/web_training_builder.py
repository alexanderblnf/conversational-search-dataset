import json
import csv
from csearch.converters.json2training import WebJson2EasyTraining
from csearch.converters.json2training import WebJson2Training
from csearch.helpers.web_dataset_helper import WebDatasetHelper
from csearch.helpers.file_helper import FileHelper


class WebTrainingSetBuilder:
    def __init__(self, json_location):
        self.__json_location: str = json_location
        self.__json_data_prefix: str = 'merged_'
        self.__url_mapping_prefix: str = 'url_mapping_'

    def __write_tsv(self, file_name: str, data: list, append: bool = False) -> None:
        """
        Given a filename and a list, this function writes the list in tsv format
        :param file_name:
        :param data:
        :return:
        """
        write_mode = 'a' if append else 'w'
        with open(self.__json_location + '/' + file_name, write_mode) as tsv_file:
            writer = csv.writer(tsv_file, delimiter='\t', lineterminator='\n')
            for entry in data:
                writer.writerow(entry)

    def __write_array(self, file_name: str, data: list, append: bool = False) -> None:
        write_mode = 'a' if append else 'w'
        with open(self.__json_location + '/' + file_name, write_mode) as f:
            for entry in data:
                f.write('%s\n' % entry)

    def __build_bm25_helper(self, is_easy=False):
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

        return dataset_helper.build_multi_topic_bm25_helper(json_data_for_bm25) if is_easy else \
            dataset_helper.build_bm25_helper(json_data_for_bm25)

    def build(self, is_easy=False) -> None:
        """
        Given a json structure, this function builds a tsv containing all possible (label, context, document) triples
        that can be obtained from the dialogues
        :return:
        """
        allocations = ['train', 'dev', 'test']

        bm25_helper = self.__build_bm25_helper(is_easy)

        for allocation in allocations:
            with open(self.__json_location + self.__json_data_prefix + allocation + '_urls.json', 'r') as f:
                json_data = json.load(f)

            with open(self.__json_location + self.__url_mapping_prefix + allocation + '.json', 'r') as f:
                url_mapping_allocation = json.load(f)

            suffix = '' if is_easy else '_hard'
            file_location = self.__json_location + '/' + 'data_' + allocation + '_web' + suffix
            file_helper = FileHelper(file_location)

            json2training_converter = WebJson2EasyTraining(json_data, url_mapping_allocation, bm25_helper, file_helper) \
                if is_easy else WebJson2Training(json_data, url_mapping_allocation, bm25_helper, file_helper)

            del json_data
            del url_mapping_allocation

            json2training_converter.convert_and_write()
