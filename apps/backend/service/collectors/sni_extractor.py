"""SNI (Server Name Indication) extraction from TLS handshakes."""
from scapy.all import TCP, Raw
import logging

logger = logging.getLogger(__name__)

class SNIExtractor:
    """Extract domain names from TLS Client Hello (SNI)."""
    
    def __init__(self, callback):
        self.callback = callback
        self.seen_domains = set()
    
    def extract_sni(self, packet):
        """Extract SNI from TLS Client Hello packet."""
        if not (packet.haslayer(TCP) and packet.haslayer(Raw)):
            return None
        
        try:
            payload = bytes(packet[Raw].load)
            
            # Check if it's a TLS handshake (0x16 = Handshake)
            if len(payload) < 5 or payload[0] != 0x16:
                return None
            
            # Check TLS version (0x0301 = TLS 1.0, 0x0303 = TLS 1.2, 0x0304 = TLS 1.3)
            if payload[1] not in [0x03]:
                return None
            
            # Skip to handshake type (should be 0x01 = Client Hello)
            if len(payload) < 6 or payload[5] != 0x01:
                return None
            
            # Parse TLS Client Hello to find SNI extension
            # Skip: content type(1) + version(2) + length(2) + handshake type(1) + length(3) + version(2) + random(32)
            pos = 43
            
            if len(payload) < pos + 1:
                return None
            
            # Session ID length
            session_id_length = payload[pos]
            pos += 1 + session_id_length
            
            if len(payload) < pos + 2:
                return None
            
            # Cipher suites length
            cipher_suites_length = (payload[pos] << 8) | payload[pos + 1]
            pos += 2 + cipher_suites_length
            
            if len(payload) < pos + 1:
                return None
            
            # Compression methods length
            compression_length = payload[pos]
            pos += 1 + compression_length
            
            if len(payload) < pos + 2:
                return None
            
            # Extensions length
            extensions_length = (payload[pos] << 8) | payload[pos + 1]
            pos += 2
            
            # Parse extensions to find SNI (type 0x0000)
            extensions_end = pos + extensions_length
            
            while pos + 4 <= extensions_end and pos + 4 <= len(payload):
                ext_type = (payload[pos] << 8) | payload[pos + 1]
                ext_length = (payload[pos + 2] << 8) | payload[pos + 3]
                pos += 4
                
                # SNI extension (type 0)
                if ext_type == 0 and pos + ext_length <= len(payload):
                    # Skip list length (2 bytes) and name type (1 byte)
                    if ext_length > 5:
                        name_length = (payload[pos + 3] << 8) | payload[pos + 4]
                        if pos + 5 + name_length <= len(payload):
                            sni = payload[pos + 5:pos + 5 + name_length].decode('utf-8', errors='ignore')
                            return sni
                
                pos += ext_length
            
        except Exception as e:
            logger.debug(f"SNI extraction error: {e}")
        
        return None
    
    def process_packet(self, packet):
        """Process packet and extract SNI if present."""
        sni = self.extract_sni(packet)
        
        if sni and sni not in self.seen_domains:
            self.seen_domains.add(sni)
            
            # Get source IP
            if packet.haslayer('IP'):
                src_ip = packet['IP'].src
                self.callback(src_ip, sni)
                logger.info(f"SNI: {src_ip} -> {sni}")
        
        return sni
