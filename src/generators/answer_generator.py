from langchain_core.prompts import ChatPromptTemplate
from langchain_community.graphs import Neo4jGraph
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage

from src.handlers.glossary_handler import GlossaryHandler
from src.handlers.query_handler import QueryHandler
from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)
glossary_handler = GlossaryHandler()
query_hander = QueryHandler(config)

class AnswerGenerator:
    def __init__(self, config):
        # Initialize Neo4j driver with credentials from Config
        self.config = config
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
            
            logger.info("Successfully connected to neo4j services")
        
        except Exception as e:
            logger.error("Error connecting to neo4j services")
            raise ConnectionError(f"Unable to connect tp neo4j: {e}")

        # Load the DeepInfra API token for the LLM
        self.deepinfra_api_token = config.deepinfra_api_token
        self.groq_api_key = config.groq_api_key
        
        self.groq_model = config.groq_model
        self.chat_template = config.chat_template
        
        # Intialize the model
        self.llm_groq = ChatGroq(
            model = self.groq_model,
            api_key=self.groq_api_key,
            temperature=0,
            max_tokens=None
        )
        
        self.prompt = ChatPromptTemplate.from_template(self.chat_template)
        self.chain = self.prompt | self.llm_groq
        
        #self.logger.info(f"Initialized the model: {self.groq_model}")

    def generate_answer(self, query):
        """Generate an answer based on the query using context from knowledge graph and glossary."""
        try:
            # context retrieved from knowledge graph
            context = query_hander.retrieve_context_from_kg(query)
            # logger.info(f"Retrieved context: {context}")

            # logger.info(f"Query: {query} (Type: {type(query)})")
            # logger.info(f"Context: (Type: {type(query)})")
            
            """
            Dynamically determine if glossary should be included
            """

            logger.info("-----------Glossary Starts here---------------")
            
            # glossary = self.glossary_provider(query).strip()
            glossary = glossary_handler.get_glossary_for_query(query)
            # logger.info(f"Matched glossary for the query from glossary dictionary: {glossary}")

            # logger.info(f"Context: {context}")

            # Ensuring glossary field is always present to avoid errors
            result = self.chain.invoke(
                {
                    "context": context,
                    "glossary": glossary if glossary else "",  # Ensures no missing field
                    "question": query,
                }
            )
            
            # Ensure the result is a string before returning it
            if isinstance(result, AIMessage):  
                result = result.content  # Extracting the text content
            
            logger.info(f"Answer generated form LLM: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
        
