from src.services.mongo_service import MongoDBHandler
from datetime import datetime, UTC
import pandas as pd
from pymongo.mongo_client import MongoClient
from rapidfuzz import process, fuzz

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
        # Cache for glossary items
        self.glossary_cache = None
        self.last_updated = None
        self._refresh_cache()

    def _refresh_cache(self):
        """Refresh the glossary cache from the database"""
        cursor = self.glossary_collection.find()
        items = []
        for doc in cursor:
            items.append({
                "term": doc.get("term"),
                "definition": doc.get("definition")
            })
        self.glossary_cache = pd.DataFrame(items) if items else pd.DataFrame(columns=["term", "definition"])
        self.last_updated = datetime.now(UTC)
        logger.info(f"Glossary cache refreshed with {len(items)} items")

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
                "createdAt": datetime.now(UTC)
            })
        if not docs:
            return {"message": "No valid glossary items provided."}
        result = self.glossary_collection.insert_many(docs)
        # Refresh cache after adding new items
        self._refresh_cache()
        return {"message": f"{len(result.inserted_ids)} glossary items saved."}

    def get_all_glossary_items(self) -> list:
        """Returns all glossary entries as a list of dictionaries."""
        # Check if cache needs refresh (optional, can be removed if always updated after add)
        if not self.glossary_cache is None:
            self._refresh_cache()
        
        return self.glossary_cache.to_dict('records') if not self.glossary_cache.empty else []

    def get_glossary_for_query(self, query: str) -> str:
        """
        Uses fuzzy matching to find glossary terms related to the query
        and returns their definitions.
        """
        # Ensure cache is available
        if self.glossary_cache is None or self.glossary_cache.empty:
            self._refresh_cache()
            if self.glossary_cache.empty:
                return ""
        
        matched = []
        
        # Get all terms
        terms = self.glossary_cache["term"].tolist()
        
        # Find best matches using fuzzy search with partial ratio
        matches = process.extract(
            query, 
            terms, 
            scorer=fuzz.partial_ratio, 
            limit=1,  
            score_cutoff=75 
        )
        
        for term, score, _ in matches:
            definition = self.glossary_cache.loc[self.glossary_cache["term"] == term, "definition"].iloc[0]
            matched.append(f"{term}: {definition}")
            logger.info(f"Fuzzy matching happened - term: {term}, score: {score}")
        
        return "\n".join(matched) if matched else ""


