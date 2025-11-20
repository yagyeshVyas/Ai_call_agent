import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ConversationalAI:
    """
    Natural conversational AI using OpenRouter API.
    Handles multi-turn conversations with context awareness.
    """
    
    def __init__(self):
        # Use requests directly to avoid OpenAI SDK dependency issues
        self.api_key = os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY"))
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Use a good conversational model from OpenRouter
        self.model = os.getenv("AI_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
        
        # Load motel knowledge from environment
        self.motel_info = self._load_motel_info()
        
        # Conversation memory: {call_id: [messages]}
        self.conversations = {}
        
        logger.info(f"🤖 Conversational AI initialized with model: {self.model}")
    
    def _load_motel_info(self):
        """Load motel information from environment variables"""
        return {
            "name": os.getenv("MOTEL_NAME", "Seahorse Inn and Cottages"),
            "phone": os.getenv("MOTEL_PHONE", "252-441-5242"),
            "address": os.getenv("MOTEL_ADDRESS", "7218 S Virginia Dare Trail, Nags Head, NC 27959"),
            "wifi_password": os.getenv("WIFI_PASSWORD", "SeahorseGuest2024"),
            "check_in": os.getenv("CHECK_IN_TIME", "3:00 PM"),
            "check_out": os.getenv("CHECK_OUT_TIME", "11:00 AM"),
            "amenities": os.getenv("AMENITIES", "Free WiFi, Pool, Beach Access, Pet-Friendly, Free Parking").split(","),
            "policies": os.getenv("POLICIES", "No smoking indoors, Pets allowed with fee, Quiet hours 10PM-8AM")
        }
    
    def _get_system_prompt(self):
        """Generate system prompt with motel knowledge"""
        amenities_list = "\n".join(f"• {a.strip()}" for a in self.motel_info["amenities"])
        
        return f"""You are the HEAD CONCIERGE at {self.motel_info['name']}, a world-class 7-star luxury coastal resort. You are renowned for your exceptional service, warmth, and professionalism.

═══════════════════════════════════════
📋 PROPERTY INFORMATION
═══════════════════════════════════════
🏨 Property: {self.motel_info['name']}
📞 Phone: {self.motel_info['phone']}
📍 Address: {self.motel_info['address']}
🔐 WiFi Password: {self.motel_info['wifi_password']}
🕒 Check-in Time: {self.motel_info['check_in']}
🕐 Check-out Time: {self.motel_info['check_out']}

✨ EXCLUSIVE AMENITIES:
{amenities_list}

📜 HOUSE POLICIES:
{self.motel_info['policies']}

═══════════════════════════════════════
🌟 YOUR PERSONALITY (7-STAR STANDARD)
═══════════════════════════════════════

**CORE VALUES:**
• Anticipate needs before guests ask
• Treat every guest like royalty
• Always go above and beyond
• Make guests feel at home AND special
• Turn problems into opportunities to delight

**COMMUNICATION STYLE:**
• Warm, genuine, and ENTHUSIASTIC  
• Professional yet personal (like talking to a valued friend)
• Use guest's name if mentioned (show you're listening!)
• Sprinkle in local charm (we're by the beach!)
• Keep responses SHORT (2-3 sentences max for phone - this is important!)
• Use natural contractions ("We're" not "We are")

**EMOTIONAL INTELLIGENCE:**
• Match guest's energy (excited → be excited! tired → be soothing)
• Acknowledge feelings ("I completely understand...")
• Celebrate special occasions ("How wonderful!")
• Show empathy for concerns

═══════════════════════════════════════
📞 CRITICAL PHONE CALL RULES
═══════════════════════════════════════

1. **BREVITY IS LUXURY**: Max 2-3 SHORT sentences per response
2. **DIRECT ANSWERS FIRST**: No fluff, answer the question immediately
3. **ADD VALUE SECOND**: Then add helpful context
4. **NEVER SAY**: "I'm just an AI" or "I'm a bot" - you ARE the concierge
5. **NEVER MAKE UP INFO**: Only use the facts provided above
6. **FOR RESERVATIONS**: "I'll connect you with our reservations team right away!"
7. **FOR COMPLEX ISSUES**: "Let me get our manager, they'll take great care of you."

═══════════════════════════════════════
💬 CONVERSATION EXAMPLES (STUDY THESE!)
═══════════════════════════════════════

❌ WRONG (robotic):
Guest: "What's the WiFi password?"
You: "The WiFi password is {self.motel_info['wifi_password']}."

✅ CORRECT (7-star):
Guest: "What's the WiFi password?"
You: "It's {self.motel_info['wifi_password']} - nice and easy! Works perfectly on our beachfront, by the way."

---

❌ WRONG (too long):
Guest: "When's check-in?"
You: "Check-in time is at {self.motel_info['check_in']}. We have a variety of check-in options available including our 24/7 kiosk. If you need early check-in, please let us know and we'll see what we can arrange."

✅ CORRECT (concise luxury):
Guest: "When's check-in?"
You: "Check-in starts at {self.motel_info['check_in']}. Need to arrive earlier? Just let me know!"

---

❌ WRONG (cold):
Guest: "Do you have parking?"
You: "Yes, we offer free parking."

✅ CORRECT (warm + value):
Guest: "Do you have parking?"
You: "Absolutely! Free parking right by your room. One less thing to worry about!"

---

✅ PERFECT (reservation request):
Guest: "I want to book a room for tonight."
You: "Wonderful! Let me connect you with our reservations specialist right away. One moment please!"

---

✅ PERFECT (goodbye):
Guest: "Thanks, bye!"
You: "My absolute pleasure! Enjoy your stay with us!"

═══════════════════════════════════════
🎯 YOUR MISSION
═══════════════════════════════════════
Make EVERY guest feel like they're calling the Ritz-Carlton, even if they're just asking about WiFi. You represent luxury, warmth, and excellence."""
    
    def chat(self, call_id, user_message):
        """
        Have a conversation turn with the AI.
        
        Args:
            call_id: Unique identifier for the call (to track context)
            user_message: What the user just said
            
        Returns:
            dict: {
                "response": str,  # AI's response
                "should_end_call": bool,  # True if conversation should end
                "intent": str  # Detected intent (greeting, question, goodbye, etc)
            }
        """
        logger.info(f"💬 [{call_id}] User: {user_message}")
        
        # Initialize conversation history if new call
        if call_id not in self.conversations:
            self.conversations[call_id] = [
                {"role": "system", "content": self._get_system_prompt()}
            ]
        
        # Add user message to history
        self.conversations[call_id].append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Call OpenRouter API with requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": self.conversations[call_id],
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            
            # Add AI response to history
            self.conversations[call_id].append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Detect if call should end
            should_end = self._detect_goodbye(user_message, ai_response)
            
            # Detect intent
            intent = self._detect_intent(user_message)
            
            logger.info(f"🤖 [{call_id}] AI: {ai_response}")
            logger.info(f"📊 [{call_id}] Intent: {intent}, End call: {should_end}")
            
            return {
                "response": ai_response,
                "should_end_call": should_end,
                "intent": intent
            }
        
        except Exception as e:
            logger.error(f"❌ AI chat error: {e}")
            return {
                "response": "I apologize, I'm having trouble right now. Let me transfer you to someone who can help.",
                "should_end_call": False,
                "intent": "error"
            }
    
    def _detect_goodbye(self, user_message, ai_response):
        """Detect if the conversation should end based on goodbye phrases"""
        goodbye_phrases = [
            "bye", "goodbye", "thank you", "thanks", "that's all",
            "i'm good", "all set", "have a good", "talk later"
        ]
        
        user_lower = user_message.lower()
        ai_lower = ai_response.lower()
        
        # Check if user is saying goodbye
        user_goodbye = any(phrase in user_lower for phrase in goodbye_phrases)
        
        # Check if AI is wrapping up
        ai_goodbye_phrases = ["have a great", "you're welcome", "enjoy your", "talk to you"]
        ai_goodbye = any(phrase in ai_lower for phrase in ai_goodbye_phrases)
        
        return user_goodbye or (user_goodbye and ai_goodbye)
    
    def _detect_intent(self, message):
        """Quick intent detection for basic routing"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["wifi", "password", "internet"]):
            return "wifi_question"
        elif any(word in message_lower for word in ["book", "reserve", "reservation", "room available"]):
            return "booking"
        elif any(word in message_lower for word in ["check in", "check out", "checkout", "checkin"]):
            return "check_in_out"
        elif any(word in message_lower for word in ["pool", "beach", "parking", "amenity", "amenities"]):
            return "amenities"
        elif any(word in message_lower for word in ["bye", "goodbye", "thank", "thanks"]):
            return "goodbye"
        else:
            return "general_question"
    
    def clear_conversation(self, call_id):
        """Clear conversation history for a call"""
        if call_id in self.conversations:
            del self.conversations[call_id]
            logger.info(f"🗑️ Cleared conversation for {call_id}")
