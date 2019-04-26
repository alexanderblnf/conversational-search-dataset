from csearch.builders.json_builder import StackExchangeJSONBuilder
from csearch.builders.training_builder import TrainingSetBuilder
import os
import sys


def build_json(dump_folder: str):
    StackExchangeJSONBuilder(dump_folder).build_json()


def build_training(dump_folder: str):
    dataset_split = {
        'train': 0.8,
        'dev': 0.1,
        'test': 0.1,
    }
    TrainingSetBuilder(dump_folder).build(dataset_split)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Incorrect number of arguments. Syntax should be: python run.py [mode]")
        exit(-1)

    mode = sys.argv[1]
    dump_folder = os.path.dirname(os.path.abspath(__file__)) + '/stackexchange_dump'

    switch = {
        'json': build_json,
        'training': build_training,
    }
    try:
        switch[mode](dump_folder)
    except KeyError:
        options = "[" + " | ".join(switch.keys()) + "]"
        print("Mode not found. Must be from " + options)


