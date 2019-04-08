import json
import csv
from csearch.converters.json2training import JSON2Training


class TrainingSetBuilder:
    def __init__(self, json_location):
        self.__json_location = json_location

    def build(self) -> None:
        with open(self.__json_location + '/data.json', 'r') as f:
            json_data = json.load(f)

        training_set = JSON2Training(json_data).convert()

        with open(self.__json_location + '/data.tsv', 'w',) as tsv_file:
            writer = csv.writer(tsv_file, delimiter='\t', lineterminator='\n')
            for entry in training_set:
                writer.writerow(entry)
