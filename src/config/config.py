import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration class for the knowledge-graph-backend application
    
    This class manages all configuration parameters, loading them from environment
    variables with fallback to default values
    """

    def __init__(self):

        # Correct Neo4j
        # self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://9d3d116e.databases.neo4j.io")
        # self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        # self.neo4j_password = os.getenv("NEO4J_PASSWORD", "MTmhQ8kiaRqRltgDThU_4hYE-aCCpIVk5aNmcUnKWKU")

        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://c95a3680.databases.neo4j.io")
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "5SYecqiUcLZz4pzO9CDdGs9jlU5rOKUQ6ddtK6DEl1o")

        self.deepinfra_api_token = os.getenv("DEEPINFRA_API_TOKEN", "YuGM4YMWqQU4kVM0u47Ntev9gUjFv2Om")

        self.groq_api_key = os.getenv("GROQ_API_KEY", "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")

        self.chat_template = os.getenv("CHAT_TEMPLATE", """Answer the question based only on the following context:

        Context: {context}

        Glossary (use for understanding terms in the question and context, not for direct inclusion in the answer): 
        {glossary}

        Question: {question}

        Instructions:
        1. Use glossary definitions to infer the meanings of terms used in the question and context.
        2. Do not copy glossary definitions directly into the answer.
        3. If the glossary is empty or irrelevant, ignore it.
        4. Do not answer based on your own general knowledge—only use the provided context and glossary.
        5. If the question is unclear even after applying glossary info, say: "I'm sorry, I didn't understand your question. Could you please rephrase it?"
        6. Give a direct answer only—no explanations of reasoning.
        7. Use only necessary info from context—ignore unrelated parts.

        Answer:""")

        # Logging configuration
        self.logging_config = {
            'logstash_host': os.getenv('LOGSTASH_HOST', 'localhost'),
            'logstash_port': int(os.getenv('LOGSTASH_PORT', '5044')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'app_name': 'document-summarizer'
        }
        
        # LLM configurations
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        # self.groq_temperature = os.getenv("GROQ_TEMPERATURE", "0")


        # MongoDB
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://kavindamadhuranga74:fLaa4T079luktEQv@cluster0.xkdqxqw.mongodb.net/?appName=Cluster0")
        # self.mongo_glossary_db = os.getenv("GlossaryDB", "your_ai_db")
        # self.mongo_glossary_collection = os.getenv("GlossaryCollection", "pdf_store")


        self.mongo_glossary_db = os.getenv("GlossaryDB", "glossary_database")
        self.mongo_glossary_collection = os.getenv("GlossaryCollection", "glossary_collection")


        self.mongo_metadata_db = os.getenv("METADATA_DB", "your_ai_db")
        self.mongo_metadata_collection = os.getenv("METADATA_COLLECTION", "pdf_store")


        # Azure
        self.azure_connection_string = os.getenv("AZURE_CONNECTION_STRING", "DefaultEndpointsProtocol=https;AccountName=researchpdfstore;AccountKey=SQnY5MvTblA+bEu7bPw3orgeZhZzvg6jNTSF4c7yWCFsdk3cwWe5pqAPgPRGdCiwr2EIY/oKK8gR+AStFcG4WQ==;EndpointSuffix=core.windows.net")
        self.azure_container_name = os.getenv("CONTAINER_NAME", "blobpdfcontainer")


    