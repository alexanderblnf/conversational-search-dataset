import json
import argparse
import copy
import requests
import numpy as np
import time

from urlextract import URLExtract
from tqdm import tqdm
from newspaper import Article
from newspaper import ArticleException
from newspaper import Config
from pathlib import PurePath
from urllib.parse import urlparse
from requests.exceptions import MissingSchema, ConnectionError, ReadTimeout
from multiprocessing import Pool
from concurrent.futures import TimeoutError
from pebble import ProcessPool, ProcessExpired



extractor = URLExtract()

INVALID_RESPONSE = {'valid': False}


def load_dataset(file_name: str) -> dict:
    with open(file_name) as f:
        json_data = json.load(f)

    return json_data


def write_dataset(file_name: str, json_data: dict):
    with open(file_name, 'w') as f:
        json.dump(json_data, f)


def add_links_to_conversation(utterances: list):
    utterances_copy = copy.deepcopy(utterances)
    for utterance in utterances_copy:
        utterance['urls'] = extractor.find_urls(utterance['utterance'])

    return utterances_copy


def is_valid_url(url: str) -> bool:
    try:
        headers = requests.head(url, timeout=10).headers
    except:
        return False

    if 'content-type' in headers and 'text/html' not in headers['content-type']:
        return False

    path = PurePath(urlparse(url).path)
    ext = path.suffix[1:]

    if ext and ext not in ['htm', 'html', 'php', 'asp']:
        return False

    return True


def init_article_config():
    config = Config()
    config.fetch_images = False

    return config


def extract_content_from_url(url: str):
    final_url = url if url.startswith('http') else 'http://' + url

    if not is_valid_url(final_url):
        return INVALID_RESPONSE

    try:
        article = Article(final_url, config=init_article_config())
        article.download()
        article.parse()

        return {
            'valid': True,
            'text': article.text
        }
    except:
        return INVALID_RESPONSE


def crawl_all_conversation_urls(utterances: list):
    pages_content = {}

    for utterance in utterances:
        for url in utterance['urls']:
            pages_content[url] = extract_content_from_url(url)
            time.sleep(10)

    return pages_content


# def crawl_worker(cpu_id: int, keys):
#     thread_pages_content = {}
#     keys_range = tqdm(keys, position=cpu_id, desc='CPU ' + str(cpu_id))
#     for key in keys_range:
#         current_conversation = json_data[key]
#         current_entry = crawl_all_conversation_urls(current_conversation['utterances'])
#         thread_pages_content = {**thread_pages_content, **current_entry}
#         keys_range.refresh()
#
#     return thread_pages_content

def crawl_worker(url):
    url_content = extract_content_from_url(url)
    if url_content == INVALID_RESPONSE:
        return None

    time.sleep(10)
    return {url: url_content}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', help='Selects the dataset to enrich', required=True)
    parser.add_argument('--mode', help='Selects the mode to operate', choices=['extract_url', 'crawl_content'], required=True)
    parser.add_argument('--output_file', help='Specifies the file to which to save the new dataset', required=True)
    parser.add_argument('--num_cpus', help='Selects the number of cpus to use. Default is 8')

    args = parser.parse_args()

    json_data = load_dataset(args.dataset)
    incr = 0

    if args.mode == 'extract_url':
        print('Extracting URLs from conversations')
        for key, conversation in tqdm(json_data.items()):
            conversation['utterances'] = add_links_to_conversation(conversation['utterances'])

        write_dataset(args.output_file, json_data)
    elif args.mode == 'crawl_content':
        print('Crawling each URL for content')
        pages_content = {}
        num_cpus = int(args.num_cpus) if args.num_cpus else 8

        all_urls = []
        for key, entry in json_data.items():
            for utterance in entry['utterances']:
                for url in utterance['urls']:
                    all_urls.append(url)

        all_urls = list(set(all_urls))

        # chunk_per_cpu = round(len(json_data) / num_cpus)
        # json_data_keys = np.array(list(json_data.keys()))

        # process_inputs = [(cpu_id, json_data_keys[(chunk_per_cpu * cpu_id):(chunk_per_cpu * cpu_id + chunk_per_cpu)])
        #                   for cpu_id in range(num_cpus)]
        pbar = tqdm(total=len(all_urls))

        with ProcessPool(max_workers=num_cpus) as pool:
            future = pool.map(crawl_worker, all_urls, timeout=35)

            iterator = future.result()
            while True:
                try:
                    result = next(iterator)
                    if result:
                        pages_content = {**pages_content, **result}
                    pbar.update(1)
                    pbar.refresh()
                    # print(len(pages_content))
                except StopIteration:
                    break
                except TimeoutError as error:
                    print("unstable_function took longer than %d seconds" % error.args[1])
                except ProcessExpired as error:
                    print("%s. Exit code: %d" % (error, error.exitcode))
                except Exception as error:
                    print("unstable_function raised %s" % error)
                    print(error.traceback)  # Python's traceback of remote process


        # p = Pool(processes=num_cpus)
        # pages_per_thread = p.starmap(crawl_worker, process_inputs)
        # p.close()

        # for entry in pages_per_thread:
        #     pages_content = {**pages_content, **entry}
        #
        pbar.close()
        write_dataset(args.output_file, pages_content)