@echo off
cd /d %~dp0

echo Installing Python dependencies...
python -m pip install --upgrade pip

pip install pyaudio
pip install vosk
pip install piper-tts
pip install python-dotenv
pip install asterisk-python-ami
pip install selenium
pip install playwright
pip install pyttsx3
pip install requests
pip install flask
pip install twilio
pip install pydantic

echo Installing Playwright browsers...
python -m playwright install

echo Setup complete! Run: python main.py
pause