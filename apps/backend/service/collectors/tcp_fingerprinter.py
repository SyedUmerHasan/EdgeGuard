"""TCP/IP stack fingerprinting for OS detection."""
from scapy.all import TCP, IP
import logging

logger = logging.getLogger(__name__)

class TCPFingerprinter:
    """Passive TCP/IP stack fingerprinting for OS detection."""
    
    # OS signatures database
    OS_SIGNATURES = {
        # Windows
        (128, 8192): "Windows 10/11",
        (128, 65535): "Windows Server",
        (128, 16384): "Windows 7/8",
        
        # Linux/Android
        (64, 5840): "Linux 2.4-2.6",
        (64, 5720): "Linux 3.x-4.x",
        (64, 29200): "Linux 5.x+",
        (64, 14600): "Android",
        
        # iOS/macOS
        (64, 65535): "iOS/macOS",
        
        # Other
        (255, 4128): "Cisco IOS",
        (64, 5840): "FreeBSD",
        (255, 8760): "Solaris",
    }
    
    def __init__(self, callback):
        self.callback = callback
        self.fingerprinted = set()  # Track already fingerprinted IPs
    
    def fingerprint_packet(self, packet):
        """Extract TCP/IP fingerprint from packet."""
        if not (packet.haslayer(IP) and packet.haslayer(TCP)):
            return None
        
        ip = packet[IP]
        tcp = packet[TCP]
        src_ip = ip.src
        
        # Only fingerprint SYN packets (connection initiation)
        if tcp.flags != 'S':
            return None
        
        # Skip if already fingerprinted
        if src_ip in self.fingerprinted:
            return None
        
        # Extract fingerprint features
        ttl = ip.ttl
        window = tcp.window
        
        # Extract TCP options
        options = []
        if tcp.options:
            for opt in tcp.options:
                if isinstance(opt, tuple):
                    options.append(opt[0])
                else:
                    options.append(str(opt))
        
        # Get MSS (Maximum Segment Size)
        mss = None
        for opt in tcp.options:
            if isinstance(opt, tuple) and opt[0] == 'MSS':
                mss = opt[1]
                break
        
        # Identify OS
        os_guess = self.identify_os(ttl, window, options, mss)
        
        if os_guess:
            self.fingerprinted.add(src_ip)
            self.callback(
                ip_address=src_ip,
                os_name=os_guess,
                ttl=ttl,
                window_size=window,
                tcp_options=','.join(options),
                mss=mss
            )
            logger.info(f"TCP/IP fingerprint: {src_ip} -> {os_guess} (TTL={ttl}, Win={window})")
            return os_guess
        
        return None
    
    def identify_os(self, ttl, window, options, mss):
        """Identify OS from TCP/IP characteristics."""
        # Normalize TTL (account for hops)
        if ttl <= 64:
            normalized_ttl = 64
        elif ttl <= 128:
            normalized_ttl = 128
        else:
            normalized_ttl = 255
        
        # Check signature database
        signature = (normalized_ttl, window)
        if signature in self.OS_SIGNATURES:
            return self.OS_SIGNATURES[signature]
        
        # Fallback to TTL-based detection
        if normalized_ttl == 128:
            return "Windows (Unknown Version)"
        elif normalized_ttl == 64:
            # Distinguish between Linux/Android and iOS/macOS
            if window == 65535:
                return "iOS/macOS"
            elif window < 10000:
                return "Linux/Android"
            else:
                return "Linux (Unknown Version)"
        elif normalized_ttl == 255:
            return "Network Device (Cisco/Router)"
        
        return "Unknown OS"
    
    def reset_cache(self):
        """Reset fingerprinted IPs cache."""
        self.fingerprinted.clear()
