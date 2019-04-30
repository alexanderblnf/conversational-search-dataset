import json
import csv
from csearch.converters.json2training import JSON2Training


class TrainingSetBuilder:
    def __init__(self, json_location):
        self.__json_location = json_location

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

    def build(self, dataset_split: dict) -> None:
        """
        Given a json structure, this function builds a tsv containing all possible (label, context, response) triples
        that can be obtained from the dialogues
        :return:
        """
        with open(self.__json_location + '/data.json', 'r') as f:
            json_data = json.load(f)

        json2training_converter = JSON2Training(json_data, dataset_split)
        training_set = json2training_converter.convert()
        dialog_lookup_table = json2training_converter.get_dialog_lookup_table()

        for allocation in dataset_split.keys():
            self.__write_tsv('data_' + allocation + '.tsv', training_set[allocation])
            self.__write_array('data_lookup_' + allocation + '.txt', dialog_lookup_table[allocation])
