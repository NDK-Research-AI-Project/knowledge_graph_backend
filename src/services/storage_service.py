from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings
from werkzeug.utils import secure_filename

from src.config.config import Config
from src.config.logging_config import setup_logging
from src.services.mongo_service import MongoDBHandler
from azure.storage.blob import BlobServiceClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import hashlib
import io
from datetime import datetime
import PyPDF2

config = Config()
logger = setup_logging(config.logging_config)


class StorageService:
    def __init__(self):
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(config.azure_connection_string)
            self.container_client = self.blob_service_client.get_container_client(config.azure_container_name)
            logger.info("Successfully connected to Azure storage container")
        except Exception as e:
            logger.error(f"Failed to connect to Azure storage container: {e}")
            raise

        # Mongo config
        self.mongo_client = MongoClient(config.mongo_uri)
        self.metadata_db = self.mongo_client[config.mongo_metadata_db]
        self.metadata_collection = self.metadata_db[config.mongo_metadata_collection]

        try:
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            raise

    # def upload_pdf_and_metadata(self, file):
    #     pdf_bytes = file.read()
    #
    #     # Generate SHA-256 hash
    #     hash_object = hashlib.sha256(pdf_bytes)
    #     document_hash = hash_object.hexdigest()
    #
    #     # Check if document already exists
    #     existing = self.metadata_collection.find_one({"hash": document_hash})
    #     if existing:
    #         return {"error": "Document already uploaded"}, 409
    #
    #     # Extract metadata using PyPDF2
    #     pdf_file = io.BytesIO(pdf_bytes)
    #     pdf_reader = PyPDF2.PdfReader(pdf_file)
    #
    #     metadata = {
    #         "filename": secure_filename(file.filename),
    #         "numberOfPages": len(pdf_reader.pages),
    #         "hash": document_hash,
    #         "fileSize": len(pdf_bytes),
    #         "fileType": file.content_type,
    #         "uploadDate": datetime.now()
    #     }
    #
    #     # Upload to Azure
    #     blob_name = f"{document_hash}_{secure_filename(file.filename)}"
    #     blob_client = self.container_client.get_blob_client(blob_name)
    #     blob_client.upload_blob(pdf_bytes, overwrite=True)
    #     metadata["azureBlobUrl"] = blob_client.url
    #     metadata["azureBlobName"] = blob_name
    #
    #     # Save metadata to MongoDB
    #     inserted_id = self.metadata_collection.insert_one(metadata).inserted_id
    #     return {"documentId": str(inserted_id)}, 200

    from werkzeug.utils import secure_filename
    from datetime import datetime
    import hashlib
    import io
    import PyPDF2
    from azure.storage.blob import ContentSettings

    def upload_pdf_and_metadata(self, pdf_bytes, original_filename, content_type):
        """
        Uploads a PDF (given as bytes) to Azure Blob Storage and stores metadata in MongoDB.
        """

        # Generate SHA-256 hash to detect duplicates
        document_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Check if document already exists in MongoDB
        existing = self.metadata_collection.find_one({"hash": document_hash})
        if existing:
            return {"error": "Document already uploaded"}, 409

        # Extract metadata using PyPDF2
        pdf_stream = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_stream)

        metadata = {
            "filename": secure_filename(original_filename),
            "numberOfPages": len(pdf_reader.pages),
            "hash": document_hash,
            "fileSize": len(pdf_bytes),
            "fileType": content_type,
            "uploadDate": datetime.now()
        }

        # Upload to Azure Blob Storage
        blob_name = f"{document_hash}_{secure_filename(original_filename)}"
        blob_client = self.container_client.get_blob_client(blob_name)

        blob_client.upload_blob(
            data=io.BytesIO(pdf_bytes),
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )

        metadata["azureBlobUrl"] = blob_client.url
        metadata["azureBlobName"] = blob_name

        # Save metadata to MongoDB
        inserted_id = self.metadata_collection.insert_one(metadata).inserted_id

        return {"documentId": str(inserted_id)}, 200

    def list_documents(self):
        documents = list(self.metadata_collection.find({}, {
            '_id': 1, 'filename': 1, 'numberOfPages': 1, 'fileSize': 1,
            'fileType': 1, 'uploadDate': 1, 'azureBlobUrl': 1, 'azureBlobName': 1
        }))

        if not documents:
            return {"error": "No documents found"}, 404

        for doc in documents:
            doc['_id'] = str(doc['_id'])
            if isinstance(doc.get('uploadDate'), datetime):
                doc['uploadDate'] = doc['uploadDate'].isoformat()
            doc['downloadUrl'] = doc['azureBlobUrl']

        return {"documents": documents}, 200