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

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        "motel": "Seahorse Inn and Cottages",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

# ============================================================================
# INCOMING CALL HANDLER
# ============================================================================

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

# ============================================================================
# HANDLE GUEST INPUT
# ============================================================================

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

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)