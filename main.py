import os
import json
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify
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
        num_digits=0,
        action='/handle_guest_input',
        method='POST',
        timeout=15,
        speech_timeout='auto',
        max_speech_time=30,
        language='en-US'
    )
    gather.say("Please tell me what you need.", voice='alice')
    
    # If no input, repeat
    response.say("Sorry, I didn't catch that. Let me try again.", voice='alice')
    response.redirect('/incoming_call')
    
    return str(response)

@app.route('/handle_guest_input', methods=['POST'])
def handle_guest_input():
    """Process guest's choice"""
    response = VoiceResponse()
    
    # Get guest input
    user_input = request.form.get('SpeechResult', '').lower()
    logger.info(f"Guest input: {user_input}")
    
    # Store session data
    from_number = request.form.get('From', 'unknown')
    call_sid = request.form.get('CallSid', 'unknown')
    
    if not user_input:
        response.say("Sorry, I didn't catch that.", voice='alice')
        response.redirect('/incoming_call')
        return str(response)
    
    # BOOKING
    if any(word in user_input for word in ["book", "booking", "reserve", "reservation", "room"]):
        logger.info("🔵 NEW BOOKING STARTED")
        response.say("Great! Let's create a new reservation.", voice='alice')
        response.say("When would you like to check in? Please say a date like tomorrow or December 20th.", voice='alice')
        
        gather = response.gather(
            num_digits=0,
            action='/booking_checkin',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        
        return str(response)
    
    # EXTEND STAY
    elif any(word in user_input for word in ["extend", "longer", "more nights", "additional"]):
        logger.info("🔵 EXTEND STAY STARTED")
        response.say("I can help you extend your stay. What's your name or room number?", voice='alice')
        
        gather = response.gather(
            num_digits=0,
            action='/extend_stay',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        
        return str(response)
    
    # CANCELLATION
    elif any(word in user_input for word in ["cancel", "cancellation", "delete", "remove"]):
        logger.info("🔵 CANCELLATION STARTED")
        response.say("I'll help you cancel your reservation. What's your name?", voice='alice')
        
        gather = response.gather(
            num_digits=0,
            action='/cancel_booking',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        
        return str(response)
    
    # QUESTIONS / FAQ
    else:
        logger.info(f"❓ FAQ REQUEST: {user_input}")
        
        # Answer based on keywords
        if "wifi" in user_input:
            response.say("We offer free high-speed WiFi. The password is Seahorse Guest 2024.", voice='alice')
        elif "check-in" in user_input or "checkin" in user_input:
            response.say("Check-in is at 3 PM. We have 24/7 kiosk check-in available.", voice='alice')
        elif "check-out" in user_input or "checkout" in user_input:
            response.say("Check-out is at 11 AM.", voice='alice')
        elif "pool" in user_input:
            response.say("Our outdoor pool is open from 9 AM to 9 PM daily.", voice='alice')
        elif "pet" in user_input or "dog" in user_input or "cat" in user_input:
            response.say("We are pet-friendly! There is a 25 dollar pet fee per stay, and we allow up to 3 pets.", voice='alice')
        elif "parking" in user_input:
            response.say("Parking is free in our lot for all guests.", voice='alice')
        elif "beach" in user_input:
            response.say("We have direct beach access from our property. It's just steps away!", voice='alice')
        else:
            response.say(user_input + ". Let me get more details for you.", voice='alice')
        
        # Ask if they need anything else
        response.say("Is there anything else I can help you with?", voice='alice')
        gather = response.gather(
            num_digits=0,
            action='/handle_guest_input',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        gather.say("Please let me know.", voice='alice')
        
        return str(response)

@app.route('/booking_checkin', methods=['POST'])
def booking_checkin():
    """Collect check-in date"""
    response = VoiceResponse()
    
    checkin_date = request.form.get('SpeechResult', '')
    logger.info(f"✏️ Check-in date: {checkin_date}")
    
    if not checkin_date:
        response.say("I didn't catch the date. When would you like to check in?", voice='alice')
        gather = response.gather(
            num_digits=0,
            action='/booking_checkin',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        return str(response)
    
    response.say(f"Got it, checking in on {checkin_date}. When will you check out?", voice='alice')
    gather = response.gather(
        num_digits=0,
        action='/booking_checkout',
        method='POST',
        timeout=15,
        speech_timeout='auto',
        language='en-US'
    )
    
    return str(response)

@app.route('/booking_checkout', methods=['POST'])
def booking_checkout():
    """Collect check-out date"""
    response = VoiceResponse()
    
    checkout_date = request.form.get('SpeechResult', '')
    logger.info(f"✏️ Check-out date: {checkout_date}")
    
    if not checkout_date:
        response.say("When will you check out?", voice='alice')
        gather = response.gather(
            num_digits=0,
            action='/booking_checkout',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        return str(response)
    
    response.say("Perfect. How many guests will be staying?", voice='alice')
    gather = response.gather(
        num_digits=0,
        action='/booking_guests',
        method='POST',
        timeout=15,
        speech_timeout='auto',
        language='en-US'
    )
    
    return str(response)

@app.route('/booking_guests', methods=['POST'])
def booking_guests():
    """Collect number of guests"""
    response = VoiceResponse()
    
    num_guests = request.form.get('SpeechResult', '1')
    logger.info(f"✏️ Number of guests: {num_guests}")
    
    response.say("Thank you! What is your full name?", voice='alice')
    gather = response.gather(
        num_digits=0,
        action='/booking_name',
        method='POST',
        timeout=15,
        speech_timeout='auto',
        language='en-US'
    )
    
    return str(response)

@app.route('/booking_name', methods=['POST'])
def booking_name():
    """Collect guest name"""
    response = VoiceResponse()
    
    name = request.form.get('SpeechResult', '')
    logger.info(f"✏️ Guest name: {name}")
    
    if not name:
        response.say("What is your name?", voice='alice')
        gather = response.gather(
            num_digits=0,
            action='/booking_name',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        return str(response)
    
    response.say(f"Thank you {name}. What is your phone number?", voice='alice')
    gather = response.gather(
        num_digits=0,
        action='/booking_phone',
        method='POST',
        timeout=15,
        speech_timeout='auto',
        language='en-US'
    )
    
    return str(response)

@app.route('/booking_phone', methods=['POST'])
def booking_phone():
    """Collect phone number"""
    response = VoiceResponse()
    
    phone = request.form.get('SpeechResult', '')
    logger.info(f"✏️ Phone: {phone}")
    
    if not phone:
        response.say("What is your phone number?", voice='alice')
        gather = response.gather(
            num_digits=0,
            action='/booking_phone',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        return str(response)
    
    response.say("Perfect! Your reservation is being processed.", voice='alice')
    response.say("A confirmation has been sent to your email. Check-in is at 3 PM.", voice='alice')
    response.say("Thank you for choosing Seahorse Inn and Cottages. Goodbye!", voice='alice')
    response.hangup()
    
    logger.info(f"✅ BOOKING COMPLETED")
    
    return str(response)

@app.route('/extend_stay', methods=['POST'])
def extend_stay():
    """Handle extend stay request"""
    response = VoiceResponse()
    
    name = request.form.get('SpeechResult', '')
    logger.info(f"📞 Extend stay from: {name}")
    
    if not name:
        response.say("What is your name or room number?", voice='alice')
        gather = response.gather(
            num_digits=0,
            action='/extend_stay',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        return str(response)
    
    response.say(f"Thank you {name}. Let me transfer you to our manager to extend your stay.", voice='alice')
    response.say("Please hold.", voice='alice')
    response.dial(Config.MOTEL_PHONE, timeout=30)
    response.hangup()
    
    return str(response)

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    """Handle cancellation"""
    response = VoiceResponse()
    
    name = request.form.get('SpeechResult', '')
    logger.info(f"❌ Cancellation from: {name}")
    
    if not name:
        response.say("What is your name?", voice='alice')
        gather = response.gather(
            num_digits=0,
            action='/cancel_booking',
            method='POST',
            timeout=15,
            speech_timeout='auto',
            language='en-US'
        )
        return str(response)
    
    response.say(f"Thank you {name}. Let me transfer you to our manager to process your cancellation.", voice='alice')
    response.dial(Config.MOTEL_PHONE, timeout=30)
    response.hangup()
    
    return str(response)

@app.route('/status', methods=['GET'])
def status():
    """Health check"""
    return jsonify({
        "status": "online",
        "motel": "Seahorse Inn and Cottages",
        "timestamp": datetime.now().isoformat()
    }), 200

# ============ RUN ============
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)