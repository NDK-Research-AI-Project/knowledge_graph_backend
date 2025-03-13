from flask import Flask, request, jsonify
from src.handlers.knowledge_graph_handler import KnowledgeGraphHandler
from src.generators.answer_generator import AnswerGenerator
import tempfile
import os

from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)
answer_generator = AnswerGenerator(config, logger)


app = Flask(__name__)
# Initialize the KnowledgeGraphHandler
handler = KnowledgeGraphHandler(config, logger)

@app.route('/api/knowledge-graph/process-document', methods=['POST'])
def process_document():
    # Check if a file is part of the request
    if 'file' not in request.files:
        logger.info({"error": "No file part"})

    file = request.files['file']

    # Check if the file has a valid name
    if file.filename == '':
        logger.info({"error": "No selected file"}), 400

    pdf_bytes = file.read()

    try:
        # # Create a temporary file to save the uploaded file
        # with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        #     temp_file.write(file.read())
        #     temp_file_path = temp_file.name
        
        # # Step 1: Process the document and create the knowledge graph
        # handler.process_and_save_document(temp_file_path)
        
        # Remove the temporary file after processing
        # os.remove(temp_file_path)
        try:
            handler.process_document(pdf_bytes)
            return jsonify({"message": "Knowledge graph created successfully."}), 200
        
        except Exception as e:
            logger.error(f"Error while creating the knowledge graph: {e}")
            return jsonify({"error": f"Error while creating the knowledge graph: {str(e)}"}), 500

            

    except Exception as e:
        return jsonify({"error": f"Error while creating the knowledge graph: {str(e)}"}), 500


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