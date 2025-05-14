from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import pubsub_v1
from datetime import datetime
import os
import sys
import base64
import json
import requests
import time


app = Flask(__name__)

creds = None


@app.route('/gmail-webhook', methods=['POST'])
def gmail_webhook():
    data = request.get_json()
    if 'message' not in data or 'data' not in data['message']:
        return jsonify({"error": "Invalid payload"}), 400

    # Decode the base64-encoded data
    encoded_data = data['message']['data']
    try:
        decoded_data = base64.urlsafe_b64decode(encoded_data + '==').decode('utf-8')
        decoded_json = json.loads(decoded_data)
    except (base64.binascii.Error, json.JSONDecodeError) as e:
        print(f"Decoding error: {e}")
        return jsonify({"error": "Decoding failed"}), 400

    print("Decoded data:", decoded_json)
    service = get_gmail_service()
    email_address = decoded_json.get('emailAddress')
    history_id = decoded_json.get('historyId')
    if not email_address or not history_id:
        return jsonify({"error": "Missing email address or history ID"}), 400

    try:
        print("Fetching history...")
        history = service.users().history().list(
            userId=email_address,  # Replace 'me' with email_address
            startHistoryId=str(history_id)
        ).execute()

        if 'history' not in history:
            print("No history found.")
            return jsonify({"status": "no_history"}), 200

        for record in history['history']:
            if 'messages' in record:
                for message in record['messages']:
                    message_id = message['id']

                    # Fetch the email
                    email = service.users().messages().get(userId=email_address, id=message_id).execute()
                    print("Fetched email:", email)

    except Exception as e:
        print(f"Error processing email: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "success"}), 200




# Google API OAuth scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

# Function to initiate the watch on Gmail
def login_gmail():
    flow = InstalledAppFlow.from_client_secrets_file('cred.json', SCOPES)
    global creds
    creds = flow.run_local_server(port=5000)


    # Build the Gmail API service
    global service
    service = build('gmail', 'v1', credentials=creds)
    # Configure the watch request
    request_body = {
        'labelIds': ['INBOX'],
        'topicName': 'projects/gmail-grabbing/topics/new-email-notifications'  # Replace with your Pub/Sub topic
    }

    # Send the watch request to start monitoring Gmail
    response = service.users().watch(userId='me', body=request_body).execute()
        
    return response.get('historyId')

def get_gmail_service():
    global creds
    if creds and creds.valid:
        return build('gmail', 'v1', credentials=creds)
    elif creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())  # Refresh the credentials
        return build('gmail', 'v1', credentials=creds)
    else:
        print("Credentials are invalid or expired.")
        return None  # Return None to indicate failure to refresh

def get_ngrok_url():
    try:
        ngrok_api_url = "http://127.0.0.1:4040/api/tunnels"
        response = requests.get(ngrok_api_url)
        response.raise_for_status()
        
        tunnels = response.json().get("tunnels", [])
        for tunnel in tunnels:
            if tunnel["proto"] == "https":  # Prefer HTTPS
                return tunnel["public_url"]
        return None
    except Exception as e:
        print(f"Error fetching Ngrok URL: {e}")
        return None

def update_pubsub_webhook(new_ngrok_url):
    try:
        project_id = "gmail-grabbing"  # Replace with your project ID
        subscription_id = "new-email-notifications-sub"  # Replace with your subscription name
        
        subscription_name = f"projects/{project_id}/subscriptions/{subscription_id}"
        
        client = pubsub_v1.SubscriberClient()
        push_config = pubsub_v1.types.PushConfig(push_endpoint=f"{new_ngrok_url}/gmail-webhook")
        client.modify_push_config(request={"subscription": subscription_name, "push_config": push_config})
        
        print(f"Webhook updated to: {new_ngrok_url}/gmail-webhook")
    except Exception as e:
        print(f"Error updating Pub/Sub webhook: {e}")

def update_ngrok():
    new_ngrok_url = get_ngrok_url()
    if new_ngrok_url:
        update_pubsub_webhook(new_ngrok_url)
    else:
        print("Failed to retrieve Ngrok URL.")

if __name__ == '__main__':
    if sys.argv[1] == 'prep':
        os.system('ngrok http http://localhost:8080')
    elif sys.argv[1] == 'run':
        history_id = login_gmail()
        print(f"Logged in to gmail. Tracking since history id: {history_id}")
        update_ngrok()
        app.run(port=8080, debug=False)
    
