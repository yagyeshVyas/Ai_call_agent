from google_voice_agent import GoogleVoiceAgent
import time

def test_login():
    print("🚀 Starting Google Voice Agent Test...")
    agent = GoogleVoiceAgent(headless=False)
    try:
        agent.start()
        print("✅ Browser launched and navigated.")
        
        if agent.is_logged_in():
            print("✅ User is ALREADY logged in!")
        else:
            print("⚠️ User is NOT logged in. Please log in manually in the popup window.")
            
        # Wait a bit to allow manual login if needed
        print("Waiting 10 seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("🛑 Closing browser...")
        agent.close()

if __name__ == "__main__":
    test_login()
