import os
import json
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import logging
import re

# ============ LOGGING SETUP ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('seahorse_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# ============ CONFIGURATION ============
class Config:
    MOTEL_NAME = "Seahorse Inn and Cottages"
    MOTEL_PHONE = "252-441-5242"
    MOTEL_ADDRESS = "7218 S Virginia Dare Trail, Nags Head, NC 27959"
    
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OWNER_PHONE = os.getenv("OWNER_PHONE", "+1-252-441-5242")
    OWNER_EMAIL = os.getenv("OWNER_EMAIL", "owner@seahorseinn.com")

# ============ MOTEL DATABASE ============
MOTEL_INFO = {
    "property": {
        "name": "Seahorse Inn and Cottages",
        "address": "7218 S Virginia Dare Trail, Nags Head, NC 27959",
        "phone": "252-441-5242",
        "website": "www.seahorseinn.com",
        "email": "reservations@seahorseinn.com"
    },
    "policies": {
        "check_in": "3:00 PM",
        "check_out": "11:00 AM",
        "pet_fee": 25,
        "max_pets": 3,
        "smoking": "Outdoor areas only",
        "parking": "Free",
        "wifi": "Free high-speed WiFi"
    },
    "amenities": [
        "Free WiFi",
        "24/7 Kiosk Check-in",
        "Pet-friendly rooms",
        "Outdoor pools",
        "Beach access"
    ]
}

# ============ FLASK APP ============
app = Flask(__name__)
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

class SeahorseAIAgent:
    def __init__(self):
        self.config = Config()
        self.guest_sessions = {}
        logger.info("🐴 Seahorse AI Agent Initialized (Twilio Voice)")
    
    def get_greeting(self):
        return (
            "Hello! Welcome to Seahorse Inn and Cottages. "
            "You can book a room, extend your stay, or ask about our amenities. "
            "What can I help you with today?"
        )
    
    @staticmethod
    def parse_date(date_str):
        """Parse natural language dates"""
        date_str = date_str.lower()
        today = datetime.now().date()
        
        if "today" in date_str:
            return today.strftime("%m/%d/%Y")
        elif "tomorrow" in date_str:
            return (today + timedelta(days=1)).strftime("%m/%d/%Y")
        else:
            numbers = re.findall(r'\d+', date_str)
            if len(numbers) >= 2:
                month, day = numbers[0], numbers[1]
                year = datetime.now().year
                return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
        return today.strftime("%m/%d/%Y")

agent = SeahorseAIAgent()

# ============ TWILIO WEBHOOK ============
@app.route('/incoming_call', methods=['POST'])
def incoming_call():
    """Handle incoming call from Twilio"""
    logger.info("📞 Incoming call received")
    
    response = VoiceResponse()
    
    # Play greeting
    response.say(agent.get_greeting(), voice='alice')
    
    # Gather guest input (Twilio Speech Recognition)
    gather = response.gather(
        num_digits=1,
        action='/handle_guest_input',
        method='POST',
        timeout=10,
        speech_timeout='auto',
        speech_model='numbers_and_commands'
    )
    gather.say("Press 1 for new booking, 2 to extend stay, 3 for cancellation, or 4 for questions.", voice='alice')
    
    return str(response)

@app.route('/handle_guest_input', methods=['POST'])
def handle_guest_input():
    """Process guest's choice"""
    response = VoiceResponse()
    
    # Get guest input
    user_input = request.form.get('SpeechResult', '').lower()
    logger.info(f"Guest input: {user_input}")
    
    if "booking" in user_input or "book" in user_input or "reserve" in user_input:
        response.say("Great! Let's create a new reservation. When would you like to check in?", voice='alice')
        gather = response.gather(
            num_digits=1,
            action='/booking_checkin',
            method='POST',
            timeout=10,
            speech_timeout='auto'
        )
        return str(response)
    
    elif "extend" in user_input or "stay" in user_input:
        response.say("I can help you extend your stay. What's your name or room number?", voice='alice')
        gather = response.gather(
            action='/extend_stay',
            method='POST',
            timeout=10,
            speech_timeout='auto'
        )
        return str(response)
    
    elif "cancel" in user_input:
        response.say("I'll help you cancel your reservation. What's your name?", voice='alice')
        gather = response.gather(
            action='/cancel_booking',
            method='POST',
            timeout=10,
            speech_timeout='auto'
        )
        return str(response)
    
    else:
        # FAQ or transfer
        response.say("Let me answer your question. For more details, I'll transfer you to our team.", voice='alice')
        response.dial(Config.MOTEL_PHONE)
    
    return str(response)

@app.route('/booking_checkin', methods=['POST'])
def booking_checkin():
    """Collect check-in date"""
    response = VoiceResponse()
    
    checkin_date = request.form.get('SpeechResult', '')
    logger.info(f"Check-in date: {checkin_date}")
    
    response.say(f"Got it, checking in on {checkin_date}. When will you check out?", voice='alice')
    gather = response.gather(
        action='/booking_checkout',
        method='POST',
        timeout=10,
        speech_timeout='auto'
    )
    return str(response)

@app.route('/booking_checkout', methods=['POST'])
def booking_checkout():
    """Collect check-out date"""
    response = VoiceResponse()
    
    checkout_date = request.form.get('SpeechResult', '')
    logger.info(f"Check-out date: {checkout_date}")
    
    response.say("Perfect. How many guests will be staying?", voice='alice')
    gather = response.gather(
        action='/booking_guests',
        method='POST',
        timeout=10,
        speech_timeout='auto'
    )
    return str(response)

@app.route('/booking_guests', methods=['POST'])
def booking_guests():
    """Collect number of guests"""
    response = VoiceResponse()
    
    num_guests = request.form.get('SpeechResult', '1')
    logger.info(f"Number of guests: {num_guests}")
    
    response.say("Thank you. I'm collecting your information. Let me transfer you to our team to complete the booking.", voice='alice')
    response.dial(Config.MOTEL_PHONE)
    
    return str(response)

@app.route('/extend_stay', methods=['POST'])
def extend_stay():
    """Handle extend stay request"""
    response = VoiceResponse()
    
    name = request.form.get('SpeechResult', '')
    logger.info(f"Guest name: {name}")
    
    response.say(f"Thank you {name}. I'm transferring you to our manager to extend your stay.", voice='alice')
    response.dial(Config.MOTEL_PHONE)
    
    return str(response)

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    """Handle cancellation"""
    response = VoiceResponse()
    
    name = request.form.get('SpeechResult', '')
    logger.info(f"Cancellation request from: {name}")
    
    response.say(f"Thank you {name}. I'm transferring you to our manager to process your cancellation.", voice='alice')
    response.dial(Config.MOTEL_PHONE)
    
    return str(response)

@app.route('/status', methods=['GET'])
def status():
    """Health check"""
    from flask import jsonify
    return jsonify({
        "status": "online",
        "motel": "Seahorse Inn and Cottages"
    }), 200

# ============ RUN ============
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)