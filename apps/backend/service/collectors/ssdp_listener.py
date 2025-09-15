"""SSDP/UPnP discovery for device details."""
from scapy.all import sniff, UDP, Raw
import logging
import re

logger = logging.getLogger(__name__)

class SSDPListener:
    """Listen for SSDP/UPnP announcements."""
    
    def __init__(self, callback):
        self.callback = callback
    
    def handle_packet(self, packet):
        """Handle SSDP packet."""
        if packet.haslayer(UDP) and packet.haslayer(Raw):
            try:
                payload = packet[Raw].load.decode('utf-8', errors='ignore')
                
                # SSDP NOTIFY or M-SEARCH response
                if 'NOTIFY' in payload or 'HTTP/1.1 200 OK' in payload:
                    # Extract device info
                    location = re.search(r'LOCATION:\s*(.+)', payload, re.IGNORECASE)
                    server = re.search(r'SERVER:\s*(.+)', payload, re.IGNORECASE)
                    usn = re.search(r'USN:\s*(.+)', payload, re.IGNORECASE)
                    nt = re.search(r'NT:\s*(.+)', payload, re.IGNORECASE)
                    
                    if location or server:
                        self.callback(
                            location=location.group(1).strip() if location else None,
                            server=server.group(1).strip() if server else None,
                            usn=usn.group(1).strip() if usn else None,
                            device_type=nt.group(1).strip() if nt else None,
                            src_ip=packet[0][1].src
                        )
                        logger.info(f"SSDP device: {server.group(1) if server else 'Unknown'}")
            except Exception as e:
                logger.debug(f"SSDP parse error: {e}")
    
    def start(self, interface=None):
        """Start listening for SSDP packets."""
        logger.info("Starting SSDP listener")
        sniff(
            prn=self.handle_packet,
            filter="udp port 1900",
            iface=interface,
            store=0
        )
