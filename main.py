from flask import Flask, request, jsonify
from src.handlers.knowledge_graph_handler import KnowledgeGraphHandler
from src.generators.answer_generator import AnswerGenerator
import tempfile
import os
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.config.config import Config
from src.config.logging_config import setup_logging


import hashlib
import io
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import PyPDF2
from datetime import datetime


config = Config()
logger = setup_logging(config.logging_config)
answer_generator = AnswerGenerator(config, logger)


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
# Initialize the KnowledgeGraphHandler
handler = KnowledgeGraphHandler(config, logger)

# @app.route('/api/knowledge-graph/process-document', methods=['POST'])
# def process_document():
#     # Check if a file is part of the request
#     if 'file' not in request.files:
#         logger.info({"error": "No file part"})

#     file = request.files['file']

#     # Check if the file has a valid name
#     if file.filename == '':
#         logger.info({"error": "No selected file"}), 400

#     pdf_bytes = file.read()

    # try:
    #     # # Create a temporary file to save the uploaded file
    #     # with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
    #     #     temp_file.write(file.read())
    #     #     temp_file_path = temp_file.name
        
    #     # # Step 1: Process the document and create the knowledge graph
    #     # handler.process_and_save_document(temp_file_path)
        
    #     # Remove the temporary file after processing
    #     # os.remove(temp_file_path)
    #     try:
    #         handler.process_document(pdf_bytes)
    #         return jsonify({"message": "Knowledge graph created successfully."}), 200
        
    #     except Exception as e:
    #         logger.error(f"Error while creating the knowledge graph: {e}")
    #         return jsonify({"error": f"Error while creating the knowledge graph: {str(e)}"}), 500

            

    # except Exception as e:
    #     return jsonify({"error": f"Error while creating the knowledge graph: {str(e)}"}), 500



# Configuration for Azure Blob Storage
AZURE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=researchpdfstore;AccountKey=SQnY5MvTblA+bEu7bPw3orgeZhZzvg6jNTSF4c7yWCFsdk3cwWe5pqAPgPRGdCiwr2EIY/oKK8gR+AStFcG4WQ==;EndpointSuffix=core.windows.net"
AZURE_CONTAINER_NAME = "blobpdfcontainer"

# Configuration for MongoDB
MONGO_URI = "mongodb+srv://kavindamadhuranga74:fLaa4T079luktEQv@cluster0.xkdqxqw.mongodb.net/?appName=Cluster0"
MONGO_DB_NAME = "your_ai_db"
MONGO_COLLECTION_NAME = "pdf_store"

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

# Create a new client and connect to the server
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
mongo_db = client[MONGO_DB_NAME]
mongo_collection = mongo_db[MONGO_COLLECTION_NAME]

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


@app.route('/api/knowledge-graph/process-document', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        logger.info({"error": "No file part"})
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        logger.info({"error": "No selected file"})
        return jsonify({"message": "No selected file"}), 400

    try:
        # Read PDF bytes
        pdf_bytes = file.read()

        # Generate SHA-256 hash
        hash_object = hashlib.sha256(pdf_bytes)
        document_hash = hash_object.hexdigest()

        # Check if document has been uploaded before
        existing_document = mongo_collection.find_one({"hash": document_hash})
        if existing_document:
            logger.info({"error": "Document already uploaded"})
            return jsonify({
                "message": "Upload failed, Document already uploaded"
            }), 409  # HTTP 409 Conflict

        # Create a BytesIO object for PDF processing
        pdf_file = io.BytesIO(pdf_bytes)
        
        # Extract PDF metadata with newer PyPDF2 syntax
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        metadata = {
            "filename": secure_filename(file.filename),
            "numberOfPages": len(pdf_reader.pages),
            "hash": document_hash,
            "fileSize": len(pdf_bytes),
            "fileType": file.content_type,
            "uploadDate": datetime.now()
        }

        # Upload PDF to Azure Blob Storage using a unique filename to prevent collisions
        blob_name = f"{document_hash}_{secure_filename(file.filename)}"
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(pdf_bytes, overwrite=True)
        metadata["azureBlobUrl"] = blob_client.url
        metadata["azureBlobName"] = blob_name

        # Upload metadata to MongoDB
        document_id = mongo_collection.insert_one(metadata).inserted_id

        logger.info({"message": "File and metadata uploaded successfully"})
        return jsonify({
            "message": "File uploaded successfully", 
            "documentId": str(document_id)
        }), 200

    except Exception as e:
        logger.error({"error": str(e)})
        return jsonify({"message": str(e) }), 500


@app.route('/api/documents', methods=['GET'])
def get_all_documents():
    try:
        # Retrieve all documents from MongoDB
        documents = list(mongo_collection.find({}, {'_id': 1, 'filename': 1, 'numberOfPages': 1, 
                                                'fileSize': 1,'fileType':1, 'uploadDate': 1, 
                                                'azureBlobUrl': 1, 'azureBlobName': 1}))
        
        # Check if documents are available
        if not documents:
            logger.info({"message": "No documents found in the database"})
            return jsonify({
                "message": "No documents available",
            }), 404  # Not Found status code
        
        # Format documents for JSON response
        formatted_documents = []
        for doc in documents:
            # Convert MongoDB ObjectId to string
            doc['_id'] = str(doc['_id'])
            # Convert datetime to string
            if 'uploadDate' in doc and isinstance(doc['uploadDate'], datetime):
                doc['uploadDate'] = doc['uploadDate'].isoformat()
                
            # Add download URL
            doc['downloadUrl'] = doc['azureBlobUrl']
            
            formatted_documents.append(doc)
            
        logger.info({"message": f"Retrieved {len(formatted_documents)} documents"})
        return jsonify({"documents": formatted_documents}), 200
    
    except Exception as e:
        logger.error({"error": f"Error retrieving documents: {str(e)}"})
        return jsonify({"message": f"Error retrieving documents: {str(e)}"}), 500


@app.route('/api/knowledge-graph/query', methods=['POST'])
def get_answer():
    data = request.get_json()

    if 'question' not in data:
        return jsonify({"error": "Question field is required"}), 400
    
    question = data['question']

    try:
        answer = answer_generator.generate_answer(question)
        return jsonify({"answer": str(answer)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    app.run(debug=True)