from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import DeepInfra
from neo4j import GraphDatabase
from spacy import load as spacy_load
import spacy
from langchain_community.graphs import Neo4jGraph
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage

from src.handlers.query_handler import QueryHandler
from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)

query_hander = QueryHandler(config, logger)

class AnswerGenerator:
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
            
            self.logger.info("Successfully connected to neo4j database")
        
        except Exception as e:
            self.logger.error("Error connecting to neo4j database")
            raise ConnectionError(f"Unable to connect tp neo4j: {e}")
        
        # Load the SpaCy NLP model for named entity recognition
        self.nlp = spacy.load("en_core_web_sm")
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
        try:
            # context retrieved from knowledge graph
            context = query_hander.retrieve_context_from_kg(query)
            logger.info(f"Retrieved context: {context}")
            
            """
            Dynamically determine if glossary should be included
            """
            
            glossary = self.glossary_provider(query).strip()
            logger.info(f"Matched glossary for the query from glossary dictionary: {glossary}")
            
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
        
        
    
    
    def glossary_provider(self, question):
        """
        Retrieve relevant glossary definitions for the question.
        Returns glossary definitions if a word form the glossary appears in the question
        
        """
        
        
        glossary_dict = {
            "Glonnova": "Glonnova - another name for Global Innovation Forum (GIF)",
            "Aurora Conference": "Aurora Conference - an annual innovation summit focusing on AI advancements.",
            "AI Ethics": "AI Ethics - a set of moral principles guiding AI development and usage."
        }
        
        # convert question to lowercase for case sensitive matching
        question_lower = question.lower()
        
        # check if any glossary term exists in the question
        matched_terms = [definition for term, definition in glossary_dict.items() if term.lower() in question_lower]
        
        
        # Return matched glossary definitions as a string
        return "\n".join(matched_terms) if matched_terms else ""
        
    
    