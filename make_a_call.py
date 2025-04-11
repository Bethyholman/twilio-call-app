from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# === USER SETUP ===

# Your Twilio account SID and Auth Token (we will get these in setup)
import os

ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
PERSONAL_PHONE_NUMBER = os.environ.get('PERSONAL_PHONE_NUMBER')
TARGET_PHONE_NUMBER = os.environ.get('TARGET_PHONE_NUMBER')

# The direct link to your audio file (Google Drive or other host)
AUDIO_URL = 'https://drive.google.com/uc?export=download&id=11bmL3MU5E3epMD_lHGA6r-Fhtxk3ev0U'

# === END USER SETUP ===

app = Flask(__name__)

@app.route("/voice", methods=['POST'])
def voice():
    """This is what Twilio will request when the call connects."""
    response = VoiceResponse()
    response.play(AUDIO_URL)
    return Response(str(response), mimetype='text/xml')

def make_call():
    """This makes the outbound call."""
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    call = client.calls.create(
        to=TARGET_PHONE_NUMBER,
        from_=PERSONAL_PHONE_NUMBER,
        url='https://c97a-2607-fea8-e1-5c00-851e-82bd-fa60-da5c.ngrok-free.app/voice'
    )
    print(f"Call initiated! SID: {call.sid}")

if __name__ == '__main__':
    import threading

    # Start the Flask server in a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()

    input("Press Enter to make the call...")
    make_call()
