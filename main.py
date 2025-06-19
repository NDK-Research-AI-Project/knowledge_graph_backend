from flask import Flask, request, jsonify
from bson import ObjectId

from io import BytesIO

from src.handlers.glossary_handler import GlossaryHandler
from src.handlers.knowledge_graph_handler import KnowledgeGraphHandler
from src.handlers.guardrail_handler import GuardrailHandler
from src.services.storage_service import StorageService
from src.generators.answer_generator import AnswerGenerator

from src.config.config import Config
from src.config.logging_config import setup_logging

from flask_cors import CORS


config = Config()
logger = setup_logging(config.logging_config)
storage_service = StorageService()
glossary_handler = GlossaryHandler()
answer_generator = AnswerGenerator(config)
guardrail_handler = GuardrailHandler(config)

app = Flask(__name__)

CORS(app)  # Enable CORS for all routes
# Initialize the KnowledgeGraphHandler
handler = KnowledgeGraphHandler(config)

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
            return jsonify({"message": "Document already exists."}), 409
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
    session_id = data.get('session_id')  # Optional session_id from frontend
    
    # If no session_id provided, create a new one using MongoDB ObjectId
    if not session_id:
        session_id = str(ObjectId())
        logger.info(f"Created new session for query: {session_id}")

    try:
        # Apply guardrail to check the safety of the user query
        is_safe, reason = guardrail_handler.is_safe_query(question)
        
        if not is_safe:
            logger.warning(f"Blocked unsafe query: {question}. Reason: {reason}")
            return jsonify({
                "error": "Your query was flagged by our safety system and cannot be processed.",
                "details": reason
            }), 403
            
        # Save user question to database
        user_message = save_chat_message(session_id, 'user', question)
        logger.info(f"Saved user question to session {session_id}")

        # Generate answer using the knowledge graph
        reponse = answer_generator.generate_answer(question)
        
        # Save LLM response to database
        assistant_message = save_chat_message(session_id, 'assistant', str(reponse["answer"]), reponse["explanation"])
        logger.info(f"Saved LLM response to session {session_id}")
        
        return jsonify({
            "answer": str(reponse["answer"]),
            "explanation": reponse["explanation"],
            "session_id": session_id  # Return session_id to frontend
        })
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        return jsonify({"error": str(e)}), 500



# Enhanced chat endpoint that uses knowledge graph for responses
@app.route('/api/chat/<string:session_id>/query', methods=['POST'])
def chat_with_knowledge_graph(session_id):
    """
    Send a question to a specific chat session and get an answer from the knowledge graph.
    This endpoint combines chat functionality with knowledge graph querying.
    """
    data = request.get_json()

    if 'question' not in data:
        return jsonify({"error": "Question field is required"}), 400
    
    question = data['question']

    try:
        # Apply guardrail to check the safety of the user query
        is_safe, reason = guardrail_handler.is_safe_query(question)
        
        if not is_safe:
            logger.warning(f"Blocked unsafe query in chat: {question}. Reason: {reason}")
            return jsonify({
                "error": "Your message was flagged by our safety system and cannot be processed.",
                "details": reason
            }), 403
        
        # Save user question to database
        user_message = save_chat_message(session_id, 'user', question)
        
        # Generate answer using the knowledge graph
        response = answer_generator.generate_answer(question)

        logger.info(f"Generated answer for session {session_id}: {response}")
        
        # Save LLM response to database
        assistant_message = save_chat_message(session_id, 'assistant', str(response["answer"]), response["explanation"])
        
        logger.info(f"Processed chat query for session {session_id}")
        
        return jsonify({
            "answer": str(response["answer"]),
            "session_id": session_id,
            "user_message": serialize_message(user_message),
            "assistant_message": serialize_message(assistant_message),
            "explanation": response["explanation"]
        }), 200
        
    except Exception as e:
        logger.error(f"Error in chat query endpoint: {e}")
        return jsonify({"error": str(e)}), 500


  

# Chat functionality setup
chat_collection = storage_service.chat_collection
datetime = storage_service.datetime

def save_chat_message(session_id, role, answer, explanation = []):
    """
    Utility function to save a chat message to the database.
    
    Args:
        session_id (str): The chat session ID
        role (str): 'user' or 'assistant'
        content (str): The message content
    
    Returns:
        dict: The saved message document
    """
    message = {
        'session_id': session_id,
        'role': role,
        'content': answer,
        'explanation': explanation,
        'timestamp': datetime.utcnow()
    }
    result = chat_collection.insert_one(message)
    message['_id'] = result.inserted_id
    return message

serialize_message = lambda msg: {
    'id': str(msg['_id']),
    'session_id': msg['session_id'],
    'role': msg['role'],
    'content': msg['content'],
    'timestamp': msg['timestamp'].isoformat() if isinstance(msg['timestamp'], datetime) else msg['timestamp'],
    'explanation': msg["explanation"]
}

