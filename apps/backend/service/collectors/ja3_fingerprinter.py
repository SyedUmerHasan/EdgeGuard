"""JA3 TLS fingerprinting for exact browser/application identification."""
from scapy.all import TCP, Raw
import hashlib
import logging

logger = logging.getLogger(__name__)

class JA3Fingerprinter:
    """
    JA3 fingerprinting identifies exact browser/application from TLS handshake.
    Format: SSLVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats
    """
    
    def __init__(self, callback):
        self.callback = callback
        self.seen_fingerprints = {}
    
    def extract_ja3(self, packet):
        """Extract JA3 fingerprint from TLS Client Hello."""
        if not (packet.haslayer(TCP) and packet.haslayer(Raw)):
            return None
        
        try:
            payload = bytes(packet[Raw].load)
            
            # Check if it's a TLS handshake (0x16)
            if len(payload) < 5 or payload[0] != 0x16:
                return None
            
            # Check for Client Hello (0x01)
            if len(payload) < 6 or payload[5] != 0x01:
                return None
            
            # Parse TLS Client Hello
            pos = 1  # Skip content type
            
            # TLS version (2 bytes)
            tls_version = (payload[pos] << 8) | payload[pos + 1]
            pos += 2
            
            # Skip length (2 bytes)
            pos += 2
            
            # Skip handshake type (1 byte)
            pos += 1
            
            # Skip handshake length (3 bytes)
            pos += 3
            
            # Client version (2 bytes)
            client_version = (payload[pos] << 8) | payload[pos + 1]
            pos += 2
            
            # Skip random (32 bytes)
            pos += 32
            
            # Session ID length
            if pos >= len(payload):
                return None
            session_id_length = payload[pos]
            pos += 1 + session_id_length
            
            # Cipher suites
            if pos + 2 > len(payload):
                return None
            cipher_suites_length = (payload[pos] << 8) | payload[pos + 1]
            pos += 2
            
            cipher_suites = []
            cipher_end = pos + cipher_suites_length
            while pos < cipher_end and pos + 2 <= len(payload):
                cipher = (payload[pos] << 8) | payload[pos + 1]
                cipher_suites.append(str(cipher))
                pos += 2
            
            # Compression methods
            if pos >= len(payload):
                return None
            compression_length = payload[pos]
            pos += 1 + compression_length
            
            # Extensions
            if pos + 2 > len(payload):
                return None
            extensions_length = (payload[pos] << 8) | payload[pos + 1]
            pos += 2
            
            extensions = []
            elliptic_curves = []
            ec_point_formats = []
            
            extensions_end = pos + extensions_length
            while pos + 4 <= extensions_end and pos + 4 <= len(payload):
                ext_type = (payload[pos] << 8) | payload[pos + 1]
                ext_length = (payload[pos + 2] << 8) | payload[pos + 3]
                pos += 4
                
                extensions.append(str(ext_type))
                
                # Elliptic curves (extension 10)
                if ext_type == 10 and pos + ext_length <= len(payload):
                    curves_length = (payload[pos] << 8) | payload[pos + 1]
                    curve_pos = pos + 2
                    curve_end = curve_pos + curves_length
                    while curve_pos + 2 <= curve_end and curve_pos + 2 <= len(payload):
                        curve = (payload[curve_pos] << 8) | payload[curve_pos + 1]
                        elliptic_curves.append(str(curve))
                        curve_pos += 2
                
                # EC point formats (extension 11)
                elif ext_type == 11 and pos + ext_length <= len(payload):
                    formats_length = payload[pos]
                    format_pos = pos + 1
                    format_end = format_pos + formats_length
                    while format_pos < format_end and format_pos < len(payload):
                        ec_point_formats.append(str(payload[format_pos]))
                        format_pos += 1
                
                pos += ext_length
            
            # Build JA3 string
            ja3_string = f"{client_version},"
            ja3_string += "-".join(cipher_suites) + ","
            ja3_string += "-".join(extensions) + ","
            ja3_string += "-".join(elliptic_curves) + ","
            ja3_string += "-".join(ec_point_formats)
            
            # Generate JA3 hash
            ja3_hash = hashlib.md5(ja3_string.encode()).hexdigest()
            
            return ja3_hash, ja3_string
            
        except Exception as e:
            logger.debug(f"JA3 extraction error: {e}")
        
        return None
    
    def process_packet(self, packet):
        """Process packet and extract JA3 if present."""
        result = self.extract_ja3(packet)
        
        if result:
            ja3_hash, ja3_string = result
            
            if ja3_hash not in self.seen_fingerprints:
                self.seen_fingerprints[ja3_hash] = ja3_string
                
                # Get source IP
                if packet.haslayer('IP'):
                    src_ip = packet['IP'].src
                    self.callback(src_ip, ja3_hash, ja3_string)
                    logger.info(f"JA3: {src_ip} -> {ja3_hash}")
        
        return result
