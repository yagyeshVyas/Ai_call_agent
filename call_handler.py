import logging

logger = logging.getLogger(__name__)

class CallManager:
    def __init__(self):
        self.active_calls = {}
    
    def play_audio(self, audio_file):
        """Play audio to caller"""
        logger.info(f"🔊 Playing: {audio_file}")
        # Use system audio player or Asterisk
        import subprocess
        subprocess.run(['ffplay', '-nodisp', '-autoexit', audio_file])
    
    def transfer_to_agent(self, call_id):
        """Transfer call to human agent"""
        logger.info(f"📞 Transferring call {call_id} to agent")
        # Use Asterisk dial command
        pass
    
    def end_call(self, call_id):
        """End the call"""
        logger.info(f"📵 Ending call {call_id}")
        if call_id in self.active_calls:
            del self.active_calls[call_id]