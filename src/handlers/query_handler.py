from neo4j import GraphDatabase
from spacy import load as spacy_load
import spacy
from langchain_community.graphs import Neo4jGraph
from neo4j import GraphDatabase
from langchain_groq import ChatGroq

from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)

class QueryHandler:
    def __init__(self, config, logger):
        # Initialize Neo4j driver with credentials from Config
        self.config = config
        self.logger = logger
        self.neo4j_uri = config.neo4j_uri
        self.neo4j_username = config.neo4j_username
        self.neo4j_password = config.neo4j_password
        
        try:
            self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_username, self.neo4j_password))
            
            graph = Neo4jGraph(
                url=self.neo4j_uri,
                username=self.neo4j_username,
                password=self.neo4j_password
            )
            
            # self.logger.info("Successfully connected to neo4j database")
        
        except Exception as e:
            self.logger.error("Error connecting to neo4j database")
            raise ConnectionError(f"Unable to connect tp neo4j: {e}")
        
        # Load the SpaCy NLP model for named entity recognition
        self.nlp = spacy.load("en_core_web_sm")
        # Load the DeepInfra API token for the LLM
        self.deepinfra_api_token = config.deepinfra_api_token
        self.groq_api_key = config.groq_api_key
        
        self.groq_model = config.groq_model
        
        self.llm_groq = ChatGroq(
            model = self.groq_model,
            api_key=self.groq_api_key,
            temperature=0,
            max_tokens=None
        )
        
        
    def retrieve_context_from_kg(self, question):
        entities = [ent[0] for ent in self.extract_entities(question)]
        if not entities:
            return "No entities found in the question."
            
        result = ""
        with self.driver.session() as session:
            for entity in entities:
                response = session.run(
                    """
                    CALL db.index.fulltext.queryNodes('fulltext_entity_id', $query, {limit: 2})
                    YIELD node, score
                    CALL {
                        WITH node
                        MATCH (node)-[r]->(neighbor)
                        RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
                        UNION ALL
                        WITH node
                        MATCH (node)<-[r]-(neighbor)
                        RETURN neighbor.id + ' - ' + type(r) + ' -> ' + node.id AS output
                    }
                    RETURN output LIMIT 50
                    """,
                    {"query": entity}
                )
                    
                results_for_entity = [record["output"] for record in response]
                if results_for_entity:
                    result += f"\nEntity: {entity}\n" + "\n".join(results_for_entity) + "\n"
                else:
                    result += f"\nEntity: {entity} - No related context found in the graph.\n"
            
        return result
        
    def extract_entities(self, text):
        doc = self.nlp(text)  # Fixed typo here
        return [(ent.text, ent.label_) for ent in doc.ents]
        