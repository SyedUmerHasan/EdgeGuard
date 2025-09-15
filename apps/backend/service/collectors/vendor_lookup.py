"""MAC vendor lookup using IEEE OUI database."""
import requests
import logging

logger = logging.getLogger(__name__)

def get_vendor(mac_address):
    """Get vendor name from MAC address using macvendors.com API."""
    try:
        # Format MAC address
        mac = mac_address.replace(':', '').replace('-', '').upper()
        
        # Use free API
        response = requests.get(f"https://api.macvendors.com/{mac}", timeout=2)
        
        if response.status_code == 200:
            return response.text.strip()
        return None
    except Exception as e:
        logger.debug(f"Vendor lookup failed for {mac_address}: {e}")
        return None
