"""mDNS/Bonjour service discovery for device identification."""
from scapy.all import sniff, DNS, DNSQR, DNSRR
import logging

logger = logging.getLogger(__name__)

class MDNSListener:
    """Listen for mDNS announcements to discover device services."""
    
    def __init__(self, callback):
        self.callback = callback
    
    def handle_packet(self, packet):
        """Handle mDNS packet."""
        if packet.haslayer(DNS):
            dns = packet[DNS]
            
            # mDNS responses
            if dns.qr == 1 and packet.haslayer(DNSRR):
                for i in range(dns.ancount):
                    try:
                        rr = dns.an[i]
                        name = rr.rrname.decode('utf-8').rstrip('.')
                        
                        # Extract service info
                        if '_' in name:  # Service announcement
                            service_type = name.split('.')[0]
                            
                            # Get additional info
                            rdata = str(rr.rdata) if rr.rdata else None
                            
                            self.callback(
                                service_name=name,
                                service_type=service_type,
                                rdata=rdata
                            )
                            logger.info(f"mDNS service: {name} -> {rdata}")
                    except Exception as e:
                        logger.debug(f"mDNS parse error: {e}")
    
    def start(self, interface=None):
        """Start listening for mDNS packets."""
        logger.info("Starting mDNS listener")
        sniff(
            prn=self.handle_packet,
            filter="udp port 5353",
            iface=interface,
            store=0
        )
