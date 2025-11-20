import os
import logging
import traceback
from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from conversational_ai import ConversationalAI

# Load environment variables
load_dotenv()

# ============ LOGGING SETUP ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============
class Config:
    MOTEL_NAME = os.getenv("MOTEL_NAME", "Seahorse Inn and Cottages")
    GREETING_TEXT = os.getenv("GREETING_TEXT", "Hello! Welcome to Seahorse Inn and Cottages. I'm your AI assistant. How can I help you today?")

app = Flask(__name__)

# Initialize Conversational AI
ai = ConversationalAI()

# ============ ROUTES ============

@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check to verify the app is running on Render"""
    return "Seahorse AI Agent is Online 🐴", 200

@app.route('/incoming_call', methods=['POST'])
def incoming_call():
    """Handle incoming call from Twilio"""
    logger.info("=" * 60)
    logger.info("📞 INCOMING CALL RECEIVED")
    logger.info("=" * 60)
    
    # Log all request data for debugging
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Form Data: {dict(request.form)}")
    
    # Get unique call identifier
    call_sid = request.form.get('CallSid', 'unknown')
    
    response = VoiceResponse()
    
    try:
        # Greeting
        response.say(Config.GREETING_TEXT, voice='alice')
        
        # Start conversational gathering
        gather = response.gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action='/handle_conversation',
            method='POST'
        )
        gather.say("I'm listening...", voice='alice')
        
        # Fallback if no input
        response.say("I didn't hear anything. Let me ask again.", voice='alice')
        response.redirect('/incoming_call', method='POST')
        
        logger.info("✅ Initial TwiML generated")
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        
        response = VoiceResponse()
        response.say("We are currently experiencing technical difficulties. Please try again later.", voice='alice')
        
    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/handle_conversation', methods=['POST'])
def handle_conversation():
    """Handle conversational turns with AI"""
    logger.info("💬 Handling Conversation Turn")
    logger.info(f"Form Data: {dict(request.form)}")
    
    response = VoiceResponse()
    
    try:
        # Get call identifier for context tracking
        call_sid = request.form.get('CallSid', 'unknown')
        
        # Get what user said
        speech_result = request.form.get('SpeechResult', '')
        
        if not speech_result:
            # No speech detected
            response.say("I didn't catch that. Could you say that again?", voice='alice')
            response.redirect('/incoming_call', method='POST')
            return str(response), 200, {'Content-Type': 'text/xml'}
        
       # Get AI response
        ai_result = ai.chat(call_sid, speech_result)
        
        # Speak AI's response
        response.say(ai_result['response'], voice='alice')
        
        # Check if call should end
        if ai_result['should_end_call']:
            logger.info(f"👋 Call ending gracefully for {call_sid}")
            response.say("Goodbye!", voice='alice')
            response.hangup()
            
            # Clean up conversation memory
            ai.clear_conversation(call_sid)
        else:
            # Continue conversation
            gather = response.gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action='/handle_conversation',
                method='POST'
            )
            gather.pause(length=1)  # Brief pause for natural feel
            
            # Fallback if they don't say anything
            response.say("Are you still there? If you need anything else, just let me know.", voice='alice')
            response.redirect('/handle_conversation', method='POST')
        
    except Exception as e:
        logger.error(f"❌ Error in conversation: {e}")
        logger.error(traceback.format_exc())
        response.say("Sorry, I had trouble understanding. Let me start over.", voice='alice')
        response.redirect('/incoming_call', method='POST')
        
    return str(response), 200, {'Content-Type': 'text/xml'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting Seahorse AI Agent on port {port}")
    app.run(host='0.0.0.0', port=port)