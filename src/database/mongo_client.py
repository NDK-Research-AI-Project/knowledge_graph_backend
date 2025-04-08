from pymongo import MongoClient
from src.config.config import Config

config = Config()

# create MongoDB client
client = MongoClient(config.mongo_uri)
glossary_db = client[config.mongo_glossary_db]

# glossary collection
glossary_collection = glossary_db[config.mongo_glossary_collection]


