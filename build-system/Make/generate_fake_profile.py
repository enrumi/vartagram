import plistlib
import uuid
import sys
import base64
from datetime import datetime, timedelta

if len(sys.argv) < 6:
    print("Usage: python3 generate_fake_profile.py cert_path team_id bundle_id output_path profile_name")
    sys.exit(1)

cert_path = sys.argv[1]
team_id = sys.argv[2]
bundle_id = sys.argv[3]
output_path = sys.argv[4]
profile_name = sys.argv[5]

# Map profile names to bundle ID suffixes
name_to_suffix = {
    'Telegram': '',
    'Share': '.Share',
    'NotificationContent': '.NotificationContent',
    'NotificationService': '.NotificationService',
    'Widget': '.Widget',
    'Intents': '.SiriIntents',
    'BroadcastUpload': '.BroadcastUpload',
}

suffix = name_to_suffix.get(profile_name, '')
app_id = f'{team_id}.{bundle_id}{suffix}'

# Read certificate and convert to DER format
with open(cert_path, "rb") as f:
    cert_data = f.read()
    # Remove PEM headers
    lines = cert_data.decode('utf-8').strip().split('\n')
    base64_str = "".join([l for l in lines if "---" not in l])
    der_data = base64.b64decode(base64_str)

profile_content = {
    "AppIDName": f"Fake {profile_name}",
    "ApplicationIdentifierPrefix": [team_id],
    "CreationDate": datetime.now(),
    "Platform": ["iOS"],
    "DeveloperCertificates": [der_data],
    "Entitlements": {
        "application-identifier": app_id,
        "com.apple.developer.team-identifier": team_id,
        "get-task-allow": True,
        "keychain-access-groups": [f"{team_id}.*"],
        "com.apple.security.application-groups": [f"group.{bundle_id}"],
        "aps-environment": "development",
        "com.apple.developer.applesignin": ["Default"],
        "com.apple.developer.carplay-messaging": True,
        "com.apple.developer.associated-domains": ["*"]
    },
    "ExpirationDate": datetime.now() + timedelta(days=365),
    "Name": f"Fake {profile_name} Profile",
    "ProvisionsAllDevices": True,
    "TeamIdentifier": [team_id],
    "TeamName": "Fake Team",
    "UUID": str(uuid.uuid4()),
    "Version": 1
}

with open(output_path, "wb") as f:
    plistlib.dump(profile_content, f)

print(f"Created {output_path}")
