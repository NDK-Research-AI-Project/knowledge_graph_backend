import os
import hashlib
import pickle
import spacy
import io
import fitz
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain_community.graphs import Neo4jGraph
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.llms import DeepInfra
from neo4j import GraphDatabase
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_community.graphs import Neo4jGraph
from langchain_community.document_loaders import TextLoader
from yfiles_jupyter_graphs import GraphWidget
from PyPDF2 import PdfReader
from paddleocr import PaddleOCR
from langchain_groq import ChatGroq

from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)


class KnowledgeGraphHandler:
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
        
        self.llm_groq = ChatGroq(
            model = self.groq_model,
            api_key=self.groq_api_key,
            temperature=0,
            max_tokens=None
        )
        
        
    def process_document(self, pdf_content):
        extracted_text = ""
        
        # First try normal pdf text extraction
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            extracted_text += page_text
            
        # If no text was extracted, try OCR
        if not extracted_text.strip():
            logger.info("No text extracted through normal pdf reading. Attempting OCR....")
            extracted_text = self.extracted_text_using_ocr(pdf_content)
            
        logger.info("Successfully extracted content from pdf")
        logger.info(f"Extracted Text: {extracted_text}")
        # return extracted_text
        
        # split the extracted text into chunks
        chunks = self.split_text_into_chunks(extracted_text)
        logger.info("Successfully splitted into chunks")
        
        self.create_knowledge_graph(chunks)
        logger.info("Successfully created knowledge graph")
            
    def extracted_text_using_ocr(self, pdf_content):
        """Extract text from a PDF using PaddleOCR for all pages."""
        extracted_text = []
        ocr = PaddleOCR(use_angle_cls=True)  # Initialize PaddleOCR

        # Open the PDF from bytes
        pdf_document = fitz.open("pdf", pdf_content)

        # Loop through all pages
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)

            # Extract image from page
            pix = page.get_pixmap()  # Get a pixmap (image) of the page
            img_data = pix.tobytes("png")  # Convert to PNG byte format for OCR

            # Perform OCR on the image
            results = ocr.ocr(img_data, cls=True)  # OCR with PaddleOCR
            page_text = ""
            for line in results[0]:
                page_text += f"{line[1][0]}\n"  # Extract text from OCR results
            extracted_text.append(page_text)

        return "\n".join(extracted_text)
            
        

    def split_text_into_chunks(self, raw_text, chunk_size=500, chunk_overlap=100):
        """Split text into manageable chunks using RecursiveCharacterTextSplitter."""
        # Initialize the text splitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Split the raw text into chunks
        chunks = [Document(page_content=chunk) for chunk in text_splitter.split_text(raw_text)]
        return chunks
    
    def create_knowledge_graph(self, chunks):
        # set the LLM transformer
        llm_transformer = LLMGraphTransformer(llm=self.llm_groq)
        
        # generate graph documents using LLM
        graph_documents = llm_transformer.convert_to_graph_documents(chunks)
        
        logger.info(f"Graph document: {graph_documents[0]}")
        
        self.save_to_graph(graph_documents)
        
        logger.info("Graph document has been processed and saved to the knowledge graph.")
        
        self.create_fulltext_index()
        
        
    # Save the graph documents into the Neo4j knowledge graph
    def save_to_graph(self, graph_documents):
        with self.driver.session() as session:
            for graph_document in graph_documents:
                for node in graph_document.nodes:
                    session.run(
                        """
                        MERGE (n:`{type}` {{id: $id}})
                        SET n += $properties
                        SET n:__Entity__
                        """.format(type=node.type),
                        id=node.id, properties=node.properties
                    )
                
                for relationship in graph_document.relationships:
                    session.run(
                        """
                        MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                        MERGE (a)-[r:{type}]->(b)
                        SET r += $properties
                        """.format(type=relationship.type),
                        source_id=relationship.source.id,
                        target_id=relationship.target.id,
                        properties=relationship.properties
                    )
                    
                logger.info(f"Nodes: List({graph_document.nodes})")
                logger.info(f"Relationships : List({graph_document.relationships})")

    def create_fulltext_index(self):
        query_create = '''
        CREATE FULLTEXT INDEX `fulltext_entity_id`
        IF NOT EXISTS
        FOR (n:__Entity__)
        ON EACH [n.id];
        '''
        with self.driver.session() as session:
            session.run(query_create)
        logger.info("Fulltext index creation attempted (created if not existing).") 
        