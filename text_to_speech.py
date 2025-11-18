import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class TextToSpeech:
    def __init__(self):
        self.output_dir = "tts_audio"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def synthesize(self, text):
        """Convert text to speech using Piper (free, offline)"""
        logger.info(f"🔊 Synthesizing: {text[:50]}...")
        
        output_file = f"{self.output_dir}/output_{time.time()}.wav"
        
        try:
            # Using Piper TTS (free, local)
            subprocess.run([
                "piper",
                "--model", "en_US-lessac-medium",
                "--output_file", output_file
            ], input=text.encode(), check=True)
            
            logger.info(f"✅ Audio generated: {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"❌ TTS failed: {e}")
            return None