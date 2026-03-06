import requests
import base64
import os
import time
from dotenv import load_dotenv
from msal import PublicClientApplication, SerializableTokenCache


load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = os.getenv("AUTHORITY")
SCOPES = [os.getenv("SCOPES")]

CACHE_FILE = os.getenv("CACHE_FILE")
PROCESSED_FILE = os.getenv("PROCESSED_FILE")
FOLDER_NAME = os.getenv("FOLDER_NAME")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL"))

cache = SerializableTokenCache()

if os.path.exists(CACHE_FILE):
    cache.deserialize(open(CACHE_FILE, "r").read())

app = PublicClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    token_cache=cache
)

accounts = app.get_accounts()

if accounts:
    result = app.acquire_token_silent(SCOPES, account=accounts[0])
else:
    result = None

if not result:
    result = app.acquire_token_interactive(scopes=SCOPES)

if cache.has_state_changed:
    open(CACHE_FILE, "w").write(cache.serialize())

access_token = result["access_token"]

headers = {
    "Authorization": "Bearer " + access_token
}

processed_ids = set()

if os.path.exists(PROCESSED_FILE):
    with open(PROCESSED_FILE) as f:
        for line in f:
            processed_ids.add(line.strip())

folder_url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/childFolders"

folders = requests.get(folder_url, headers=headers).json()

folder_id = None

for f in folders["value"]:
    if f["displayName"] == FOLDER_NAME:
        folder_id = f["id"]

if not folder_id:
    print("Folder not found")
    exit()

print("Monitoring folder:", FOLDER_NAME)

email_list = []

while True:

    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages?$top=10&$orderby=receivedDateTime desc"

    response = requests.get(url, headers=headers)
    emails = response.json()

    for mail in emails["value"]:

        message_id = mail["id"]

        if message_id in processed_ids:
            continue

        print("\nNew Mail Found")

        processed_ids.add(message_id)

        with open(PROCESSED_FILE, "a") as f:
            f.write(message_id + "\n")

        subject = mail["subject"]
        sender = mail["from"]["emailAddress"]["address"]
        body = mail["bodyPreview"]

        attachments_list = []

        if mail["hasAttachments"]:

            attach_url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"

            attach_response = requests.get(attach_url, headers=headers).json()

            for att in attach_response["value"]:

                file_name = att["name"]

                print("Downloading:", file_name)

                file_data = base64.b64decode(att["contentBytes"])

                with open(file_name, "wb") as f:
                    f.write(file_data)

                attachments_list.append(file_name)

        mail_dict = {
            "subject": subject,
            "from": sender,
            "body": body,
            "attachments": attachments_list
        }

        email_list.append(mail_dict)

        for email in email_list:
            print(email["subject"])
            print(email["body"])
            print(email["attachments"])

    time.sleep(CHECK_INTERVAL)