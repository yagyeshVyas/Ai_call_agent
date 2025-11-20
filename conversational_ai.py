import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ConversationalAI:
    """
    Natural conversational AI using OpenRouter API.
    Handles multi-turn conversations with context awareness.
    """
    
    def __init__(self):
        # OpenRouter is OpenAI-compatible, just different base URL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY"))
        )
        
        # Use a good conversational model from OpenRouter
        # Options: meta-llama/llama-3.1-8b-instruct (cheap), google/gemini-pro (good), gpt-3.5-turbo
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
        amenities_list = "\n".join(f"- {a.strip()}" for a in self.motel_info["amenities"])
        
        return f"""You are a friendly and professional receptionist for {self.motel_info['name']}.

**Your Knowledge:**
- Property: {self.motel_info['name']}
- Phone: {self.motel_info['phone']}
- Address: {self.motel_info['address']}
- WiFi Password: {self.motel_info['wifi_password']}
- Check-in: {self.motel_info['check_in']}
- Check-out: {self.motel_info['check_out']}

**Amenities:**
{amenities_list}

**Policies:**
{self.motel_info['policies']}

**Your Personality:**
- Warm, welcoming, and conversational
- Speak like a real person, not a robot
- Use natural language, contractions, and casual phrases
- Keep responses SHORT (1-3 sentences max for phone calls)
- Be helpful and patient
- If you don't know something, offer to transfer to a manager

**Important Rules:**
1. NEVER make up information not in your knowledge base
2. For reservations, tell them you'll transfer them to the booking system
3. When guests say goodbye/thank you/bye, respond warmly and end naturally
4. Always confirm WiFi password clearly when asked

**Conversation Style:**
- Guest: "What's the wifi password?"
  You: "It's {self.motel_info['wifi_password']}. Pretty simple to remember!"
  
- Guest: "When can I check in?"
  You: "Check-in starts at {self.motel_info['check_in']}. We'll have your room ready!"
  
- Guest: "Thanks, bye"
  You: "You're welcome! Have a great day!"
"""
    
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
            # Call OpenRouter API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversations[call_id],
                max_tokens=150,  # Keep responses short for phone calls
                temperature=0.7  # Balanced creativity
            )
            
            ai_response = response.choices[0].message.content.strip()
            
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
