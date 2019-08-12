import json
import pandas as pd
import numpy as np
import time
import os
import itertools as it
import argparse


from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
from collections import defaultdict

from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import KFold

from pandas import DataFrame
from operator import add
from multiprocessing import Pool

import nltk


def get_json_data() -> str:
    input_files = {
        'train': 'merged_train_intents.json',
        'dev': 'merged_dev_intents.json',
        'test': 'merged_test_intents.json'
    }

    json_data = {}

    for split, input_file in input_files.items():
        with open('../../stackexchange_dump/' + input_file) as f:
            json_data[split] = json.load(f)

    del json_data['train']['10298']

    json_data_with_intents = []
    for split, data in json_data.items():
        for key, entry in data.items():
            if 'has_intent_labels' in entry:
                utterances = [
                    {'utterance': utt['utterance'], 'intent': utt['intent'], 'split': split}
                    for utt in entry['utterances']
                ]
                json_data_with_intents += utterances

    return json.dumps(json_data_with_intents)


def get_preprocessed_df(df: DataFrame) -> DataFrame:
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')

    corpus = df.copy()
    corpus['utterance'] = [entry.lower() for entry in corpus['utterance']]
    corpus['utterance'] = [word_tokenize(entry) for entry in corpus['utterance']]

    tag_map = defaultdict(lambda: wn.NOUN)
    tag_map['J'] = wn.ADJ
    tag_map['V'] = wn.VERB
    tag_map['R'] = wn.ADV
    for index, entry in enumerate(corpus['utterance']):
        final_words = []
        word_lemmatized = WordNetLemmatizer()
        for word, tag in pos_tag(entry):
            if word not in stopwords.words('english') and word.isalpha():
                word_final = word_lemmatized.lemmatize(word, tag_map[tag[0]])
                final_words.append(word_final)
        # The final processed set of words for each iteration will be stored in 'text_final'
        corpus.loc[index, 'utterance_final'] = str(final_words)

    return corpus


# def get_split_datasets(processed_df: DataFrame):
#     train = processed_df[(processed_df['split'] == 'train') | (processed_df['split'] == 'dev')]
#     test = processed_df[processed_df['split'] == 'test']
#
#     tfidf_vectorizer = TfidfVectorizer()
#     tfidf_vectorizer.fit(processed_df['utterance_final'])
#     encoder = MultiLabelBinarizer()
#
#     x_train = tfidf_vectorizer.transform(train['utterance_final'])
#     y_train = encoder.fit_transform(train['intent'])
#     x_test = tfidf_vectorizer.transform(test['utterance_final'])
#     y_test = encoder.fit_transform(test['intent'])
#
#     return x_train, y_train, x_test, y_test


def custom_accuracy(y_true, y_pred):
    accuracies = []
    for index, true_labels in enumerate(y_true):
        predicted_labels = y_pred[index]
        label_sum = list(map(add, true_labels, predicted_labels))
        acc = label_sum.count(2) / (label_sum.count(2) + label_sum.count(1))
        accuracies.append(acc)

    return np.mean(accuracies)


def custom_cv(clf, processed_ds, labels, num_iterations, random_state, tfidf_vectorizer, label_encoder):
    custom_accuracy_avg = []
    for i in range(num_iterations):
        kf = KFold(n_splits=10, shuffle=True, random_state=random_state + i * int(round(time.time()) / 1000))
        for train_index, test_index in kf.split(processed_ds):
            x_train, x_test = tfidf_vectorizer.transform(processed_ds[train_index]), \
                              tfidf_vectorizer.transform(processed_ds[test_index])
            y_train, y_test = label_encoder.transform(labels[train_index]), label_encoder.transform(labels[test_index])
            y_predicted = clf.fit(x_train, y_train).predict(x_test)
            custom_accuracy_avg.append(custom_accuracy(y_test, y_predicted))

    return np.mean(custom_accuracy_avg), np.std(custom_accuracy_avg)


def cv_worker(work_num):
    entry = combinations[work_num]

    clf = OneVsRestClassifier(
        GradientBoostingClassifier(learning_rate=entry[0], n_estimators=entry[1], max_depth=entry[2])
    )
    print('Combination ' + str(work_num))
    mean_accuracy, std_accuracy = custom_cv(clf, processed_ds, labels, 2, work_num * 10, tfidf_vectorizer, encoder)

    return [work_num, mean_accuracy, std_accuracy]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_cpus', help='Selects the number of cpus to use', required=True)

    args = parser.parse_args()


    if not os.path.isfile('processed_df.pkl'):
        print('Building dataframe...')
        initial_df = pd.read_json(get_json_data())

        print('Pre-processing dataframe')
        preprocessed_df = get_preprocessed_df(initial_df)
        preprocessed_df.to_pickle('processed_df.pkl')
    else:
        preprocessed_df = pd.read_pickle('processed_df.pkl')

    processed_ds = preprocessed_df['utterance_final']
    labels = preprocessed_df['intent']

    print('Fitting the TF-IDF Vectorizer and Label Encoder..')
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_vectorizer.fit(processed_ds)

    encoder = MultiLabelBinarizer()
    encoder.fit(labels)

    param_grid = {
        'learning_rate': [0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 1],
        'n_estimators': [80, 100, 200, 250, 300, 500],
        'max_depth': [1, 3, 5, 7],
    }

    all_keys = list(param_grid.keys())
    combinations = list(it.product(*(param_grid[name] for name in all_keys)))
    print('Total Combinations: ' + str(len(combinations)))

    p = Pool(processes=int(args.num_cpus))
    data = p.map(cv_worker, [i for i in range(len(combinations))])
    p.close()

    np.savetxt('cv_result.out', data)

    best_entry = 0
    best_index = 0
    best_std = 0

    for result_entry in data:
        mean_entry = result_entry[1]
        std_entry = result_entry[2]
        if mean_entry >= best_entry:
            best_entry = mean_entry
            best_index = result_entry[0]
            best_std = std_entry

    print(best_index)
    print(best_entry)
    print(best_std)
    print(combinations[best_index])
    #
    # processed_ds =
    # x_train, y_train, x_test, y_test = get_split_datasets(preprocessed_df)

    # print('Applying classifier')

    # predictions = clf.fit(x_train, y_train).predict(x_test)
    # print(custom_accuracy(y_test, predictions))
