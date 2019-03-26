from csearch.builders.json_builder import StackExchangeJSONBuilder
import os

dump_folder = os.path.dirname(os.path.abspath(__file__)) + '/stackexchange_dump'
StackExchangeJSONBuilder(dump_folder).build_json()
