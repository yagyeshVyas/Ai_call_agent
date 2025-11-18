import openai
import json
import logging

logger = logging.getLogger(__name__)

class AIBrain:
    def __init__(self, api_key):
        openai.api_key = api_key
        self.model = "gpt-4o-mini"  # Free tier model
    
    def detect_intent(self, user_input):
        """Detect guest intent from input"""
        logger.info(f"🧠 Analyzing intent for: {user_input}")
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an intent detector for a motel AI assistant.
                        Classify the guest intent into ONE of these categories:
                        - NEW_BOOKING (booking new room)
                        - EXTEND_STAY (extending current stay)
                        - CANCEL (canceling reservation)
                        - FAQ (asking about motel info)
                        - OTHER (everything else)
                        
                        Respond with ONLY the category name."""
                    },
                    {"role": "user", "content": user_input}
                ],
                max_tokens=10
            )
            
            intent = response['choices'][0]['message']['content'].strip()
            logger.info(f"✅ Intent: {intent}")
            return intent
        
        except Exception as e:
            logger.error(f"❌ Intent detection failed: {e}")
            return "OTHER"
    
    def answer_faq(self, question, motel_info):
        """Answer FAQs using motel knowledge base"""
        logger.info(f"❓ Answering FAQ: {question}")
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a helpful motel assistant for {motel_info['property']['name']}.
                        Use this information to answer questions naturally:
                        {json.dumps(motel_info, indent=2)}
                        Keep responses under 100 words. Be friendly and professional."""
                    },
                    {"role": "user", "content": question}
                ],
                max_tokens=150
            )
            
            answer = response['choices'][0]['message']['content']
            logger.info(f"✅ FAQ answered")
            return answer
        
        except Exception as e:
            logger.error(f"❌ FAQ answering failed: {e}")
            return "I'm not sure about that. Let me transfer you to our manager."