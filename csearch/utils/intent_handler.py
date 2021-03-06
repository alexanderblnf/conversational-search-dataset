import json
import csv
import argparse
from sklearn import preprocessing
from collections import defaultdict
import numpy as np


def merge_intent_to_json_dataset(dataset_file: str, intent_file: str, split: str):
    """
    Given a JSON dataset, a csv with intents and a split, it appends the intents to the dataset and
    writes it into a new JSON file (suffixed with _intents)
    :param dataset_file: Path to dataset .json
    :param intent_file: Path to intent .csv
    :param split: Specifies the allocation (can be train, dev, test)
    """
    if split not in ['train', 'dev', 'test']:
        raise ValueError('Split should be either train, dev or test')

    intent_data = []
    with open(intent_file, 'r') as intent_f:
        records = csv.DictReader(intent_f)
        for row in records:
            intent_data.append(dict(row))

    with open(dataset_file, 'r') as dataset_f:
        dataset_data = json.load(dataset_f)

    for row in intent_data:
        if row['allocation'] != split:
            continue

        conversation_id = row['conversation_id']
        comment_pos = int(row['comment_pos'])
        if 'has_intent_labels' not in dataset_data[conversation_id]:
            dataset_data[conversation_id]['has_intent_labels'] = True
            dataset_data[conversation_id]['utterances'][0]['intent'] = ['OQ']

        dataset_data[conversation_id]['utterances'][comment_pos - 1]['intent'] = row['annotations'].split(',')

    with open(dataset_file[:dataset_file.index('.json')] + '_intents.json', 'w') as output_f:
        json.dump(dataset_data, output_f)


def generate_intent_mtl_training_from_training_set(dataset_location: str, training_lookup_location: str, samples_per_context: int):
    """
    Generates the intent file for training based on the lookup of the Main Training file.
    For each dialogue context, the function creates a new entry in the intent training file corresponding to the
    intent of the last utterance in the current context. If current
    :param dataset_file: Path to .json dataset
    :param training_lookup_file: Path to .txt lookup file generated when the training .tsv was generated
    :param samples_per_context: Number of training samples that were generated per context
    :return:
    """
    # To be changed if something else than the last user query of the context needs to be observed
    initial_last_utterance = 3
    allocations = ['train', 'dev', 'test']
    training_intent_data = defaultdict(list)
    training_lookup_files = {}

    for allocation in allocations:
        dataset_file = dataset_location + '/merged_' + allocation + '_intents.json'
        with open(dataset_file, 'r') as dataset_f:
            dataset_data = json.load(dataset_f)

        lookup_data = []
        training_lookup_file = training_lookup_location + '/data_' + allocation + '_web_hard_lookup.txt'
        training_lookup_files[allocation] = training_lookup_file

        with open(training_lookup_file, 'r') as training_lookup_f:
            rows = csv.reader(training_lookup_f)
            for row in rows:
                lookup_data.append(row[0])

        current_index = lookup_data[0]
        occurrences = 0
        current_last_utterance = initial_last_utterance

        for entry in lookup_data:
            if entry != current_index:
                current_index = entry
                occurrences = 0
                current_last_utterance = initial_last_utterance

            if 'has_intent_labels' in dataset_data[current_index]:
                conversation_length = len(dataset_data[current_index]['utterances'])

                # Web can have multiple URLs for the same conversation
                if current_last_utterance > conversation_length:
                    occurrences = 0
                    current_last_utterance = initial_last_utterance

                training_intent_data[allocation].append(dataset_data[current_index]['utterances'][current_last_utterance - 1]['intent'])
            else:
                training_intent_data[allocation].append('None')

            if occurrences > 0 and occurrences % samples_per_context == 0:
                current_last_utterance += 2

            occurrences += 1

    label_encoder = preprocessing.LabelEncoder()
    label_encoder.fit([','.join(sorted(val)) if val != 'None' else 'A' for values in training_intent_data.values()
                       for val in values])
    np.save(training_lookup_location + '/encoder_classes.npy', label_encoder.classes_)

    for allocation in allocations:
        output_file = training_lookup_files[allocation][:training_lookup_files[allocation].index('.txt')] + '_intents'
        with open(output_file + '.txt', 'w') as output_f:
            for entry in training_intent_data[allocation]:
                output_f.write("%s\n" % str(entry))

        training_intent_data_stringified = [','.join(sorted(entry)) if entry != 'None' else 'A'
                                            for entry in training_intent_data[allocation]]

        training_intent_data_encoded = label_encoder.transform(training_intent_data_stringified)

        with open(output_file + '_encoded.txt', 'w') as output_f:
            for entry in training_intent_data_encoded:
                output_f.write("%s\n" % str(entry))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--mode', help='Selects the mode of operation', choices=['merge', 'generate_mtl'], required=True)
    parser.add_argument('--dataset_file', help='JSON file containing the json dataset')
    parser.add_argument('--split', help='Dataset split (train, dev or test')
    parser.add_argument('--intent_file', help='CSV file containing the intents')
    parser.add_argument('--dataset_location', help='Location of the JSON files containing the json dataset')
    parser.add_argument('--training_lookup_location', help='Location of the lookup files generated with the training .tsv')
    parser.add_argument('--samples_per_context', help='How many samples are generated per context')

    args = parser.parse_args()

    if args.mode == 'merge':
        if not args.dataset_file or not args.split or not args.intent_file:
            parser.error('--dataset_file, --split and --intent_file are required when using the merge mode')
        merge_intent_to_json_dataset(args.dataset_file, args.intent_file, args.split)

    if args.mode == 'generate_mtl':
        if not args.dataset_location or not args.training_lookup_location or not args.samples_per_context:
            parser.error('--dataset_location, --training_lookup_location and --samples_per_context '
                         'are required when using the generate mode')
        generate_intent_mtl_training_from_training_set(
            args.dataset_location, args.training_lookup_location, int(args.samples_per_context)
        )
