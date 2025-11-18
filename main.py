import os
import sys
import threading
import time
import json
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import asyncio
import logging

# ============ IMPORTS ============
from speech_recognition import SpeechRecognizer
from text_to_speech import TextToSpeech
from ai_brain import AIBrain
from skytouch_automation import SkyTouchAgent
from call_handler import CallManager
from sms_email import NotificationService

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
    
    CHECKIN_TIME = "3:00 PM"
    CHECKOUT_TIME = "11:00 AM"
    
    # SkyTouch Credentials
    SKYTOUCH_URL = "https://www.skytouch.com"
    SKYTOUCH_USERNAME = os.getenv("SKYTOUCH_USERNAME")
    SKYTOUCH_PASSWORD = os.getenv("SKYTOUCH_PASSWORD")
    
    # Notifications
    OWNER_PHONE = os.getenv("OWNER_PHONE", "+1-252-441-5242")
    OWNER_EMAIL = os.getenv("OWNER_EMAIL", "owner@seahorseinn.com")
    
    # OpenAI (Free tier)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Twilio (optional, for SMS)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE")

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
        "min_age": 21,
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
        "Beach access",
        "Coffee maker in rooms",
        "Flat-screen TV",
        "Air conditioning"
    ],
    "faqs": {
        "wifi_password": "SeahorseGuest2024!",
        "kiosk_code": "See envelope upon arrival",
        "pool_hours": "9 AM - 9 PM",
        "ice_machine": "On every floor",
        "parking": "Free parking in lot"
    }
}

# ============ MAIN APP ============
app = Flask(__name__)

