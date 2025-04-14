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
AUDIO_URL = 'https://www.dropbox.com/scl/fi/mt8ufzzxto7xn46xpe07o/voice2.mp3?rlkey=ir1y7bbwezhwjsnnne60umlex&st=7en0mjpm&dl=1'

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
        url='https://twilio-call-app.onrender.com/voice'
    )
    print(f"Call initiated! SID: {call.sid}")

if __name__ == '__main__':
    import threading

    # Start the Flask server in a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()

    input("Press Enter to make the call...")
    make_call()
