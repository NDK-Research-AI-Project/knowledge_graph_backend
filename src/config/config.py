import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration class for the knowledge-graph-backend application
    
    This class manages all configuration parameters, loading them from environment
    variables with fallback to default values
    """
    # NEO4J_URI = os.getenv("NEO4J_URI","neo4j+s://c95a3680.databases.neo4j.io")
    # NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    # NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "5SYecqiUcLZz4pzO9CDdGs9jlU5rOKUQ6ddtK6DEl1o")

    
    # DEEPINFRA_API_TOKEN = os.getenv("DEEPINFRA_API_TOKEN", "YuGM4YMWqQU4kVM0u47Ntev9gUjFv2Om")
    # GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
    
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://c95a3680.databases.neo4j.io")
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "5SYecqiUcLZz4pzO9CDdGs9jlU5rOKUQ6ddtK6DEl1o")
        
        self.deepinfra_api_token = os.getenv("DEEPINFRA_API_TOKEN", "YuGM4YMWqQU4kVM0u47Ntev9gUjFv2Om")

        self.groq_api_key = os.getenv("GROQ_API_KEY", "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")
        
        self.chat_template = os.getenv("CHAT_TEMPLATE", """Answer the question based only on the following context:
        Context: {context}

        Glossary (for understanding and referring to same meanings only, not for direct inclusion in the answer): {glossary}

        Question: {question}

        Follow these instructions when when giving the response:

        1. Use the glossary definitions to understand the unknown terms in context and question.
        2. Do not include the glossary definitions directly in your answer.
        3. If the glossary is empty or does not contain relevant definitions for words you don't know in question, ignore it..
        4. do not answer the question using your general knowledge.
        5. If the question is not clear even after considering the glossary definitions, respond with: "I'm sorry, I didn't understand your question. Could you please rephrase it?"
        6. Provide only the response, do not explain about how you get the answer
        7. no need to add everything in the context to the response. just get the required infurmation only. sometimes context will include additional informations which is not relevent to the final answer

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
    