from pymongo import MongoClient
from pymongo.server_api import ServerApi
from src.config.config import Config

from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(config.mongo_uri)
        self.glossary_db = self.client[config.mongo_glossary_db]
        self.glossary_collection = self.glossary_db[config.mongo_glossary_collection]


        self.metadata_db = self.client[config.mongo_metadata_db]
        self.metadata_collection = self.metadata_db[config.mongo_metadata_collection]



# # create MongoDB client
# client = MongoClient(config.mongo_uri)
# glossary_db = client[config.mongo_glossary_db]
#
#
# # glossary collection
# glossary_collection = glossary_db[config.mongo_glossary_collection]


