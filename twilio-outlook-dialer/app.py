from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from msal import ConfidentialClientApplication
import requests
import os
import threading
import time
import logging

# === SETUP LOGGING ===
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# === TERMINAL COLORS ===
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log(message, level='info'):
    print(message)
    getattr(logging, level)(message)

# === ENVIRONMENT VARIABLES CHECK ===
required_env_vars = [
    'OUTLOOK_CLIENT_ID',
    'OUTLOOK_CLIENT_SECRET',
    'OUTLOOK_TENANT_ID',
    'TWILIO_ACCOUNT_SID',
    'TWILIO_AUTH_TOKEN',
    'TWILIO_PHONE_NUMBER',
    'PERSONAL_PHONE_NUMBER'
]

for var in required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f"{Colors.FAIL}⚠️ Missing required environment variable: {var}{Colors.ENDC}")

ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
PERSONAL_PHONE_NUMBER = os.environ.get('PERSONAL_PHONE_NUMBER')
AUDIO_URL = 'https://dl.dropboxusercontent.com/scl/fi/mt8ufzzxto7xn46xpe07o/voice2.mp3'

OUTLOOK_CLIENT_ID = os.environ.get('OUTLOOK_CLIENT_ID')
OUTLOOK_CLIENT_SECRET = os.environ.get('OUTLOOK_CLIENT_SECRET')
OUTLOOK_TENANT_ID = os.environ.get('OUTLOOK_TENANT_ID')

# === FLASK APP ===
app = Flask(__name__)

@app.route("/voice", methods=['POST'])
def voice():
    """Twilio requests this when the call connects."""
    response = VoiceResponse()
    response.play(AUDIO_URL)
    return Response(str(response), mimetype='text/xml')


def make_call(target_number, max_retries=3):
    """Initiate outbound call with retry logic."""
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    attempt = 0

    while attempt < max_retries:
        try:
            call = client.calls.create(
                to=target_number,
                from_=PERSONAL_PHONE_NUMBER,
                url='https://twilio-call-app.onrender.com/voice'
            )
            log(f"{Colors.OKGREEN}📞 Call initiated! SID: {call.sid}{Colors.ENDC}")
            return
        except Exception as e:
            attempt += 1
            log(f"{Colors.WARNING}Attempt {attempt} failed: {e}{Colors.ENDC}", level='warning')
            time.sleep(2)  # Wait before retrying

    log(f"{Colors.FAIL}❌ Failed to initiate call after {max_retries} attempts.{Colors.ENDC}", level='error')


def get_outlook_contacts():
    """Authenticate and fetch contacts from Microsoft 365 (Outlook)."""
    authority = f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}"
    app = ConfidentialClientApplication(
        client_id=OUTLOOK_CLIENT_ID,
        client_credential=OUTLOOK_CLIENT_SECRET,
        authority=authority
    )

    scopes = ['https://graph.microsoft.com/.default']
    result = app.acquire_token_for_client(scopes=scopes)

    if "access_token" in result:
        token = result['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/contacts?$select=displayName,mobilePhone,businessPhones',
            headers=headers
        )

        if response.status_code == 200:
            contacts = response.json().get('value', [])
            log(f"{Colors.OKBLUE}✅ Successfully fetched {len(contacts)} contacts from Outlook.{Colors.ENDC}")
            return contacts
        else:
            log(f"{Colors.FAIL}Failed to fetch contacts: {response.status_code} - {response.text}{Colors.ENDC}", level='error')
            return []
    else:
        log(f"{Colors.FAIL}Error acquiring token: {result.get('error_description')}{Colors.ENDC}", level='error')
        return []


def select_contact(contacts):
    """Display contacts and let user pick one."""
    print(f"\n{Colors.HEADER}Your Outlook Contacts:{Colors.ENDC}")
    numbered_contacts = []

    for idx, contact in enumerate(contacts):
        name = contact.get('displayName', 'No Name')
        phone_numbers = contact.get('mobilePhone') or (contact.get('businessPhones') or [])
        if phone_numbers:
            number = phone_numbers if isinstance(phone_numbers, str) else phone_numbers[0]
            print(f"{idx + 1}: {name} - {number}")
            numbered_contacts.append(number)

    if not numbered_contacts:
        log(f"{Colors.WARNING}⚠️ No contacts with phone numbers found.{Colors.ENDC}", level='warning')
        return None

    try:
        choice = input(f"\nEnter the number of the contact you want to call: ")
        selected_number = numbered_contacts[int(choice) - 1]
        print(f"{Colors.OKGREEN}✅ Selected: {selected_number}{Colors.ENDC}")
        return selected_number
    except (IndexError, ValueError):
        log(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}", level='error')
        return None


if __name__ == '__main__':
    # Start Flask server in background
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))).start()

    # Fetch Outlook contacts
    contacts = get_outlook_contacts()

    if contacts:
        target_number = select_contact(contacts)

        if target_number:
            input(f"\n{Colors.OKBLUE}Press Enter to initiate the call...{Colors.ENDC}")
            make_call(target_number)
    else:
        log(f"{Colors.FAIL}No contacts to call.{Colors.ENDC}", level='error')