# Endpoint to list chat sessions
@app.route('/api/chat/sessions', methods=['GET'])
def list_chat_sessions():
    """
    List all chat sessions with their metadata.
    This can be useful for the frontend to show a list of previous chats.
    """
    try:
        # Get unique session IDs and their latest message timestamps
        pipeline = [
            {
                '$group': {
                    '_id': '$session_id',
                    'last_message_time': {'$max': '$timestamp'},
                    'message_count': {'$sum': 1},
                    'first_user_message': {'$first': {'$cond': [{'$eq': ['$role', 'user']}, '$content', None]}},
                    'last_message': {'$last': '$content'}
                }
            },
            {
                '$sort': {'last_message_time': -1}
            },
            {
                '$limit': 50  # Limit to last 50 sessions
            }
        ]
        
        sessions = list(chat_collection.aggregate(pipeline))
        
        # Format the response
        formatted_sessions = []
        for session in sessions:
            # Generate topic suggestion from first user message or last message
            topic = generate_topic_suggestion(session.get('first_user_message') or session.get('last_message', ''))
            
            formatted_sessions.append({
                'session_id': session['_id'],
                'last_message_time': session['last_message_time'].isoformat() if isinstance(session['last_message_time'], datetime) else session['last_message_time'],
                'message_count': session['message_count'],
                'suggested_topic': topic,
                'preview': truncate_text(session.get('last_message', ''), 100)
            })
        
        return jsonify({
            'sessions': formatted_sessions,
            'total_count': len(formatted_sessions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        return jsonify({'error': f'Error listing chat sessions: {str(e)}'}), 500

def generate_topic_suggestion(message):
    """
    Generate a topic suggestion based on the message content.
    """
    if not message:
        return "New Chat"
    
    # Simple keyword-based topic generation
    message_lower = message.lower()
    
    # Define topic keywords
    topic_keywords = {
        "Technical Support": ["error", "bug", "issue", "problem", "fix", "troubleshoot"],
        "Data Analysis": ["data", "analysis", "chart", "graph", "statistics", "metrics"],
        "Knowledge Query": ["what is", "how to", "explain", "define", "meaning"],
        "Document Processing": ["pdf", "document", "file", "upload", "process"],
        "API Integration": ["api", "endpoint", "request", "response", "integration"],
        "Database": ["database", "query", "mongodb", "neo4j", "collection"],
        "Configuration": ["config", "setup", "install", "configure", "environment"]
    }
    
    # Check for keyword matches
    for topic, keywords in topic_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            return topic
    
    # Extract first few meaningful words as fallback
    words = message.split()[:3]
    if words:
        return " ".join(words).title()
    
    return "General Discussion"

def truncate_text(text, max_length=100):
    """
    Truncate text to specified length with ellipsis.
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + "..."


# Endpoint to create a new chat session
@app.route('/api/chat/create', methods=['POST'])
def create_chat_session():
    """
    Create a new chat session and return the session ID.
    The frontend can use this ID to start a new chat thread.
    """
    try:
        # Generate a unique session ID using MongoDB ObjectId
        session_id = str(ObjectId())
        
        # Optionally, you can create an initial session document in MongoDB
        # to track session metadata (creation time, etc.)
        session_metadata = {
            'session_id': session_id,
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        # Store session metadata (optional)
        # For now, we'll just return the session ID without storing metadata
        # If you want to store session metadata, uncomment the next line:
        # chat_collection.insert_one(session_metadata)
        
        logger.info(f"Created new chat session: {session_id}")
        
        return jsonify({
            'session_id': session_id,
            'message': 'Chat session created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        return jsonify({'error': f'Error creating chat session: {str(e)}'}), 500

# Endpoint to add a message to a specific chat session
@app.route('/api/chat/<string:session_id>', methods=['POST'])
def add_message(session_id):
    data = request.get_json()
    role = data.get('role')
    content = data.get('content')
    if not role or not content:
        return jsonify({'error': 'role and content are required'}), 400

    message = {
        'session_id': session_id,
        'role': role,
        'content': content,
        'timestamp': datetime.utcnow()
    }
    result = chat_collection.insert_one(message)
    message['_id'] = result.inserted_id
    return jsonify(serialize_message(message)), 201

# Endpoint to retrieve chat history for a specific session
@app.route('/api/chat/<string:session_id>', methods=['GET'])
def get_history(session_id):
    limit = int(request.args.get('limit', 100))
    skip = int(request.args.get('skip', 0))

    cursor = chat_collection.find({'session_id': session_id})\
                            .sort('timestamp', 1)\
                            .skip(skip)\
                            .limit(limit)
    messages = [serialize_message(msg) for msg in cursor]
    return jsonify(messages), 200


# Endpoint to delete chat history for a specific session
@app.route('/api/chat/<string:session_id>', methods=['DELETE'])
def delete_history(session_id):
    result = chat_collection.delete_many({'session_id': session_id})
    return jsonify({'deleted_count': result.deleted_count}), 200


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


@app.route('/api/glossary/update/<item_id>', methods=['PATCH'])
def update_glossary(item_id):
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Expected a JSON object with update data."}), 400
    try:
        result = glossary_handler.update_glossary_item(item_id, data)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error updating glossary item: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/glossary/delete/<item_id>', methods=['DELETE'])
def delete_glossary(item_id):
    try:
        result = glossary_handler.delete_glossary_item(item_id)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error deleting glossary item: {e}")
        return jsonify({"error": str(e)}), 500
  

if __name__ == "__main__":
    app.run(debug=True)