import plistlib
import uuid
import sys
import base64
from datetime import datetime, timedelta

if len(sys.argv) < 7:
    print("Usage: python3 generate_fake_profile.py cert_der_path key_path team_id bundle_id output_path profile_name")
    sys.exit(1)

cert_der_path = sys.argv[1]
key_path = sys.argv[2]
team_id = sys.argv[3]
bundle_id = sys.argv[4]
output_path = sys.argv[5]
profile_name = sys.argv[6]

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

# Read certificate DER data directly
with open(cert_der_path, "rb") as f:
    der_data = f.read()

profile_content = {
    "AppIDName": f"Fake {profile_name}",
    "ApplicationIdentifierPrefix": [team_id],
    "CreationDate": datetime.now(),
    "Platform": ["iOS"],
    "IsXcodeManaged": False,
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
    "ProvisionedDevices": [],
    "ProvisionsAllDevices": True,
    "TeamIdentifier": [team_id],
    "TeamName": "Fake Team",
    "TimeToLive": 365,
    "UUID": str(uuid.uuid4()),
    "Version": 1
}

# Write plist to temp file
import tempfile
import subprocess
import os

temp_plist = tempfile.NamedTemporaryFile(mode='wb', suffix='.plist', delete=False)
temp_plist_path = temp_plist.name
plistlib.dump(profile_content, temp_plist)
temp_plist.close()

# Sign the plist with openssl smime to create mobileprovision
# key_path is now passed as argument

# Convert DER back to PEM for signing
temp_cert_pem = tempfile.NamedTemporaryFile(mode='wb', suffix='.pem', delete=False)
temp_cert_pem_path = temp_cert_pem.name

# Convert DER to PEM
subprocess.run([
    'openssl', 'x509',
    '-inform', 'DER',
    '-in', cert_der_path,
    '-out', temp_cert_pem_path
], check=True, capture_output=True)
temp_cert_pem.close()

try:
    subprocess.run([
        'openssl', 'smime', '-sign',
        '-in', temp_plist_path,
        '-out', output_path,
        '-outform', 'der',
        '-signer', temp_cert_pem_path,
        '-inkey', key_path,
        '-nodetach'
    ], check=True, capture_output=True)
    
    print(f"Created {output_path}")
finally:
    os.unlink(temp_plist_path)
    if os.path.exists(temp_cert_pem_path):
        os.unlink(temp_cert_pem_path)
