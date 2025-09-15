"""Nmap integration for comprehensive device scanning."""
import nmap
import logging

logger = logging.getLogger(__name__)

class NmapScanner:
    """Comprehensive device scanning using Nmap."""
    
    def __init__(self, callback):
        self.callback = callback
        try:
            self.nm = nmap.PortScanner()
        except nmap.PortScannerError:
            logger.error("Nmap not found. Install with: sudo apt install nmap")
            self.nm = None
    
    def scan_network(self, network='192.168.1.0/24', arguments='-sn'):
        """
        Scan network for devices.
        
        Args:
            network: Network range (e.g., '192.168.1.0/24')
            arguments: Nmap arguments
                -sn: Ping scan (no port scan)
                -O: OS detection
                -sV: Service version detection
                -A: Aggressive scan (OS, version, scripts)
        """
        if not self.nm:
            logger.error("Nmap not available")
            return {}
        
        logger.info(f"Starting Nmap scan: {network} {arguments}")
        
        try:
            self.nm.scan(hosts=network, arguments=arguments)
            
            results = {}
            for host in self.nm.all_hosts():
                host_info = self.process_host(host)
                if host_info:
                    results[host] = host_info
                    self.callback(host, host_info)
            
            logger.info(f"Nmap scan complete: {len(results)} hosts found")
            return results
            
        except Exception as e:
            logger.error(f"Nmap scan error: {e}")
            return {}
    
    def process_host(self, host):
        """Process scanned host information."""
        try:
            if host not in self.nm.all_hosts():
                return None
            
            host_data = self.nm[host]
            
            info = {
                'ip': host,
                'hostname': host_data.hostname() if host_data.hostname() else None,
                'state': host_data.state(),
                'mac': None,
                'vendor': None,
                'os': None,
                'ports': []
            }
            
            # MAC address and vendor
            if 'mac' in host_data['addresses']:
                info['mac'] = host_data['addresses']['mac']
            
            if 'vendor' in host_data and host_data['vendor']:
                info['vendor'] = list(host_data['vendor'].values())[0] if host_data['vendor'] else None
            
            # OS detection
            if 'osmatch' in host_data and host_data['osmatch']:
                info['os'] = host_data['osmatch'][0]['name']
            
            # Open ports
            if 'tcp' in host_data:
                for port, port_info in host_data['tcp'].items():
                    if port_info['state'] == 'open':
                        info['ports'].append({
                            'port': port,
                            'service': port_info.get('name', ''),
                            'product': port_info.get('product', ''),
                            'version': port_info.get('version', '')
                        })
            
            logger.info(f"Nmap: {host} - {info['hostname']} ({info['vendor']})")
            return info
            
        except Exception as e:
            logger.error(f"Error processing host {host}: {e}")
            return None
    
    def quick_scan(self, network='192.168.1.0/24'):
        """Quick ping scan to find active hosts."""
        return self.scan_network(network, '-sn')
    
    def detailed_scan(self, host):
        """Detailed scan of single host."""
        return self.scan_network(host, '-O -sV')
    
    def scan_async(self, network, arguments='-sn'):
        """Async scan in background."""
        import threading
        thread = threading.Thread(
            target=self.scan_network, 
            args=(network, arguments), 
            daemon=True
        )
        thread.start()
        return thread
