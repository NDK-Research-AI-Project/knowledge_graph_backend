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
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://9d3d116e.databases.neo4j.io")
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "MTmhQ8kiaRqRltgDThU_4hYE-aCCpIVk5aNmcUnKWKU")

        # self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://c95a3680.databases.neo4j.io")
        # self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        # self.neo4j_password = os.getenv("NEO4J_PASSWORD", "5SYecqiUcLZz4pzO9CDdGs9jlU5rOKUQ6ddtK6DEl1o")

        self.deepinfra_api_token = os.getenv("DEEPINFRA_API_TOKEN", "YuGM4YMWqQU4kVM0u47Ntev9gUjFv2Om")

        self.groq_api_key = os.getenv("GROQ_API_KEY", "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")

        #self.chat_template = os.getenv("CHAT_TEMPLATE", """Answer the question based only on the following context:        
        self.chat_template = os.getenv("CHAT_TEMPLATE", 
        """
        You are an expert assistant specialized in answering clinical research questions using only the given information.                         
        
        Context: {context}

        Glossary (for interpreting terms only—not to be quoted):  
        {glossary}

        User Question: {question}

        Instructions:
        1. If the user's message is a greeting (like "Hi", "Hello", "Hey", etc.) or general conversation starter, respond in a friendly way and briefly explain what you can help with. For example: "Hello! I'm your clinical research assistant. I can help answer questions based on the information in my knowledge base. What would you like to know about?"
        2. Understand the question and context using the glossary definitions—do not copy or repeat glossary content in the answer.
        3. Answer strictly using information from the context. Do not rely on external or general medical knowledge.
        4. If the glossary is empty or not useful, proceed with context alone.
        5. If the question is ambiguous or unclear after applying glossary help, respond with:
        "I'm sorry, I didn't understand your question. Could you please rephrase it?"
        6. Provide a clear and concise answer. Avoid explanations, reasoning steps, or rephrasing the question.
        7. Only include relevant facts from the context. Disregard unrelated information.

        Answer:""")

        # self.chat_template = os.getenv("CHAT_TEMPLATE", """Answer the question based only on the following context:

        # Context: {context}

        # Glossary (use for understanding terms in the question and context): 
        # {glossary}

        # Question: {question}

        # Instructions:
        # 1. If a term in the question is similar to a term in the glossary (even if misspelled), treat the term as referring to the correct glossary term.
        # 2. For example, if "Ashaliy" appears in the question and "Ashalia" is in the glossary, interpret "Ashaliy" as "Ashalia" in your answer.
        # 3. Use glossary definitions to understand terms in the question and context.
        # 4. Do not copy glossary definitions directly into the answer.
        # 5. If the glossary is empty or irrelevant, ignore it.
        # 6. Do not answer based on your own general knowledge—only use the provided context and glossary.
        # 7. If the question is unclear even after applying glossary info, say: "I'm sorry, I didn't understand your question. Could you please rephrase it?"
        # 8. Give a direct answer only—no explanations of reasoning.
        # 9. Use only necessary info from context—ignore unrelated parts.

        # Answer:""")

        # Logging configuration
        self.logging_config = {
            'logstash_host': os.getenv('LOGSTASH_HOST', 'localhost'),
            'logstash_port': int(os.getenv('LOGSTASH_PORT', '5044')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'app_name': 'document-summarizer'
        }
        
        # LLM configurations
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.deepinfra_model = os.getenv("DEEPINFRA_MODEL", "google/gemma-3-12b-it")
        # self.groq_temperature = os.getenv("GROQ_TEMPERATURE", "0")


        # MongoDB
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://kavindamadhuranga74:fLaa4T079luktEQv@cluster0.xkdqxqw.mongodb.net/?appName=Cluster0")
        # self.mongo_glossary_db = os.getenv("GlossaryDB", "your_ai_db")
        # self.mongo_glossary_collection = os.getenv("GlossaryCollection", "pdf_store")       
        self.mongo_glossary_db = os.getenv("GlossaryDB", "glossary_database")
        self.mongo_glossary_collection = os.getenv("GlossaryCollection", "glossary_collection")

        self.mongo_metadata_db = os.getenv("METADATA_DB", "your_ai_db")
        self.mongo_metadata_collection = os.getenv("METADATA_COLLECTION", "pdf_store")

        # Chat configuration
        self.mongo_chat_db = os.getenv("CHAT_DB", "your_ai_db")
        self.mongo_chat_collection = os.getenv("CHAT_COLLECTION", "chat_sessions")

        # Azure
        self.azure_connection_string = os.getenv("AZURE_CONNECTION_STRING", "DefaultEndpointsProtocol=https;AccountName=researchpdfstore;AccountKey=SQnY5MvTblA+bEu7bPw3orgeZhZzvg6jNTSF4c7yWCFsdk3cwWe5pqAPgPRGdCiwr2EIY/oKK8gR+AStFcG4WQ==;EndpointSuffix=core.windows.net")
        self.azure_container_name = os.getenv("CONTAINER_NAME", "blobpdfcontainer")


    