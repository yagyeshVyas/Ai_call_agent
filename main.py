import os
import logging
import traceback
from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

# Load environment variables
load_dotenv()

# ============ CONFIGURATION ============
class Config:
    MOTEL_NAME = os.getenv("MOTEL_NAME", "Seahorse Inn and Cottages")
    GREETING_TEXT = os.getenv("GREETING_TEXT", "Hello! Welcome to Seahorse Inn and Cottages. How can I help you today?")

# ============ LOGGING SETUP ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
    
    response = VoiceResponse()
    
    try:
        # 1. Basic Greeting
        response.say(Config.GREETING_TEXT, voice='alice')
        
        # 2. Gather Input with LONGER timeouts
        gather = response.gather(
            input='speech dtmf',
            timeout=10,  # Increased from 5 to 10 seconds
            speech_timeout='auto',  # Auto-detect when user stops speaking
            num_digits=1,
            action='/handle_input',
            method='POST'
        )
        gather.say("You can tell me what you need, or press 1 for reservations, 2 for questions.", voice='alice')
        
        # 3. Fallback if no input - redirect instead of hangup
        response.say("I didn't hear anything. Let me ask again.", voice='alice')
        response.redirect('/incoming_call', method='POST')
        
        logger.info("✅ TwiML generated successfully")
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Emergency Fallback
        response = VoiceResponse()
        response.say("We are currently experiencing technical difficulties. Please try again later.", voice='alice')
        
    return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/handle_input', methods=['POST'])
def handle_input():
    """Handle the user's response"""
    logger.info("📝 Handling User Input")
    logger.info(f"Form Data: {dict(request.form)}")
    
    response = VoiceResponse()
    
    try:
        speech_result = request.form.get('SpeechResult')
        digits = request.form.get('Digits')
        
        if speech_result:
            msg = f"You said: {speech_result}. Thank you, I will help you with that."
            logger.info(f"Speech: {speech_result}")
        elif digits:
            if digits == '1':
                msg = "You pressed 1 for reservations. Let me connect you to our booking system."
            elif digits == '2':
                msg = "You pressed 2 for questions. An agent will assist you shortly."
            else:
                msg = f"You pressed: {digits}."
            logger.info(f"Digits: {digits}")
        else:
            msg = "I didn't get that. Let me ask again."
            response.say(msg, voice='alice')
            response.redirect('/incoming_call', method='POST')
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        response.say(msg, voice='alice')
        response.say("Thank you for calling. Goodbye.", voice='alice')
        
    except Exception as e:
        logger.error(f"❌ Error in handle_input: {e}")
        response.say("Sorry, I had trouble understanding. Please try again.", voice='alice')
        response.redirect('/incoming_call', method='POST')
        
    return str(response), 200, {'Content-Type': 'text/xml'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)