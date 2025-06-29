from flask import session, request, jsonify, current_app
from flask_login import login_required
from app.chatbot import chatbot_bp
from llama_index.core.llms import ChatMessage, MessageRole


@chatbot_bp.route('/chatbot', methods=['POST'])
@login_required
def handle_chat():
    """
    Handles chat messages from the user, gets a response from the AI,
    and manages the conversation history in the user's Flask session.
    """
    # Get the chat engine from the application context
    chat_engine = current_app.query_engine
    if not chat_engine:
        return jsonify({'error': 'AI services are currently unavailable.'}), 503

    # Validate user input
    data = request.get_json()
    if not data or not (user_msg := data.get('message', '').strip()):
        return jsonify({'error': 'A non-empty message is required.'}), 400

    # Load this user's specific chat history from their Flask session - The history is stored as a list of dictionaries, so we convert it to ChatMessage objects
    raw_history = session.get('chat_history', [])
    chat_history = [ChatMessage(role=MessageRole(msg['role']), content=msg['content']) for msg in raw_history]

    # Get a response from the AI chat engine, providing the history
    try:
        # Pass the user's message and their specific history to the engine
        response = chat_engine.chat(user_msg, chat_history=chat_history)
        ai_answer = str(response)

        # Update the session history with the new messages
        raw_history.append({"role": "user", "content": user_msg})
        # Add the latest AI response
        raw_history.append({"role": "assistant", "content": ai_answer})
        
        # Trim the history to the last 10 turns (20 messages) to prevent it from getting too large
        session['chat_history'] = raw_history[-20:]

    except Exception as e:
        print(f"Error querying the AI model: {e}")
        return jsonify({'error': 'An error occurred while communicating with the AI.'}), 500

    return jsonify({'response': ai_answer})