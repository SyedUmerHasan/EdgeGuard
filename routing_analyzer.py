#!/usr/bin/env python3
"""
EdgeGuard Network Routing Analyzer
Tracks data routing patterns and identifies suspicious network flows
"""

import subprocess
import socket
import struct
import time
from collections import defaultdict
from datetime import datetime
import json

class NetworkRoutingAnalyzer:
    def __init__(self):
        self.routing_table = {}
        self.flow_patterns = defaultdict(list)
        self.gateway_ip = self.get_default_gateway()
        self.local_network = self.get_local_network()
        
    def get_default_gateway(self):
        """Get the default gateway IP address"""
        try:
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True)
            if result.stdout:
                # Parse: default via 192.168.1.1 dev wlan0
                parts = result.stdout.split()
                if 'via' in parts:
                    gateway_idx = parts.index('via') + 1
                    return parts[gateway_idx]
        except Exception as e:
            print(f"Error getting gateway: {e}")
        return None
    
    def get_local_network(self):
        """Get local network CIDR"""
        try:
            result = subprocess.run(['ip', 'route', 'show'], 
                                  capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'src' in line and not 'default' in line:
                    # Parse: 192.168.1.0/24 dev wlan0 proto kernel scope link src 192.168.1.100
                    parts = line.split()
                    if '/' in parts[0]:
                        return parts[0]  # Return CIDR like 192.168.1.0/24
        except Exception as e:
            print(f"Error getting local network: {e}")
        return None
    
    def is_local_ip(self, ip):
        """Check if IP is in local network"""
        if not self.local_network:
            return ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.')
        
        try:
            network, prefix = self.local_network.split('/')
            network_int = struct.unpack("!I", socket.inet_aton(network))[0]
            ip_int = struct.unpack("!I", socket.inet_aton(ip))[0]
            mask = (0xffffffff >> (32 - int(prefix))) << (32 - int(prefix))
            return (network_int & mask) == (ip_int & mask)
        except:
            return False
    
    def analyze_routing_pattern(self, src_ip, dst_ip, packet_size, protocol):
        """Analyze routing patterns for suspicious behavior"""
        timestamp = datetime.now()
        
        # Determine flow direction
        src_local = self.is_local_ip(src_ip)
        dst_local = self.is_local_ip(dst_ip)
        
        if src_local and dst_local:
            flow_type = "internal"
        elif src_local and not dst_local:
            flow_type = "outbound"
        elif not src_local and dst_local:
            flow_type = "inbound"
        else:
            flow_type = "transit"  # Shouldn't happen in home network
        
        # Create flow record
        flow_record = {
            'timestamp': timestamp.isoformat(),
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'packet_size': packet_size,
            'protocol': protocol,
            'flow_type': flow_type,
            'via_gateway': dst_ip == self.gateway_ip or src_ip == self.gateway_ip
        }
        
        # Store in flow patterns
        flow_key = f"{src_ip}->{dst_ip}"
        self.flow_patterns[flow_key].append(flow_record)
        
        return flow_record
    
    def detect_suspicious_routing(self):
        """Detect suspicious routing patterns"""
        suspicious_patterns = []
        
        for flow_key, records in self.flow_patterns.items():
            if len(records) < 5:  # Need some data to analyze
                continue
                
            # Check for unusual patterns
            recent_records = records[-10:]  # Last 10 records
            
            # Pattern 1: Excessive outbound traffic from single device
            outbound_count = sum(1 for r in recent_records if r['flow_type'] == 'outbound')
            if outbound_count > 7:  # More than 70% outbound
                suspicious_patterns.append({
                    'type': 'excessive_outbound',
                    'flow': flow_key,
                    'severity': 'medium',
                    'description': f'Device {flow_key.split("->")[0]} sending excessive outbound traffic'
                })
            
            # Pattern 2: Unusual internal communication
            internal_count = sum(1 for r in recent_records if r['flow_type'] == 'internal')
            unique_internal_dsts = len(set(r['dst_ip'] for r in recent_records if r['flow_type'] == 'internal'))
            if internal_count > 5 and unique_internal_dsts > 3:
                suspicious_patterns.append({
                    'type': 'internal_scanning',
                    'flow': flow_key,
                    'severity': 'high',
                    'description': f'Possible internal network scanning from {flow_key.split("->")[0]}'
                })
            
            # Pattern 3: Large data transfers
            total_bytes = sum(r['packet_size'] for r in recent_records)
            if total_bytes > 1000000:  # > 1MB in recent packets
                suspicious_patterns.append({
                    'type': 'large_transfer',
                    'flow': flow_key,
                    'severity': 'medium',
                    'description': f'Large data transfer detected: {total_bytes/1024/1024:.2f}MB'
                })
        
        return suspicious_patterns
    
    def get_routing_summary(self):
        """Get summary of routing patterns"""
        summary = {
            'gateway_ip': self.gateway_ip,
            'local_network': self.local_network,
            'total_flows': len(self.flow_patterns),
            'flow_types': defaultdict(int),
            'top_talkers': {},
            'suspicious_count': 0
        }
        
        # Analyze flow types
        for records in self.flow_patterns.values():
            for record in records:
                summary['flow_types'][record['flow_type']] += 1
        
        # Find top talkers (most active IPs)
        ip_activity = defaultdict(int)
        for flow_key in self.flow_patterns.keys():
            src_ip = flow_key.split('->')[0]
            ip_activity[src_ip] += len(self.flow_patterns[flow_key])
        
        # Get top 5 most active IPs
        summary['top_talkers'] = dict(sorted(ip_activity.items(), 
                                           key=lambda x: x[1], reverse=True)[:5])
        
        # Count suspicious patterns
        suspicious = self.detect_suspicious_routing()
        summary['suspicious_count'] = len(suspicious)
        summary['suspicious_patterns'] = suspicious
        
        return summary

if __name__ == "__main__":
    analyzer = NetworkRoutingAnalyzer()
    print(f"Gateway: {analyzer.gateway_ip}")
    print(f"Local Network: {analyzer.local_network}")
    
    # Test with some sample data
    analyzer.analyze_routing_pattern("192.168.1.100", "8.8.8.8", 1500, "TCP")
    analyzer.analyze_routing_pattern("192.168.1.101", "192.168.1.100", 500, "UDP")
    
    summary = analyzer.get_routing_summary()
    print(json.dumps(summary, indent=2))
