"""Fingerbank API integration for exact device identification."""
import requests
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Load API key from .env file
def load_api_key():
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith('FINGERBANK_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return os.getenv('FINGERBANK_API_KEY', 'YOUR_API_KEY_HERE')

FINGERBANK_API_KEY = load_api_key()
FINGERBANK_API_URL = "https://api.fingerbank.org/api/v2/combinations/interrogate"

def identify_device_exact(mac_address, dhcp_fingerprint=None, user_agent=None, hostname=None):
    """
    Query Fingerbank API for exact device identification.
    
    Returns: dict with device_name, device_type, os, version, score
    """
    if FINGERBANK_API_KEY == "YOUR_API_KEY_HERE":
        logger.warning("Fingerbank API key not configured. Set FINGERBANK_API_KEY in environment.")
        return None
    
    try:
        # Build query payload
        payload = {}
        
        if mac_address:
            # Extract OUI (first 6 chars)
            payload['mac'] = mac_address.replace(':', '').replace('-', '')[:6]
        
        if dhcp_fingerprint:
            payload['dhcp_fingerprint'] = dhcp_fingerprint
        
        if user_agent:
            payload['user_agent'] = user_agent
        
        if hostname:
            payload['hostname'] = hostname
        
        # Query Fingerbank API
        response = requests.get(
            FINGERBANK_API_URL,
            params={'key': FINGERBANK_API_KEY},
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'device' in data:
                device_info = {
                    'device_name': data['device'].get('name'),
                    'device_type': data.get('device_class', {}).get('name'),
                    'os': data.get('device', {}).get('parent_name'),
                    'version': data.get('version'),
                    'score': data.get('score', 0)
                }
                
                logger.info(f"Fingerbank identified: {device_info['device_name']} (score: {device_info['score']})")
                return device_info
        else:
            logger.warning(f"Fingerbank API error: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Fingerbank API request failed: {e}")
    
    return None
