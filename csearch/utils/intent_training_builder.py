# %%
import json
import csv
import numpy as np
from sklearn import preprocessing
from sklearn.model_selection import KFold


def get_data():
    splits = ['train', 'dev', 'test']
    all_intents = []
    all_data = []
    all_data_encoded = []

    for split in splits:
        with open('../../stackexchange_dump/merged_' + split + '_intents.json', 'r') as f:
            data = json.load(f)
        for key, entry in data.items():
            if 'has_intent_labels' in entry:
                for utterance in entry['utterances']:
                    if 'intent' not in utterance:
                        print(entry)
                        continue

                    intent = ','.join(utterance['intent'])
                    all_data.append([intent, utterance['utterance'], 'placeholder'])
                    all_intents.append(intent)

    le = preprocessing.LabelEncoder()
    le.fit(all_intents)

    for entry in all_data:
        encoded_intent = le.transform([entry[0]])[0]
        encoded_entry = [encoded_intent, entry[1], entry[2]]
        all_data_encoded.append(encoded_entry)

    return np.array(all_data), np.array(all_data_encoded)


def generate_training_sets():
    all_data, all_data_encoded = get_data()

    kf = KFold(n_splits=10, shuffle=True)
    for index, (train_index, test_index) in enumerate(kf.split(all_data)):
        print('Split: ' + str(index))
        terminator = '.tsv.' + str(index)
        write_tsv('../../stackexchange_dump/crossval_intents/intent_data_train_unencoded' + terminator, all_data[train_index])
        write_tsv('../../stackexchange_dump/crossval_intents/intent_data_train' + terminator, all_data_encoded[train_index])
        write_tsv('../../stackexchange_dump/crossval_intents/intent_data_dev_unencoded' + terminator, all_data[test_index])
        write_tsv('../../stackexchange_dump/crossval_intents/intent_data_dev' + terminator, all_data_encoded[test_index])
        write_tsv('../../stackexchange_dump/crossval_intents/intent_data_test_unencoded' + terminator, all_data[test_index])
        write_tsv('../../stackexchange_dump/crossval_intents/intent_data_test' + terminator, all_data_encoded[test_index])


def write_tsv(file_name, dataset):
    with open(file_name, 'w') as tsv_file:
        writer = csv.writer(tsv_file, delimiter='\t', lineterminator='\n')
        for entry in dataset:
            writer.writerow(entry)


if __name__ == '__main__':
    generate_training_sets()

    # for split in splits:
    #     final_dataset_encoded = generate_training_set(split, le)
    #     with open('stackexchange_dump/intent_data_' + split + '.tsv', 'w', ) as tsv_file:
    #         writer = csv.writer(tsv_file, delimiter='\t', lineterminator='\n')
    #         for entry in final_dataset_encoded:
    #             writer.writerow(entry)
# %%
