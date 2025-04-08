from flask import Flask, request, jsonify

from src.handlers import glossary_handler
from src.handlers.glossary_handler import GlossaryHandler
from src.handlers.knowledge_graph_handler import KnowledgeGraphHandler
from src.generators.answer_generator import AnswerGenerator

from src.config.config import Config
from src.config.logging_config import setup_logging

config = Config()
logger = setup_logging(config.logging_config)
answer_generator = AnswerGenerator(config, logger)
glossary_handler = GlossaryHandler(logger)

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