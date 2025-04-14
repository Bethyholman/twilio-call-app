from flask import Flask, request, Response, render_template_string, redirect
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os
import threading
import msal
import requests

# === USER SETUP ===

# Twilio credentials
ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
PERSONAL_PHONE_NUMBER = os.environ.get('PERSONAL_PHONE_NUMBER')

# Microsoft 365 credentials
CLIENT_ID = os.environ.get('CLIENT_ID')  # Application (client) ID
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')  # Client secret
TENANT_ID = os.environ.get('TENANT_ID')  # Directory (tenant) ID

# Direct audio file URL
AUDIO_URL = 'https://dl.dropboxusercontent.com/scl/fi/mt8ufzzxto7xn46xpe07o/voice2.mp3'

# === END USER SETUP ===

app = Flask(__name__)

# Token cache
cache = msal.SerializableTokenCache()

def get_access_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )
    result = app.acquire_token_silent(["Contacts.Read"], account=None)

    if not result:
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    return result['access_token']

@app.route("/")
def list_contacts():
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('https://graph.microsoft.com/v1.0/me/contacts?$select=displayName,mobilePhone', headers=headers)

    contacts = response.json().get('value', [])

    # Build a simple HTML page with links to place calls
    html = "<h2>Your Contacts</h2><ul>"
    for contact in contacts:
        name = contact.get('displayName', 'Unnamed')
        phone = contact.get('mobilePhone')
        if phone:
            html += f'<li>{name} - <a href="/call?number={phone}">{phone}</a></li>'
    html += "</ul>"

    return render_template_string(html)

@app.route("/call")
def call():
    target_number = request.args.get('number')

    if not target_number:
        return "No number provided.", 400

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    call = client.calls.create(
        to=target_number,
        from_=PERSONAL_PHONE_NUMBER,
        url='https://twilio-call-app.onrender.com/voice'
    )
    print(f"Call initiated! SID: {call.sid}")

    return f"Call initiated to {target_number}!"

@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()
    response.play(AUDIO_URL)
    return Response(str(response), mimetype='text/xml')

if __name__ == '__main__':
    # Start the Flask server in a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))).start()

    input("Server running! Open https://twilio-call-app.onrender.com/ in your browser.\n")
