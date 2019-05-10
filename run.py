from csearch.builders.json_builder import StackExchangeJSONBuilder
from csearch.builders.training_builder import TrainingSetBuilder
import os
import sys


def build_json(dump_folder: str, topic: str):
    dataset_split = {
        'train': 0.7,
        'dev': 0.15,
        'test': 0.15,
    }
    StackExchangeJSONBuilder(dump_folder, topic).build_json(dataset_split)


def build_training(dump_folder: str, topic: str):
    dataset_split = {
        'train': 0.7,
        'dev': 0.15,
        'test': 0.15,
    }
    TrainingSetBuilder(dump_folder).build(dataset_split)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("ERROR: Incorrect number of arguments. Syntax should be: python run.py [mode] [topic]")
        exit(-1)

    switch = {
        'json': build_json,
        'training': build_training,
    }

    mode = sys.argv[1]

    if mode not in switch.keys():
        options = "[" + " | ".join(switch.keys()) + "]"
        print("ERROR: Mode not found. Must be from " + options)
        exit(-1)

    topic = sys.argv[2]

    allowed_topics = [
        "academia", "android", "apple", "askubuntu", "bicycles", "biology", "buddhism", "cooking", "dba", "diy",
        "electronics", "ell", "economics",
        "english", "gaming", "gis", "math", "security", "law", "money", "movies", "music", "philosophy",
        "physics", "photo", "politics", "salesforce", "scifi", "security", "sound", "stats", "travel",
        "workplace", "worldbuilding"
    ]

    if topic not in allowed_topics:
        options = "[" + " | ".join(allowed_topics) + "]"
        print("ERROR: Topic not found. Must be from " + options)
        exit(-1)

    dump_folder = os.path.dirname(os.path.abspath(__file__)) + '/stackexchange_dump/' + topic

    if not os.path.exists(dump_folder + '/Posts.xml'):
        print("ERROR: The files for the chosen topic do not exist")
        exit(-1)

    switch[mode](dump_folder, topic)