class SeahorseAIAgent:
    def __init__(self):
        self.config = Config()
        self.stt = SpeechRecognizer()
        self.tts = TextToSpeech()
        self.ai_brain = AIBrain(api_key=self.config.OPENAI_API_KEY)
        self.skytouch = SkyTouchAgent(
            username=self.config.SKYTOUCH_USERNAME,
            password=self.config.SKYTOUCH_PASSWORD
        )
        self.notifications = NotificationService(self.config)
        self.call_manager = CallManager()
        self.active_calls = {}
        logger.info("🐴 Seahorse AI Agent Initialized")
    
    def handle_incoming_call(self, call_id, caller_number):
        """Main call handling logic"""
        logger.info(f"📞 Incoming call: {caller_number}")
        
        # Greeting
        greeting = self.tts.synthesize(
            "Hello! Welcome to Seahorse Inn and Cottages. "
            "How can I help you today? You can book a room, extend your stay, "
            "cancel a reservation, or ask about our amenities."
        )
        self.call_manager.play_audio(greeting)
        
        # Listen to guest
        user_input = self.stt.listen(timeout=10)
        logger.info(f"Guest said: {user_input}")
        
        if not user_input:
            self.tts.synthesize(
                "Sorry, I didn't catch that. Let me transfer you to our manager."
            )
            self.call_manager.transfer_to_agent(call_id)
            return
        
        # AI Brain processes intent
        intent = self.ai_brain.detect_intent(user_input)
        logger.info(f"Intent detected: {intent}")
        
        # Handle based on intent
        if intent == "NEW_BOOKING":
            self.handle_new_booking(call_id, user_input)
        
        elif intent == "EXTEND_STAY":
            self.handle_extend_stay(call_id)
        
        elif intent == "CANCEL":
            self.handle_cancellation(call_id)
        
        elif intent == "FAQ":
            self.handle_faq(call_id, user_input)
        
        else:
            self.transfer_to_agent(call_id)
    
    def handle_new_booking(self, call_id, context=""):
        """Fully automated new reservation"""
        logger.info("🔵 NEW BOOKING PROCESS STARTED")
        
        guest_info = {}
        
        # Collect check-in date
        self.tts.synthesize("What is your check-in date? Please say MMDD or today, tomorrow, or a specific date.")
        check_in = self.stt.listen(timeout=8)
        guest_info['check_in'] = self.parse_date(check_in)
        
        # Collect check-out date
        self.tts.synthesize(f"And your check-out date? That would be after {guest_info['check_in']}.")
        check_out = self.stt.listen(timeout=8)
        guest_info['check_out'] = self.parse_date(check_out)
        
        # Collect number of guests
        self.tts.synthesize("How many guests will be staying?")
        num_guests = self.stt.listen(timeout=8)
        guest_info['guests'] = self.extract_number(num_guests)
        
        # Collect full name
        self.tts.synthesize("What is the guest's full name?")
        name = self.stt.listen(timeout=8)
        guest_info['name'] = name.title()
        
        # Collect phone number
        self.tts.synthesize("And your phone number? Please spell it out.")
        phone = self.stt.listen(timeout=8)
        guest_info['phone'] = self.extract_phone(phone)
        
        # Collect email
        self.tts.synthesize("And your email address?")
        email = self.stt.listen(timeout=8)
        guest_info['email'] = email.lower()
        
        # Confirm details
        confirmation_text = (
            f"Perfect! I have you down for: "
            f"{guest_info['name']}, "
            f"checking in {guest_info['check_in']}, "
            f"checking out {guest_info['check_out']}, "
            f"{guest_info['guests']} guests. "
            f"Phone: {guest_info['phone']}, "
            f"Email: {guest_info['email']}. "
            f"Is this correct?"
        )
        self.tts.synthesize(confirmation_text)
        
        confirm = self.stt.listen(timeout=5)
        
        if "yes" in confirm.lower() or "correct" in confirm.lower():
            # ✅ AUTOMATE SKYTOUCH BOOKING
            logger.info(f"✅ Booking guest: {guest_info['name']}")
            
            booking_result = self.skytouch.create_reservation(
                name=guest_info['name'],
                phone=guest_info['phone'],
                email=guest_info['email'],
                check_in=guest_info['check_in'],
                check_out=guest_info['check_out'],
                num_guests=guest_info['guests']
            )
            
            if booking_result['success']:
                confirmation_number = booking_result['confirmation_id']
                
                self.tts.synthesize(
                    f"Excellent! Your reservation is confirmed! "
                    f"Your confirmation number is {confirmation_number}. "
                    f"Check-in is at 3 PM. A copy has been sent to {guest_info['email']}. "
                    f"Thank you for choosing Seahorse Inn!"
                )
                
                # Send notification to owner
                self.notifications.send_sms(
                    f"✅ NEW BOOKING: {guest_info['name']} | "
                    f"Conf: {confirmation_number} | "
                    f"Dates: {guest_info['check_in']} to {guest_info['check_out']} | "
                    f"Phone: {guest_info['phone']}"
                )
                
                self.notifications.send_email(
                    subject=f"New Reservation: {guest_info['name']}",
                    body=f"Booking Details:\n{json.dumps(guest_info, indent=2)}\n\n"
                         f"Confirmation: {confirmation_number}"
                )
                
                logger.info("✅ Booking completed successfully")
                self.call_manager.end_call(call_id)
            
            else:
                self.tts.synthesize(
                    "I had trouble creating your reservation. "
                    "Let me transfer you to our manager to complete this."
                )
                self.transfer_to_agent(call_id)
        
        else:
            self.tts.synthesize("Let's try again. What are your check-in dates?")
            self.handle_new_booking(call_id)
    
    def handle_extend_stay(self, call_id):
        """Extend existing reservation"""
        logger.info("🔵 EXTEND STAY PROCESS STARTED")
        
        self.tts.synthesize("I can help you extend your stay! What's your name or room number?")
        guest_id = self.stt.listen(timeout=8)
        
        # Search in SkyTouch
        reservation = self.skytouch.search_reservation(guest_id)
        
        if not reservation:
            self.tts.synthesize("I couldn't find that reservation. Let me transfer you to our team.")
            self.transfer_to_agent(call_id)
            return
        
        # Ask for new checkout
        self.tts.synthesize(
            f"I found your reservation for {reservation['guest_name']}. "
            f"You're currently checking out on {reservation['checkout_date']}. "
            f"What would you like your new checkout date to be?"
        )
        new_checkout = self.stt.listen(timeout=8)
        new_checkout_date = self.parse_date(new_checkout)
        
        # Update in SkyTouch
        update_result = self.skytouch.update_checkout(
            reservation_id=reservation['id'],
            new_checkout=new_checkout_date
        )
        
        if update_result['success']:
            self.tts.synthesize(
                f"Perfect! Your checkout has been extended to {new_checkout_date}. "
                f"An updated confirmation has been sent to your email. "
                f"Thank you!"
            )
            
            self.notifications.send_sms(
                f"📅 EXTENSION: {reservation['guest_name']} | "
                f"New checkout: {new_checkout_date}"
            )
            
            logger.info("✅ Extension completed")
            self.call_manager.end_call(call_id)
        else:
            self.tts.synthesize("I had trouble updating your reservation. Let me get our manager.")
            self.transfer_to_agent(call_id)
    
    def handle_cancellation(self, call_id):
        """Collect cancellation details"""
        logger.info("🔵 CANCELLATION PROCESS STARTED")
        
        cancel_info = {}
        
        self.tts.synthesize("I'll help you cancel your reservation. What's your name?")
        cancel_info['name'] = self.stt.listen(timeout=8).title()
        
        self.tts.synthesize("What was your check-in date?")
        cancel_info['check_in'] = self.parse_date(self.stt.listen(timeout=8))
        
        self.tts.synthesize("And your check-out date?")
        cancel_info['check_out'] = self.parse_date(self.stt.listen(timeout=8))
        
        self.tts.synthesize("Your phone number?")
        cancel_info['phone'] = self.extract_phone(self.stt.listen(timeout=8))
        
        self.tts.synthesize("Why are you canceling today?")
        cancel_info['reason'] = self.stt.listen(timeout=8)
        
        # Confirmation
        self.tts.synthesize(
            f"Just to confirm, {cancel_info['name']}, "
            f"you want to cancel the reservation from {cancel_info['check_in']} to {cancel_info['check_out']}. "
            f"Is that right?"
        )
        
        confirm = self.stt.listen(timeout=5)
        
        if "yes" in confirm.lower():
            # Send to owner
            self.notifications.send_sms(
                f"❌ CANCELLATION REQUEST: {cancel_info['name']} | "
                f"Dates: {cancel_info['check_in']} - {cancel_info['check_out']} | "
                f"Phone: {cancel_info['phone']} | "
                f"Reason: {cancel_info['reason']}"
            )
            
            self.notifications.send_email(
                subject=f"Cancellation Request: {cancel_info['name']}",
                body=f"Cancellation Details:\n{json.dumps(cancel_info, indent=2)}"
            )
            
            self.tts.synthesize(
                "Your cancellation request has been received. "
                "Our manager will contact you shortly. "
                "Thank you."
            )
            
            logger.info("✅ Cancellation recorded")
            self.call_manager.end_call(call_id)
        else:
            self.tts.synthesize("Let's try again.")
            self.handle_cancellation(call_id)
    
    def handle_faq(self, call_id, question):
        """Answer FAQs"""
        logger.info("🔵 FAQ PROCESS STARTED")
        
        answer = self.ai_brain.answer_faq(question, MOTEL_INFO)
        self.tts.synthesize(answer)
        
        self.tts.synthesize("Is there anything else I can help you with?")
        response = self.stt.listen(timeout=5)
        
        if "yes" in response.lower():
            self.handle_incoming_call(call_id, None)
        else:
            self.tts.synthesize("Thank you for calling Seahorse Inn. Goodbye!")
            self.call_manager.end_call(call_id)
    
    def transfer_to_agent(self, call_id):
        """Transfer to human agent"""
        logger.info("📞 Transferring to agent...")
        self.call_manager.transfer_to_agent(call_id)
    
    @staticmethod
    def parse_date(date_str):
        """Parse natural language dates"""
        date_str = date_str.lower()
        today = datetime.now().date()
        
        if "today" in date_str:
            return today.strftime("%m/%d/%Y")
        elif "tomorrow" in date_str:
            return (today + timedelta(days=1)).strftime("%m/%d/%Y")
        elif "next" in date_str:
            return (today + timedelta(days=7)).strftime("%m/%d/%Y")
        else:
            # Extract numbers
            import re
            numbers = re.findall(r'\d+', date_str)
            if len(numbers) >= 2:
                month, day = numbers[0], numbers[1]
                year = datetime.now().year
                return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
        
        return today.strftime("%m/%d/%Y")
    
    @staticmethod
    def extract_number(text):
        """Extract number from text"""
        import re
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 1
    
    @staticmethod
    def extract_phone(text):
        """Extract phone number from text"""
        import re
        digits = re.findall(r'\d', text)
        if len(digits) >= 10:
            phone = ''.join(digits[-10:])
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        return "Invalid"

# ============ FLASK API ============
agent = SeahorseAIAgent()

@app.route('/incoming-call', methods=['POST'])
def incoming_call():
    """Webhook for incoming calls"""
    data = request.json
    call_id = data.get('call_id')
    caller = data.get('caller_number')
    
    # Handle in background thread
    thread = threading.Thread(target=agent.handle_incoming_call, args=(call_id, caller))
    thread.start()
    
    return jsonify({"status": "call_processing"}), 200

@app.route('/status', methods=['GET'])
def status():
    """Health check"""
    return jsonify({
        "status": "online",
        "active_calls": len(agent.active_calls),
        "motel": "Seahorse Inn and Cottages"
    }), 200

# ============ RUN ============
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)