import pyaudio
import vosk
import json
import logging

logger = logging.getLogger(__name__)

class SpeechRecognizer:
    def __init__(self, model_path="model"):
        """Initialize Vosk speech recognition"""
        vosk.SetLogLevel(-1)
        
        try:
            self.model = vosk.Model(model_path)
            logger.info("✅ Vosk model loaded")
        except Exception as e:
            logger.error(f"❌ Model failed: {e}")
            raise
        
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        self.microphone = pyaudio.PyAudio()
    
    def listen(self, timeout=10):
        """Listen to microphone and return transcribed text"""
        logger.info("🎤 Listening...")
        
        stream = self.microphone.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096
        )
        
        start_time = time.time()
        final_result = ""
        
        while time.time() - start_time < timeout:
            data = stream.read(4096)
            
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if "result" in result:
                    final_result = " ".join([x["conf"] for x in result["result"]])
                    logger.info(f"✅ Heard: {final_result}")
                    break
        
        stream.stop_stream()
        stream.close()
        
        return final_result if final_result else ""