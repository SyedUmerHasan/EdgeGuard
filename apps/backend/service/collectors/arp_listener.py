"""ARP listener for device discovery."""
from scapy.all import ARP, sniff
import logging

logger = logging.getLogger(__name__)

class ARPListener:
    """Listen for ARP packets to discover devices."""
    
    def __init__(self, callback):
        self.callback = callback
    
    def handle_packet(self, packet):
        """Handle ARP packet."""
        if packet.haslayer(ARP):
            if packet[ARP].op == 1:  # ARP request
                mac = packet[ARP].hwsrc
                ip = packet[ARP].psrc
                self.callback(mac, ip)
    
    def start(self, interface=None):
        """Start listening for ARP packets."""
        logger.info(f"Starting ARP listener on interface: {interface or 'all'}")
        sniff(
            prn=self.handle_packet,
            filter="arp",
            iface=interface,
            store=0
        )
