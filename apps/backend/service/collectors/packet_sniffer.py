"""Packet sniffer for traffic statistics and connection tracking."""
from scapy.all import sniff, IP, TCP, UDP, DNS, DNSQR, ICMP, DHCP, Raw
from scapy.layers.http import HTTPRequest, HTTPResponse
from service.collectors.tcp_fingerprinter import TCPFingerprinter
from service.collectors.sni_extractor import SNIExtractor
from service.collectors.ja3_fingerprinter import JA3Fingerprinter
import logging
from collections import defaultdict
import time

# Try to import TLS support, but make it optional
try:
    from scapy.layers.tls.record import TLS
    TLS_AVAILABLE = True
except ImportError:
    TLS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("TLS support not available - install cryptography package")

logger = logging.getLogger(__name__)

class PacketSniffer:
    """Sniff packets for comprehensive network analysis."""
    
    def __init__(self, traffic_callback, dns_callback, connection_callback, 
                 http_callback, tls_callback, port_scan_callback, 
                 dhcp_callback, icmp_callback, tcp_fingerprint_callback, sni_callback, ja3_callback):
        self.traffic_callback = traffic_callback
        self.dns_callback = dns_callback
        self.connection_callback = connection_callback
        self.http_callback = http_callback
        self.tls_callback = tls_callback
        self.port_scan_callback = port_scan_callback
        self.dhcp_callback = dhcp_callback
        self.icmp_callback = icmp_callback
        self.tcp_fingerprint_callback = tcp_fingerprint_callback
        self.sni_callback = sni_callback
        self.ja3_callback = ja3_callback
        
        self.stats = defaultdict(lambda: {
            'sent': 0, 'received': 0, 
            'packets_sent': 0, 'packets_received': 0
        })
        
        # Track TCP/IP fingerprinting
        self.tcp_fingerprinter = TCPFingerprinter(tcp_fingerprint_callback)
        
        # Track SNI extraction
        self.sni_extractor = SNIExtractor(sni_callback)
        
        # Track JA3 fingerprinting
        self.ja3_fingerprinter = JA3Fingerprinter(ja3_callback)
        
        # Track port scan attempts
        self.port_attempts = defaultdict(lambda: defaultdict(set))
        self.last_scan_check = time.time()
    
    def handle_packet(self, packet):
        """Handle captured packet."""
        if not packet.haslayer(IP):
            return
        
        ip_layer = packet[IP]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        packet_size = len(packet)
        
        # TCP/IP fingerprinting (passive OS detection)
        if packet.haslayer(TCP):
            self.tcp_fingerprinter.fingerprint_packet(packet)
            
            # SNI extraction from TLS handshakes
            self.sni_extractor.process_packet(packet)
            
            # JA3 fingerprinting from TLS handshakes
            self.ja3_fingerprinter.process_packet(packet)
        
        # Update traffic stats
        self.stats[src_ip]['sent'] += packet_size
        self.stats[src_ip]['packets_sent'] += 1
        self.stats[dst_ip]['received'] += packet_size
        self.stats[dst_ip]['packets_received'] += 1
        
        # Track TCP/UDP connections
        if packet.haslayer(TCP) or packet.haslayer(UDP):
            protocol = 'TCP' if packet.haslayer(TCP) else 'UDP'
            layer = packet[TCP] if packet.haslayer(TCP) else packet[UDP]
            
            self.connection_callback(
                src_ip=src_ip,
                src_port=layer.sport,
                dst_ip=dst_ip,
                dst_port=layer.dport,
                protocol=protocol,
                bytes_sent=packet_size
            )
            
            # Detect port scanning
            if packet.haslayer(TCP):
                tcp = packet[TCP]
                if tcp.flags == 'S':  # SYN packet
                    self.port_attempts[src_ip][dst_ip].add(layer.dport)
                    
                    # Check for scan pattern (5+ ports in 10 seconds)
                    if len(self.port_attempts[src_ip][dst_ip]) >= 5:
                        self.port_scan_callback(src_ip, dst_ip, list(self.port_attempts[src_ip][dst_ip]))
        
        # Track DNS queries
        if packet.haslayer(DNS) and packet.haslayer(DNSQR):
            dns_layer = packet[DNS]
            if dns_layer.qr == 0:  # Query
                query = dns_layer.qd.qname.decode('utf-8').rstrip('.')
                query_type = dns_layer.qd.qtype
                self.dns_callback(src_ip, query, query_type)
        
        # Track HTTP metadata
        if packet.haslayer(HTTPRequest):
            http = packet[HTTPRequest]
            method = http.Method.decode() if http.Method else None
            host = http.Host.decode() if http.Host else None
            path = http.Path.decode() if http.Path else None
            user_agent = http.User_Agent.decode() if http.User_Agent else None
            referer = http.Referer.decode() if hasattr(http, 'Referer') and http.Referer else None
            
            # Build full URL
            full_url = f"http://{host}{path}" if host and path else None
            
            self.http_callback(
                src_ip=src_ip,
                method=method,
                host=host,
                path=path,
                full_url=full_url,
                user_agent=user_agent,
                referer=referer
            )
        
        # Track TLS/SSL
        if TLS_AVAILABLE and packet.haslayer(TLS):
            try:
                tls = packet[TLS]
                self.tls_callback(
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    tls_version=str(tls.version) if hasattr(tls, 'version') else None
                )
            except:
                pass
        
        # Track DHCP events
        if packet.haslayer(DHCP):
            try:
                dhcp_options = packet[DHCP].options
                for opt in dhcp_options:
                    if isinstance(opt, tuple) and opt[0] == 'message-type':
                        self.dhcp_callback(src_ip, opt[1], packet)
            except:
                pass
        
        # Track ICMP
        if packet.haslayer(ICMP):
            icmp = packet[ICMP]
            self.icmp_callback(src_ip, dst_ip, icmp.type, icmp.code)
    
    def check_port_scans(self):
        """Periodically clean up port scan tracking."""
        current_time = time.time()
        if current_time - self.last_scan_check > 10:
            self.port_attempts.clear()
            self.last_scan_check = current_time
    
    def get_stats(self):
        """Get current traffic stats."""
        return dict(self.stats)
    
    def reset_stats(self):
        """Reset traffic stats."""
        self.stats.clear()
    
    def start(self, interface=None):
        """Start packet sniffing."""
        logger.info(f"Starting packet sniffer on interface: {interface or 'all'}")
        sniff(
            prn=self.handle_packet,
            iface=interface,
            store=0
        )
