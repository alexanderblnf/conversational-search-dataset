import csv

class FileHelper:
    def __init__(self, file_location: str):
        self.__file_location = file_location

    def write_tsv(self, suffix: str, data: list, append: bool = False) -> None:
        """
        Given a filename and a list, this function writes the list in tsv format
        :param file_name:
        :param data:
        :return:
        """
        write_mode = 'a' if append else 'w'
        with open(self.__file_location + suffix, write_mode) as tsv_file:
            writer = csv.writer(tsv_file, delimiter='\t', lineterminator='\n')
            for entry in data:
                writer.writerow(entry)

    def write_array(self, suffix: str, data: list, append: bool = False) -> None:
        write_mode = 'a' if append else 'w'
        with open(self.__file_location + suffix, write_mode) as f:
            for entry in data:
                f.write('%s\n' % entry)
