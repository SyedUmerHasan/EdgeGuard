"""DHCP fingerprinting for exact device identification."""
from scapy.all import sniff, DHCP, BOOTP
import logging

logger = logging.getLogger(__name__)

class DHCPFingerprinter:
    """Capture DHCP packets for device fingerprinting."""
    
    def __init__(self, callback):
        self.callback = callback
    
    def handle_packet(self, packet):
        """Handle DHCP packet."""
        if packet.haslayer(DHCP) and packet.haslayer(BOOTP):
            try:
                bootp = packet[BOOTP]
                dhcp = packet[DHCP]
                
                mac_address = bootp.chaddr[:6].hex(':')
                requested_ip = bootp.ciaddr if bootp.ciaddr != '0.0.0.0' else bootp.yiaddr
                
                # Extract DHCP options
                hostname = None
                vendor_class = None
                param_req_list = []
                
                for opt in dhcp.options:
                    if isinstance(opt, tuple):
                        opt_name, opt_value = opt[0], opt[1]
                        
                        # Option 12: Hostname
                        if opt_name == 'hostname':
                            hostname = opt_value.decode('utf-8', errors='ignore') if isinstance(opt_value, bytes) else str(opt_value)
                        
                        # Option 60: Vendor Class Identifier
                        elif opt_name == 'vendor_class_id':
                            vendor_class = opt_value.decode('utf-8', errors='ignore') if isinstance(opt_value, bytes) else str(opt_value)
                        
                        # Option 55: Parameter Request List (DHCP Fingerprint)
                        elif opt_name == 'param_req_list':
                            if isinstance(opt_value, (list, tuple)):
                                param_req_list = list(opt_value)
                            elif isinstance(opt_value, bytes):
                                param_req_list = list(opt_value)
                
                # Create DHCP fingerprint string
                dhcp_fingerprint = ','.join(map(str, param_req_list)) if param_req_list else None
                
                if mac_address and (hostname or vendor_class or dhcp_fingerprint):
                    self.callback(
                        mac_address=mac_address,
                        ip_address=requested_ip,
                        hostname=hostname,
                        vendor_class=vendor_class,
                        dhcp_fingerprint=dhcp_fingerprint
                    )
                    logger.info(f"DHCP: {mac_address} -> {hostname or 'unknown'} (fingerprint: {dhcp_fingerprint})")
                    
            except Exception as e:
                logger.debug(f"DHCP parse error: {e}")
    
    def start(self, interface=None):
        """Start listening for DHCP packets."""
        logger.info("Starting DHCP fingerprinter")
        sniff(
            prn=self.handle_packet,
            filter="udp port 67 or udp port 68",
            iface=interface,
            store=0
        )
