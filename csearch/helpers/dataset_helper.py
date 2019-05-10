

class DatasetHelper:
    @classmethod
    def __get_index_split(cls, dataset: dict, dataset_split: dict) -> dict:
        """
        Given a train/dev/test distribution, this function returns the indexes of the chronological split. The
        resulting split can deviate from the proposed percentages in case the index falls between dialogs occuring
        at the same time
        NOTE: The dataset is assumed to be already ordered, as the previous processes take care of that
        :param dataset
        :param dataset_split: Should be a dict in the form
        {
            'train': 0.8,
            'dev': 0.1,
            'test': 0.1
        }
        :return:
        """
        dataset_length = len(dataset)
        dev_start_index = int(dataset_split['train'] * dataset_length)

        while (dataset[dev_start_index]['dialog_time']
               == dataset[dev_start_index + 1]['dialog_time']):
            dev_start_index += 1

        test_start_index = dev_start_index + int(dataset_split['dev'] * dataset_length)
        while (dataset[test_start_index]['dialog_time']
               == dataset[test_start_index + 1]['dialog_time']):
            test_start_index += 1

        return {
            'dev_start_index': dev_start_index,
            'test_start_index': test_start_index,
        }

    @classmethod
    def get_split_dataset(cls, dataset: dict, dataset_split: dict) -> dict:
        index_split = DatasetHelper.__get_index_split(dataset, dataset_split)
        split_dataset = {
            'train': {},
            'dev': {},
            'test': {}
        }

        current_dataset_allocation = 'train'
        for (key, entry) in dataset.items():
            if key == index_split['dev_start_index']:
                current_dataset_allocation = 'dev'

            elif key == index_split['test_start_index']:
                current_dataset_allocation = 'test'

            split_dataset[current_dataset_allocation].update({key: entry})

        return split_dataset
