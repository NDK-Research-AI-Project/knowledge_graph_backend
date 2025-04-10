from src.services.mongo_service import MongoDBHandler
from datetime import datetime
from pymongo.mongo_client import MongoClient

from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)

class GlossaryHandler:
    def __init__(self):
        # Mongo config
        self.mongo_client = MongoClient(config.mongo_uri)
        self.glossary_db = self.mongo_client[config.mongo_glossary_db]
        self.glossary_collection = self.glossary_db[config.mongo_glossary_collection]

    def add_glossary_items(self, items: list) -> dict:
        """
        Expects items as a list of dictionaries, each with keys "term" and "definition".
        Stores each item as a separate document.
        """
        docs = []
        for item in items:
            term = item.get("term")
            definition = item.get("definition")
            if not term or not definition:
                logger.error("Both 'term' and 'definition' are required for each glossary item.")
                continue
            docs.append({
                "term": term,
                "definition": definition,
                "createdAt": datetime.utcnow()
            })
        if not docs:
            return {"message": "No valid glossary items provided."}
        # result = glossary_collection.insert_many(docs)
        result = self.glossary_collection.insert_many(docs)
        return {"message": f"{len(result.inserted_ids)} glossary items saved."}

    def get_all_glossary_items(self) -> list:
        """Returns all glossary entries as a list of dictionaries."""
        # cursor = glossary_collection.find({})
        cursor = self.glossary_collection.find()
        items = []
        for doc in cursor:
            items.append({
                "term": doc.get("term"),
                "definition": doc.get("definition")
            })
        return items

    def get_glossary_for_query(self, query: str) -> str:
        """
        Searches glossary items whose term appears in the query (case-insensitive)
        and returns their definitions concatenated by newline.
        """
        query_lower = query.lower()
        # cursor = glossary_collection.find({})
        cursor = self.glossary_collection.find()
        matched = []
        for doc in cursor:
            term = doc.get("term", "")
            if term.lower() in query_lower:
                definition = doc.get("definition", "")
                # Format the term and definition together in a string
                matched.append(f"{term}: {definition}")

            # Return the matched terms and definitions, separated by newlines
        return "\n".join(matched) if matched else ""


