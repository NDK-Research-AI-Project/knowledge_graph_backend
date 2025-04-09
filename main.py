from flask import Flask, request, jsonify

from io import BytesIO

from src.handlers.glossary_handler import GlossaryHandler
from src.handlers.knowledge_graph_handler import KnowledgeGraphHandler
from src.generators.answer_generator import AnswerGenerator
from src.services.storage_service import StorageService

from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)
answer_generator = AnswerGenerator(config, logger)
storage_service = StorageService(logger)
glossary_handler = GlossaryHandler(logger)

app = Flask(__name__)
# Initialize the KnowledgeGraphHandler
handler = KnowledgeGraphHandler(config, logger)

@app.route('/api/knowledge-graph/process-document', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.info({"error": "No selected file"})
        return jsonify({"message": "No selected file"}), 400

    try:
        pdf_bytes = file.read()
        file_stream = BytesIO(pdf_bytes)

        # First, try uploading the file
        result, status = storage_service.upload_pdf_and_metadata(
            pdf_bytes=pdf_bytes,
            original_filename=file.filename,
            content_type=file.content_type
        )

        if status == 409:
            logger.info({"message": "File already exists."})
        else:
            logger.info({"message": "File uploaded successfully."})

        # Process knowledge graph regardless of upload status
        handler.process_document(pdf_bytes)

        logger.info({"message": "Knowledge graph created successfully."})

        # Return appropriate message
        if status == 409:
            return jsonify({"message": "Document already exists."}), 200
        else:
            return jsonify(result), status

    except Exception as e:
        logger.error(f"Error while creating the knowledge graph: {e}")
        return jsonify({"error": f"Error while creating the knowledge graph: {str(e)}"}), 500


@app.route('/api/documents', methods=['GET'])
def get_all_documents():
    try:
        result, status = storage_service.list_documents()
        return jsonify(result), status
    except Exception as e:
        logger.error({"error": str(e)})
        return jsonify({"message": str(e)}), 500

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



# New endpoint: add glossary items
@app.route('/api/glossary/add', methods=['POST'])
def add_glossary():
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Expected a list of glossary items."}), 400
    try:
        result = glossary_handler.add_glossary_items(data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error adding glossary items: {e}")
        return jsonify({"error": str(e)}), 500


# New endpoint: get all glossary items
@app.route('/api/glossary/list', methods=['GET'])
def list_glossary():
    try:
        items = glossary_handler.get_all_glossary_items()
        return jsonify(items), 200
    except Exception as e:
        logger.error(f"Error retrieving glossary items: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)