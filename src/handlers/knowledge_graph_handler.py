import os
import hashlib
import pickle
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
from neo4j import Query

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
            
            self.graph = Neo4jGraph(
                url=self.neo4j_uri,
                username=self.neo4j_username,
                password=self.neo4j_password
            )
            
            self.logger.info("Successfully connected to neo4j services")
        
        except Exception as e:
            self.logger.error("Error connecting to neo4j services")
            raise ConnectionError(f"Unable to connect tp neo4j: {e}")

        # Initialize OCR
        self.ocr = PaddleOCR(use_angle_cls=True, lang="en")

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

        # Initialize LLM Tranformer
        self.llm_transformer = LLMGraphTransformer(llm=self.llm_groq)
        
        
    # def process_document(self, pdf_content):
    #     """Process a PDF document and create a knowledge graph."""
    #     extracted_text = ""
    #
    #     # First try normal pdf text extraction
    #     pdf_reader = PdfReader(io.BytesIO(pdf_content))
    #     for page in pdf_reader.pages:
    #         page_text = page.extract_text()
    #         extracted_text += page_text
    #
    #     # If no text was extracted, try OCR
    #     if not extracted_text.strip():
    #         logger.info("No text extracted through normal pdf reading. Attempting OCR....")
    #         extracted_text = self.extracted_text_using_ocr(pdf_content)
    #
    #     logger.info("Successfully extracted content from pdf")
    #     logger.info(f"Extracted Text: {extracted_text}")
    #     # return extracted_text
    #
    #     # split the extracted text into chunks
    #     chunks = self.split_text_into_chunks(extracted_text)
    #     logger.info("Successfully split into chunks")
    #
    #     self.create_knowledge_graph(chunks)
    #     logger.info("Successfully created knowledge graph")

    def process_document(self, pdf_content):
        try:
            logger.info("Starting document processing...")
            extracted_text = ""

            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text

            if not extracted_text.strip():
                logger.info("Trying OCR...")
                extracted_text = self.extracted_text_using_ocr(pdf_content)

            logger.info(f"Extracted text: {extracted_text[:500]}...")

            chunks = self.split_text_into_chunks(extracted_text)
            logger.info(f"Chunks created: {len(chunks)}")

            self.create_knowledge_graph(chunks)
            logger.info("Knowledge graph created successfully")

        except Exception as e:
            logger.error(f"Error during document processing: {e}", exc_info=True)
            raise e

    def extracted_text_using_ocr(self, pdf_content):
        """Extract text from a PDF using PaddleOCR for all pages."""
        extracted_text = []

        # Open the PDF from bytes
        pdf_document = fitz.open("pdf", pdf_content)

        # Loop through all pages
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)

            # Extract image from page
            pix = page.get_pixmap()  # Get a pixmap (image) of the page
            img_data = pix.tobytes("png")  # Convert to PNG byte format for OCR

            # Perform OCR on the image
            results = self.ocr.ocr(img_data, cls=True)  # OCR with PaddleOCR
            page_text = ""
            # for line in results[0]:
            #     page_text += f"{line[1][0]}\n"  # Extract text from OCR results
            # extracted_text.append(page_text)

            if results[0]:
                for line in results[0]:
                    page_text += f"{line[1][0]}\n"
                extracted_text.append(page_text)

        pdf_document.close()
        return "\n".join(extracted_text)
            
        

    def split_text_into_chunks(self, raw_text, chunk_size=500, chunk_overlap=100):
        """Split text into manageable chunks using RecursiveCharacterTextSplitter."""
        # Initialize the text splitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Split the raw text into chunks
        chunks = [Document(page_content=chunk) for chunk in text_splitter.split_text(raw_text)]
        return chunks
    
    # def create_knowledge_graph(self, chunks):
    #     # generate graph documents using LLM
    #     graph_documents = self.llm_transformer.convert_to_graph_documents(chunks)
    #
    #     self.logger.info(f"Graph document: {graph_documents[0]}")
    #
    #     self.save_to_graph(graph_documents)
    #
    #     self.logger.info("Graph document has been processed and saved to the knowledge graph.")
    #
    #     self.create_fulltext_index()
    def create_knowledge_graph(self, chunks):
        try:
            graph_documents = self.llm_transformer.convert_to_graph_documents(chunks)
            logger.info(f"First Graph doc: {graph_documents[0] if graph_documents else 'Empty'}")
            self.save_to_graph(graph_documents)
            self.create_fulltext_index()
        except Exception as e:
            logger.error(f"Graph creation failed: {e}", exc_info=True)
            raise e

    # Save the graph documents into the Neo4j knowledge graph
    def save_to_graph(self, graph_documents):
        """Save the graph documents into the Neo4j knowledge graph."""
        with self.driver.session() as session:
            for graph_document in graph_documents:
                # Create nodes
                for node in graph_document.nodes:
                    session.run(
                        """
                        MERGE (n:`{type}` {{id: $id}})
                        SET n += $properties
                        SET n:__Entity__
                        """.format(type=node.type),
                        id=node.id,
                        properties=node.properties
                    )

                # Create relationships
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
                    
                self.logger.info(f"Nodes: List({graph_document.nodes})")
                self.logger.info(f"Relationships : List({graph_document.relationships})")

    # def create_fulltext_index(self):
    #     query_create = '''
    #     CREATE FULLTEXT INDEX `fulltext_entity_id`
    #     IF NOT EXISTS
    #     FOR (n:__Entity__)
    #     ON EACH [n.id];
    #     '''
    #     with self.driver.session() as session:
    #         session.run(query_create)
    #     self.logger.info("Fulltext index creation attempted (created if not existing).")
    #

    def create_fulltext_index(self):
        query_create = '''
        CREATE FULLTEXT INDEX `fulltext_entity_id`
        IF NOT EXISTS
        FOR (n:__Entity__)
        ON EACH [n.id];
        '''
        with self.driver.session() as session:
            session.run(Query(query_create))  # FIX: wrap with Query()
        self.logger.info("Fulltext index creation attempted (created if not existing).")
