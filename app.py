from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os

# === USER SETUP ===

# Your Twilio account SID and Auth Token (keep these as environment variables)
ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
PERSONAL_PHONE_NUMBER = os.environ.get('PERSONAL_PHONE_NUMBER')

# The direct link to your audio file (Google Drive or other host)
AUDIO_URL = 'https://dl.dropboxusercontent.com/scl/fi/mt8ufzzxto7xn46xpe07o/voice2.mp3'

# === END USER SETUP ===

app = Flask(__name__)

# Store active call SID globally
active_call_sid = None

@app.route("/voice", methods=['POST'])
def voice():
    """Twilio requests this URL when the call connects."""
    response = VoiceResponse()
    response.say("You are now connected.")
    return Response(str(response), mimetype='text/xml')

@app.route("/call", methods=['GET'])
def initiate_call():
    """Trigger call from CRM click-to-dial."""
    global active_call_sid

    target_number = request.args.get('number')
    if not target_number:
        return "Error: No number provided.", 400

    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    # Make the call to your phone first
    call = client.calls.create(
        to=PERSONAL_PHONE_NUMBER,
        from_=TWILIO_PHONE_NUMBER,
        url='https://twilio-call-app.onrender.com/voice',
        status_callback='https://twilio-call-app.onrender.com/status',
        status_callback_event=['initiated', 'ringing', 'answered', 'completed']
    )

    active_call_sid = call.sid
    print(f"Call initiated! Call SID: {call.sid}")

    return f"Calling your phone! Call SID: {call.sid}", 200

@app.route("/play-message", methods=['GET'])
def play_message():
    """Manually trigger playback of the pre-recorded message."""
    global active_call_sid

    if not active_call_sid:
        return "Error: No active call.", 400

    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    # Use Twilio's call modification to redirect to the message
    call = client.calls(active_call_sid).update(
        url='https://twilio-call-app.onrender.com/message',
        method='POST'
    )

    print(f"Playing message in active call SID: {active_call_sid}")
    return "Message playback triggered!", 200

@app.route("/message", methods=['POST'])
def message():
    """Plays the recorded message."""
    response = VoiceResponse()
    response.play(AUDIO_URL)
    return Response(str(response), mimetype='text/xml')

@app.route("/status", methods=['POST'])
def status_callback():
    """Handle status updates from Twilio."""
    global active_call_sid

    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')

    print(f"Call SID: {call_sid}, Status: {call_status}")

    if call_status == 'completed':
        active_call_sid = None  # Reset when call is complete

    return ('', 204)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
