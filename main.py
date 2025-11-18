import os
import json
import threading
import traceback
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)

class Config:
    """Configuration"""
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

logger.info("🐴 Seahorse AI Agent Initialized (Twilio Voice)")

@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        "motel": "Seahorse Inn and Cottages",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route('/test_twiml', methods=['GET', 'POST'])
def test_twiml():
    """Minimal TwiML test - no fancy stuff"""
    logger.info("🧪 TEST ENDPOINT CALLED")
    
    response_str = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello from Seahorse Inn. This is a test.</Say>
    <Hangup/>
</Response>'''
    
    logger.info(f"Returning: {response_str}")
    return response_str, 200, {'Content-Type': 'text/xml'}

@app.route('/incoming_call', methods=['POST'])
def incoming_call():
    """Handle incoming call from Twilio"""
    logger.info("=" * 60)
    logger.info("📞 INCOMING CALL RECEIVED")
    logger.info("=" * 60)
    
    try:
        # Log request details
        logger.info(f"From: {request.form.get('From', 'Unknown')}")
        logger.info(f"To: {request.form.get('To', 'Unknown')}")
        logger.info(f"CallSid: {request.form.get('CallSid', 'Unknown')}")
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Add greeting
        greeting_text = "Hello! Welcome to Seahorse Inn and Cottages. You can book a room, extend your stay, or ask about our amenities. What can I help you with today?"
        logger.info(f"Playing greeting: {greeting_text[:50]}...")
        response.say(greeting_text, voice='alice')
        
        # Add gather for speech input
        logger.info("Adding gather for speech input...")
        gather = response.gather(
            num_digits=0,
            action='/handle_guest_input',
            method='POST',
            timeout=10,
            speech_timeout='auto',
            language='en-US'
        )
        gather.say("Please tell me what you need.", voice='alice')
        
        # Fallback if no input
        response.say("Sorry, I didn't catch that. Let me try again.", voice='alice')
        response.redirect('/incoming_call')
        
        # Convert to string
        twiml_str = str(response)
        logger.info("✅ TwiML response created successfully")
        logger.info(f"TwiML Preview: {twiml_str[:150]}...")
        
        # Return with correct content type
        return twiml_str, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ERROR IN INCOMING_CALL: {str(e)}")
        logger.error("=" * 60)
        logger.error(traceback.format_exc())
        
        # Return error response (still valid TwiML)
        response = VoiceResponse()
        response.say("Sorry, there was a system error. Please try again later.", voice='alice')
        
        return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/handle_guest_input', methods=['POST'])
def handle_guest_input():
    """Handle guest input from gather"""
    logger.info("=" * 60)
    logger.info("📝 HANDLING GUEST INPUT")
    logger.info("=" * 60)
    
    try:
        speech_result = request.form.get('SpeechResult', 'No input')
        logger.info(f"Guest said: {speech_result}")
        
        response = VoiceResponse()
        
        # Simple response
        response.say(f"You said: {speech_result}", voice='alice')
        response.say("Thank you for calling. Goodbye.", voice='alice')
        response.hangup()
        
        logger.info("✅ Response sent")
        return str(response), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        
        response = VoiceResponse()
        response.say("Error processing your request.", voice='alice')
        response.hangup()
        
        return str(response), 200, {'Content-Type': 'text/xml'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)