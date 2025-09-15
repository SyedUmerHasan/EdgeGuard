"""Active port scanner for deep device discovery."""
from scapy.all import IP, TCP, sr1, ICMP
import logging
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class PortScanner:
    """Active port scanning for service discovery."""
    
    # Common ports to scan
    COMMON_PORTS = [
        21,    # FTP
        22,    # SSH
        23,    # Telnet
        25,    # SMTP
        53,    # DNS
        80,    # HTTP
        443,   # HTTPS
        445,   # SMB
        554,   # RTSP (cameras)
        1883,  # MQTT (IoT)
        3389,  # RDP
        5000,  # UPnP
        5353,  # mDNS
        8080,  # HTTP Alt
        8443,  # HTTPS Alt
        8883,  # MQTT SSL
    ]
    
    def __init__(self, callback):
        self.callback = callback
    
    def scan_port(self, ip, port, timeout=1):
        """Scan single port using SYN scan."""
        try:
            # Send SYN packet
            pkt = IP(dst=ip)/TCP(dport=port, flags='S')
            resp = sr1(pkt, timeout=timeout, verbose=0)
            
            if resp is None:
                return None  # No response (filtered)
            
            if resp.haslayer(TCP):
                if resp[TCP].flags == 0x12:  # SYN-ACK
                    # Send RST to close connection
                    rst = IP(dst=ip)/TCP(dport=port, flags='R')
                    sr1(rst, timeout=0.5, verbose=0)
                    return 'open'
                elif resp[TCP].flags == 0x14:  # RST-ACK
                    return 'closed'
            
            return None
            
        except Exception as e:
            logger.debug(f"Port scan error {ip}:{port} - {e}")
            return None
    
    def scan_host(self, ip, ports=None, max_workers=10):
        """Scan multiple ports on a host."""
        if ports is None:
            ports = self.COMMON_PORTS
        
        logger.info(f"Scanning {ip} for {len(ports)} ports...")
        
        open_ports = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.scan_port, ip, port): port for port in ports}
            
            for future in futures:
                port = futures[future]
                try:
                    result = future.result()
                    if result == 'open':
                        open_ports.append(port)
                        logger.info(f"Found open port: {ip}:{port}")
                except Exception as e:
                    logger.debug(f"Scan error: {e}")
        
        if open_ports:
            self.callback(ip, open_ports)
        
        return open_ports
    
    def scan_network(self, ip_list, ports=None):
        """Scan multiple hosts."""
        results = {}
        
        for ip in ip_list:
            open_ports = self.scan_host(ip, ports)
            if open_ports:
                results[ip] = open_ports
            
            # Small delay between hosts
            time.sleep(0.5)
        
        return results
    
    def quick_scan(self, ip):
        """Quick scan of most common ports."""
        quick_ports = [22, 80, 443, 554, 1883, 8080]
        return self.scan_host(ip, quick_ports, max_workers=6)
