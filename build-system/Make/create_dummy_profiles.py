#!/usr/bin/env python3
import plistlib
import datetime
import subprocess
import sys
import os
import tempfile

def create_dummy_mobileprovision(name, team_id, bundle_id, output_path, cert_path, key_path):
    """Create a minimal valid .mobileprovision file"""
    
    # Map output name to bundle suffix
    # Based on profile_name_mapping in BuildConfiguration.py
    name_to_suffix = {
        'Telegram': '',
        'Share': '.Share',
        'NotificationContent': '.NotificationContent',
        'NotificationService': '.NotificationService',
        'Widget': '.Widget',
        'Intents': '.SiriIntents',
        'BroadcastUpload': '.BroadcastUpload',
        'WatchApp': '.watchkitapp',
        'WatchExtension': '.watchkitapp.watchkitextension'
    }
    
    suffix = name_to_suffix.get(name, '')
    # Use team_id as-is (should be "DUMMY" for unsigned builds)
    app_id = f'{team_id}.{bundle_id}{suffix}'
    keychain_team = team_id
    
    # Create minimal provisioning profile plist
    profile_dict = {
        'AppIDName': f'Vartagram {name}',
        'ApplicationIdentifierPrefix': [team_id] if team_id else [],
        'CreationDate': datetime.datetime(2024, 1, 1, 0, 0, 0),
        'Platform': ['iOS'],
        'IsXcodeManaged': False,
        'DeveloperCertificates': [],
        'Entitlements': {
            'application-identifier': app_id,
            'keychain-access-groups': [keychain_team],
            'com.apple.security.application-groups': [f'group.{bundle_id}'],
            'get-task-allow': True,
            'aps-environment': 'development'
        },
        'ExpirationDate': datetime.datetime(2099, 12, 31, 23, 59, 59),
        'Name': f'Vartagram {name} Profile',
        'ProvisionedDevices': [],
        'TeamIdentifier': [team_id],
        'TeamName': 'Vartagram Team',
        'TimeToLive': 365,
        'UUID': f'00000000-0000-0000-0000-{name.lower():0>12s}'[:36],
        'Version': 1
    }
    
    # Read the certificate and add to profile
    cert_data = None
    if os.path.exists(cert_path):
        with open(cert_path, 'rb') as f:
            cert_pem = f.read()
            # Extract DER data from PEM
            import re
            cert_b64 = re.search(b'-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----', cert_pem, re.DOTALL)
            if cert_b64:
                import base64
                cert_data = base64.b64decode(cert_b64.group(1))
    
    # Update DeveloperCertificates
    if cert_data:
        profile_dict['DeveloperCertificates'] = [cert_data]
    
    # Serialize to plist
    plist_data = plistlib.dumps(profile_dict, fmt=plistlib.FMT_XML)
    
    # Save plist to temp file
    temp_plist = os.path.join(tempfile.gettempdir(), 'temp_profile.plist')
    with open(temp_plist, 'wb') as f:
        f.write(plist_data)
    
    # Sign with openssl to create PKCS#7 structure
    try:
        result = subprocess.run([
            'openssl', 'smime', '-sign',
            '-in', temp_plist,
            '-out', output_path,
            '-outform', 'der',
            '-signer', cert_path,
            '-inkey', key_path,
            '-nodetach'
        ], capture_output=True, text=True, check=False)
        
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f'Created: {output_path}')
        else:
            print(f'Error creating {output_path}: {result.stderr}')
            return False
            
    except Exception as e:
        print(f'Error: {e}')
        return False
    finally:
        # Clean up
        if os.path.exists(temp_plist):
            os.remove(temp_plist)
    
    return True

def create_self_signed_cert(cert_path, key_path):
    """Create a self-signed certificate for signing"""
    print('Creating self-signed certificate...')
    
    # Generate private key
    subprocess.run([
        'openssl', 'genrsa',
        '-out', key_path,
        '2048'
    ], capture_output=True, check=True)
    
    # Create self-signed certificate
    subprocess.run([
        'openssl', 'req',
        '-new', '-x509',
        '-key', key_path,
        '-out', cert_path,
        '-days', '365',
        '-subj', '/CN=Dummy Codesigning Certificate'
    ], capture_output=True, check=True)
    
    print(f'Certificate created: {cert_path}')
    print(f'Private key created: {key_path}')

if __name__ == '__main__':
    team_id = sys.argv[1] if len(sys.argv) > 1 else 'XXXXXXXXXX'
    bundle_id = sys.argv[2] if len(sys.argv) > 2 else 'org.telegram.messenger'
    output_dir = sys.argv[3] if len(sys.argv) > 3 else 'build-system/empty-codesigning/profiles'
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create self-signed certificate
    cert_path = os.path.join(tempfile.gettempdir(), 'dummy_cert.pem')
    key_path = os.path.join(tempfile.gettempdir(), 'dummy_key.pem')
    
    try:
        create_self_signed_cert(cert_path, key_path)
        
        # These names must match the values in profile_name_mapping in BuildConfiguration.py
        profiles = [
            'Telegram',
            'Share', 
            'NotificationContent',
            'NotificationService',
            'Widget',
            'Intents',
            'BroadcastUpload'
        ]
        
        success_count = 0
        for profile_name in profiles:
            output_path = os.path.join(output_dir, f'{profile_name}.mobileprovision')
            if create_dummy_mobileprovision(profile_name, team_id, bundle_id, output_path, cert_path, key_path):
                success_count += 1
        
        print(f'\n? Successfully created {success_count}/{len(profiles)} profiles in {output_dir}')
        
    finally:
        # Clean up temp files
        if os.path.exists(cert_path):
            os.remove(cert_path)
        if os.path.exists(key_path):
            os.remove(key_path)
