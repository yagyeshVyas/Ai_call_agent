from playwright.sync_api import sync_playwright
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SkyTouchAgent:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.browser = None
        self.context = None
        self.page = None
    
    def login(self):
        """Login to SkyTouch PMS"""
        logger.info("🔐 Logging into SkyTouch...")
        
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=False)  # Show browser for testing
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        try:
            self.page.goto("https://www.skytouch.com/login")
            self.page.fill('input[name="username"]', self.username)
            self.page.fill('input[name="password"]', self.password)
            self.page.click('button:has-text("Login")')
            
            # Wait for dashboard
            self.page.wait_for_selector('[data-test-id="dashboard"]', timeout=10000)
            logger.info("✅ SkyTouch login successful")
            return True
        
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    def create_reservation(self, name, phone, email, check_in, check_out, num_guests):
        """Create new reservation in SkyTouch"""
        logger.info(f"📝 Creating reservation for {name}...")
        
        if not self.browser:
            self.login()
        
        try:
            # Navigate to reservations
            self.page.click('text="Reservations"')
            self.page.click('text="New Reservation"')
            
            # Fill guest name
            self.page.fill('[placeholder="Guest Name"]', name)
            
            # Fill phone
            self.page.fill('[placeholder="Phone"]', phone)
            
            # Fill email
            self.page.fill('[placeholder="Email"]', email)
            
            # Fill check-in
            self.page.fill('[placeholder="Check In"]', check_in)
            
            # Fill check-out
            self.page.fill('[placeholder="Check Out"]', check_out)
            
            # Fill guests
            self.page.fill('[placeholder="Number of Guests"]', str(num_guests))
            
            # Submit
            self.page.click('button:has-text("Create Reservation")')
            
            # Wait and get confirmation
            self.page.wait_for_selector('[data-test-id="confirmation"]', timeout=10000)
            confirmation = self.page.text_content('[data-test-id="confirmation"]')
            
            logger.info(f"✅ Reservation created: {confirmation}")
            
            return {
                "success": True,
                "confirmation_id": confirmation
            }
        
        except Exception as e:
            logger.error(f"❌ Reservation creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def search_reservation(self, guest_identifier):
        """Search for existing reservation"""
        logger.info(f"🔍 Searching for {guest_identifier}...")
        
        if not self.browser:
            self.login()
        
        try:
            self.page.fill('[placeholder="Search Guest"]', guest_identifier)
            self.page.wait_for_selector('[data-test-id="search-result"]', timeout=5000)
            
            # Extract reservation data
            reservation = {
                "guest_name": self.page.text_content('[data-test-id="guest-name"]'),
                "id": self.page.text_content('[data-test-id="res-id"]'),
                "checkout_date": self.page.text_content('[data-test-id="checkout"]')
            }
            
            logger.info(f"✅ Reservation found: {reservation}")
            return reservation
        
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return None
    
    def update_checkout(self, reservation_id, new_checkout):
        """Update checkout date"""
        logger.info(f"📅 Updating checkout to {new_checkout}...")
        
        if not self.browser:
            self.login()
        
        try:
            self.page.click(f'[data-res-id="{reservation_id}"]')
            self.page.click('[data-test-id="edit"]')
            
            # Clear and fill new checkout
            self.page.fill('[placeholder="Check Out"]', "")
            self.page.fill('[placeholder="Check Out"]', new_checkout)
            
            self.page.click('button:has-text("Update")')
            
            logger.info("✅ Checkout updated")
            return {"success": True}
        
        except Exception as e:
            logger.error(f"❌ Update failed: {e}")
            return {"success": False}
    
    def close(self):
        """Close browser"""
        if self.browser:
            self.browser.close()