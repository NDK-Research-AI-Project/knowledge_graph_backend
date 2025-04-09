from src.services.mongo_service import MongoDBHandler
from datetime import datetime

from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)

class GlossaryHandler:
    def __init__(self, logger):
        self.logger = logger

    def add_glossary_items(self, items: list) -> dict:
        """
        Expects items as a list of dictionaries, each with keys "Term" and "Definition".
        Stores each item as a separate document.
        """
        docs = []
        for item in items:
            term = item.get("Term")
            definition = item.get("Definition")
            if not term or not definition:
                self.logger.error("Both 'Term' and 'Definition' are required for each glossary item.")
                continue
            docs.append({
                "term": term,
                "definition": definition,
                "createdAt": datetime.utcnow()
            })
        if not docs:
            return {"message": "No valid glossary items provided."}
        # result = glossary_collection.insert_many(docs)
        result = config.mongo_glossary_collection.insert_many(docs)
        return {"message": f"{len(result.inserted_ids)} glossary items saved."}

    def get_all_glossary_items(self) -> list:
        """Returns all glossary entries as a list of dictionaries."""
        # cursor = glossary_collection.find({})
        cursor = config.mongo_glossary_collection.find()
        items = []
        for doc in cursor:
            items.append({
                "Term": doc.get("term"),
                "Definition": doc.get("definition")
            })
        return items

    def get_glossary_for_query(self, query: str) -> str:
        """
        Searches glossary items whose term appears in the query (case-insensitive)
        and returns their definitions concatenated by newline.
        """
        query_lower = query.lower()
        # cursor = glossary_collection.find({})
        cursor = config.mongo_glossary_collection.find({})
        matched = []
        for doc in cursor:
            term = doc.get("term", "")
            if term.lower() in query_lower:
                matched.append(doc.get("definition", ""))
        return "\n".join(matched) if matched else ""
