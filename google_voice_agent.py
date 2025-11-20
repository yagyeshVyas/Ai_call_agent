import logging
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleVoiceAgent:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None

    def start(self):
        """Start the browser and navigate to Google Voice"""
        self.playwright = sync_playwright().start()
        # Use a persistent context to save login session
        user_data_dir = "./gv_user_data"
        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"] # Try to hide automation
        )
        
        self.page = self.browser.pages[0]
        self.page.goto("https://voice.google.com")
        logger.info("🌍 Navigated to Google Voice")
        
        # Check if logged in
        if self.is_logged_in():
            logger.info("✅ Already logged in")
        else:
            logger.info("⚠️ Not logged in. Please log in manually in the browser window.")
            self.wait_for_login()

    def is_logged_in(self):
        """Check if user is logged in by looking for specific elements"""
        try:
            # Look for the 'Make a call' button or profile icon
            # Google Voice UI changes, but 'Make a call' or the dialpad is usually present
            self.page.wait_for_selector('div[aria-label="Make a call"]', timeout=5000)
            return True
        except:
            try:
                # Alternative selector
                self.page.wait_for_selector('a[aria-label="Calls"]', timeout=2000)
                return True
            except:
                return False

    def wait_for_login(self):
        """Wait until the user logs in manually"""
        logger.info("⏳ Waiting for login... (Press Ctrl+C to cancel)")
        while not self.is_logged_in():
            time.sleep(2)
        logger.info("✅ Login detected!")

    def send_sms(self, phone_number, message):
        """Send an SMS message"""
        try:
            logger.info(f"📨 Sending SMS to {phone_number}...")
            
            # 1. Click 'Messages' tab
            self.page.click('a[aria-label="Messages"]', timeout=5000)
            time.sleep(1)
            
            # 2. Click 'Send new message'
            self.page.click('div[aria-label="Send new message"]', timeout=5000)
            
            # 3. Type phone number
            self.page.fill('input[placeholder="Type a name or phone number"]', phone_number)
            time.sleep(1)
            self.page.keyboard.press("Enter")
            
            # 4. Type message
            self.page.fill('textarea[aria-label="Type a message"]', message)
            time.sleep(1)
            
            # 5. Send
            self.page.keyboard.press("Enter")
            logger.info("✅ SMS sent!")
            
        except Exception as e:
            logger.error(f"❌ Failed to send SMS: {e}")

    def make_call(self, phone_number):
        """Initiate an outbound call"""
        try:
            logger.info(f"📞 Calling {phone_number}...")
            
            # 1. Click 'Calls' tab
            self.page.click('a[aria-label="Calls"]', timeout=5000)
            time.sleep(1)
            
            # 2. Click 'Make a call'
            self.page.click('div[aria-label="Make a call"]', timeout=5000)
            
            # 3. Type phone number
            self.page.fill('input[placeholder="Enter a name or number"]', phone_number)
            time.sleep(1)
            
            # 4. Click Call button (usually the first option in dropdown or just enter)
            self.page.keyboard.press("Enter")
            
            # Wait for call to connect (this is tricky to detect)
            logger.info("✅ Call initiated. Check browser for audio.")
            
        except Exception as e:
            logger.error(f"❌ Failed to make call: {e}")

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

if __name__ == "__main__":
    # Test the agent
    agent = GoogleVoiceAgent(headless=False)
    try:
        agent.start()
        
        # Example usage (uncomment to test)
        # agent.send_sms("555-555-5555", "Hello from Seahorse AI!")
        
        # Keep open for a bit
        print("Browser is open. You can test manually.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        agent.close()
