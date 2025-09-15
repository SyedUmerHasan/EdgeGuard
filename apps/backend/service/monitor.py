"""Main background monitoring service."""
import logging
import signal
import sys
import time
from pathlib import Path
from threading import Thread

sys.path.append(str(Path(__file__).parent.parent))
from shared.database import init_db
from service.collectors.arp_listener import ARPListener
from service.collectors.packet_sniffer import PacketSniffer
from service.collectors.device_tracker import DeviceTracker
from service.collectors.mdns_listener import MDNSListener
from service.collectors.ssdp_listener import SSDPListener
from service.collectors.dhcp_fingerprinter import DHCPFingerprinter
from service.collectors.port_scanner import PortScanner
from service.collectors.netdisco_scanner import NetdiscoScanner
from service.collectors.nmap_scanner import NmapScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/edgeguard-monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EdgeGuardMonitor:
    """Main monitoring service."""
    
    def __init__(self):
        self.running = False
        self.device_tracker = DeviceTracker()
        self.arp_listener = ARPListener(self.on_device_discovered)
        self.mdns_listener = MDNSListener(self.on_mdns_service)
        self.ssdp_listener = SSDPListener(self.on_ssdp_device)
        self.dhcp_fingerprinter = DHCPFingerprinter(self.on_dhcp_fingerprint)
        self.port_scanner = PortScanner(self.on_ports_discovered)
        self.netdisco_scanner = NetdiscoScanner(self.on_netdisco_device)
        self.nmap_scanner = NmapScanner(self.on_nmap_device)
        self.packet_sniffer = PacketSniffer(
            traffic_callback=self.on_traffic,
            dns_callback=self.on_dns_query,
            connection_callback=self.on_connection,
            http_callback=self.on_http_request,
            tls_callback=self.on_tls_connection,
            port_scan_callback=self.on_port_scan,
            dhcp_callback=self.on_dhcp_event,
            icmp_callback=self.on_icmp_event,
            tcp_fingerprint_callback=self.on_tcp_fingerprint,
            sni_callback=self.on_sni_domain,
            ja3_callback=self.on_ja3_fingerprint
        )
    
    def on_device_discovered(self, mac_address, ip_address):
        """Callback when device is discovered via ARP."""
        self.device_tracker.add_or_update_device(mac_address, ip_address)
    
    def on_traffic(self, ip_address, bytes_sent, bytes_received, packets_sent, packets_received):
        """Callback for traffic statistics."""
        self.device_tracker.update_traffic_stats(ip_address, bytes_sent, bytes_received, packets_sent, packets_received)
    
    def on_dns_query(self, ip_address, domain, query_type):
        """Callback for DNS queries."""
        self.device_tracker.log_dns_query(ip_address, domain, query_type)
    
    def on_connection(self, src_ip, src_port, dst_ip, dst_port, protocol, bytes_sent):
        """Callback for network connections."""
        self.device_tracker.log_connection(src_ip, src_port, dst_ip, dst_port, protocol, bytes_sent)
    
    def on_http_request(self, src_ip, method, host, path, full_url, user_agent, referer):
        """Callback for HTTP requests."""
        self.device_tracker.log_http_metadata(src_ip, method, host, path, full_url, user_agent, referer)
    
    def on_tls_connection(self, src_ip, dst_ip, tls_version):
        """Callback for TLS connections."""
        self.device_tracker.log_tls_metadata(src_ip, dst_ip, tls_version)
    
    def on_port_scan(self, src_ip, target_ip, ports):
        """Callback for port scan detection."""
        self.device_tracker.log_port_scan(src_ip, target_ip, ports)
    
    def on_dhcp_event(self, src_ip, event_type, packet):
        """Callback for DHCP events."""
        self.device_tracker.log_dhcp_event(src_ip, event_type, packet)
    
    def on_icmp_event(self, src_ip, dst_ip, icmp_type, icmp_code):
        """Callback for ICMP events."""
        self.device_tracker.log_icmp_event(src_ip, dst_ip, icmp_type, icmp_code)
    
    def on_mdns_service(self, service_name, service_type, rdata):
        """Callback for mDNS service discovery."""
        # Parse mDNS data for device info
        device_name = None
        device_model = None
        ip_address = None
        
        if isinstance(rdata, list):
            for item in rdata:
                if isinstance(item, bytes):
                    item_str = item.decode('utf-8', errors='ignore')
                    if item_str.startswith('fn='):
                        device_name = item_str[3:]  # Friendly name
                    elif item_str.startswith('md='):
                        device_model = item_str[3:]  # Model
        elif isinstance(rdata, bytes):
            rdata_str = rdata.decode('utf-8', errors='ignore')
            # Check if it's an IP address
            if '.' in rdata_str and not rdata_str.endswith('.local.'):
                ip_address = rdata_str
        
        if device_name or device_model:
            logger.info(f"mDNS device found: {device_name or device_model} ({service_type})")
            # Store in service discovery if we have IP
            if ip_address:
                self.device_tracker.log_service_discovery(
                    ip_address,
                    service_type,
                    device_name or service_name,
                    f"Model: {device_model}" if device_model else None
                )
    
    def on_ssdp_device(self, location, server, usn, device_type, src_ip):
        """Callback for SSDP/UPnP device discovery."""
        self.device_tracker.log_service_discovery(
            src_ip, 
            device_type or 'UPnP Device',
            server or 'Unknown',
            f"Location: {location}, USN: {usn}"
        )
    
    def on_dhcp_fingerprint(self, mac_address, ip_address, hostname, vendor_class, dhcp_fingerprint):
        """Callback for DHCP fingerprinting."""
        self.device_tracker.add_or_update_device(
            mac_address, 
            ip_address, 
            hostname, 
            dhcp_fingerprint, 
            vendor_class
        )
    
    def on_tcp_fingerprint(self, ip_address, os_name, ttl, window_size, tcp_options, mss):
        """Callback for TCP/IP fingerprinting."""
        self.device_tracker.log_tcp_fingerprint(ip_address, os_name, ttl, window_size, tcp_options, mss)
    
    def on_sni_domain(self, ip_address, domain):
        """Callback for SNI domain extraction."""
        self.device_tracker.log_visited_site(ip_address, domain)
    
    def on_ja3_fingerprint(self, ip_address, ja3_hash, ja3_string):
        """Callback for JA3 fingerprinting."""
        self.device_tracker.log_ja3_fingerprint(ip_address, ja3_hash, ja3_string)
    
    def on_ports_discovered(self, ip_address, ports):
        """Callback for discovered open ports."""
        self.device_tracker.log_open_ports(ip_address, ports)
    
    def on_netdisco_device(self, ip_address, device_type, device_name, manufacturer, model, raw_info):
        """Callback for netdisco discovered device."""
        self.device_tracker.log_netdisco_device(ip_address, device_type, device_name, manufacturer, model, raw_info)
    
    def on_nmap_device(self, ip_address, nmap_info):
        """Callback for nmap discovered device."""
        self.device_tracker.log_nmap_device(ip_address, nmap_info)
    
    def run_discovery_scan(self):
        """Run periodic discovery scans."""
        while self.running:
            time.sleep(3600)  # Every hour
            
            logger.info("Running periodic discovery scan...")
            
            # Netdisco scan (10 seconds)
            self.netdisco_scanner.scan_async(duration=10)
            
            # Nmap quick scan (detect network range automatically)
            # TODO: Auto-detect network range from interfaces
            # self.nmap_scanner.scan_async('192.168.1.0/24', '-sn')
    
    def cleanup_inactive_devices(self):
        """Periodically mark inactive devices."""
        while self.running:
            time.sleep(300)  # Every 5 minutes
            self.device_tracker.mark_inactive_devices()
    
    def update_traffic_stats(self):
        """Periodically update traffic stats from sniffer."""
        while self.running:
            time.sleep(60)  # Every minute
            stats = self.packet_sniffer.get_stats()
            for ip, data in stats.items():
                self.device_tracker.update_traffic_stats(
                    ip, 
                    data['sent'], 
                    data['received'],
                    data['packets_sent'],
                    data['packets_received']
                )
            self.packet_sniffer.reset_stats()
    
    def start(self):
        """Start monitoring service."""
        logger.info("Starting EdgeGuard monitoring service...")
        
        # Initialize database
        init_db()
        
        self.running = True
        
        # Start cleanup thread
        cleanup_thread = Thread(target=self.cleanup_inactive_devices, daemon=True)
        cleanup_thread.start()
        
        # Start discovery scan thread
        discovery_thread = Thread(target=self.run_discovery_scan, daemon=True)
        discovery_thread.start()
        
        # Start traffic stats thread
        stats_thread = Thread(target=self.update_traffic_stats, daemon=True)
        stats_thread.start()
        
        # Start ARP listener thread
        arp_thread = Thread(target=self.arp_listener.start, daemon=True)
        arp_thread.start()
        
        # Start mDNS listener thread
        mdns_thread = Thread(target=self.mdns_listener.start, daemon=True)
        mdns_thread.start()
        
        # Start SSDP listener thread
        ssdp_thread = Thread(target=self.ssdp_listener.start, daemon=True)
        ssdp_thread.start()
        
        # Start DHCP fingerprinter thread
        dhcp_thread = Thread(target=self.dhcp_fingerprinter.start, daemon=True)
        dhcp_thread.start()
        
        # Start packet sniffer (blocking)
        try:
            self.packet_sniffer.start()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop monitoring service."""
        logger.info("Stopping EdgeGuard monitoring service...")
        self.running = False

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    monitor = EdgeGuardMonitor()
    monitor.start()
