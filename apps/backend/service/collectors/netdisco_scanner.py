"""Netdisco integration for IoT device discovery."""
from netdisco.discovery import NetworkDiscovery
import logging
import time

logger = logging.getLogger(__name__)

class NetdiscoScanner:
    """Discover IoT devices using netdisco."""
    
    def __init__(self, callback):
        self.callback = callback
        self.netdis = NetworkDiscovery()
    
    def scan(self, duration=10):
        """Scan network for IoT devices."""
        logger.info(f"Starting netdisco scan for {duration} seconds...")
        
        self.netdis.scan(duration)
        
        # Process discovered devices
        for device_type in self.netdis.discover():
            devices = self.netdis.get_info(device_type)
            
            for device in devices:
                self.process_device(device_type, device)
        
        self.netdis.stop()
        logger.info("Netdisco scan complete")
    
    def process_device(self, device_type, device_info):
        """Process discovered device."""
        try:
            # Extract device information
            host = device_info.get('host', '')
            name = device_info.get('name', device_info.get('hostname', ''))
            manufacturer = device_info.get('manufacturer', '')
            model = device_info.get('model', '')
            
            if host:
                self.callback(
                    ip_address=host,
                    device_type=device_type,
                    device_name=name,
                    manufacturer=manufacturer,
                    model=model,
                    raw_info=str(device_info)
                )
                
                logger.info(f"Netdisco found: {device_type} - {name} ({host})")
        
        except Exception as e:
            logger.error(f"Error processing netdisco device: {e}")
    
    def scan_async(self, duration=10):
        """Async scan in background."""
        import threading
        thread = threading.Thread(target=self.scan, args=(duration,), daemon=True)
        thread.start()
        return thread
