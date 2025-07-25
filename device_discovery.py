#!/usr/bin/env python3
"""
EdgeGuard Device Discovery & Fingerprinting
Identifies devices on the network and detects unauthorized access
"""

import subprocess
import socket
import struct
import time
import json
from collections import defaultdict
from datetime import datetime, timedelta
import re

class DeviceDiscovery:
    def __init__(self, local_network=None):
        self.local_network = local_network
        self.known_devices = {}
        self.device_profiles = defaultdict(dict)
        self.unauthorized_devices = []
        self.load_known_devices()
        
    def load_known_devices(self):
        """Load previously discovered devices from file"""
        try:
            with open('known_devices.json', 'r') as f:
                self.known_devices = json.load(f)
        except FileNotFoundError:
            self.known_devices = {}
    
    def save_known_devices(self):
        """Save discovered devices to file"""
        with open('known_devices.json', 'w') as f:
            json.dump(self.known_devices, f, indent=2)
    
    def get_arp_table(self):
        """Get ARP table to discover active devices"""
        devices = {}
        try:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                # Parse: hostname (192.168.1.100) at aa:bb:cc:dd:ee:ff [ether] on wlan0
                match = re.search(r'\(([\d.]+)\) at ([a-f0-9:]{17})', line)
                if match:
                    ip, mac = match.groups()
                    hostname = line.split('(')[0].strip() if '(' in line else 'unknown'
                    devices[ip] = {
                        'mac': mac.upper(),
                        'hostname': hostname,
                        'last_seen': datetime.now().isoformat(),
                        'discovery_method': 'arp'
                    }
        except Exception as e:
            print(f"Error reading ARP table: {e}")
        return devices
    
    def ping_sweep(self, network_range="192.168.1.1-254"):
        """Perform ping sweep to discover active devices"""
        active_ips = []
        try:
            # Simple ping sweep for common ranges
            base_ip = network_range.split('-')[0].rsplit('.', 1)[0]
            start_range = int(network_range.split('-')[0].split('.')[-1])
            end_range = int(network_range.split('-')[1])
            
            for i in range(start_range, min(end_range + 1, start_range + 20)):  # Limit to 20 IPs for speed
                ip = f"{base_ip}.{i}"
                result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    active_ips.append(ip)
        except Exception as e:
            print(f"Error in ping sweep: {e}")
        return active_ips
    
    def fingerprint_device(self, ip, mac, hostname):
        """Create device fingerprint based on network behavior"""
        fingerprint = {
            'ip': ip,
            'mac': mac,
            'hostname': hostname,
            'device_type': self.guess_device_type(hostname, mac),
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'ports_accessed': [],
            'protocols_used': [],
            'data_patterns': {
                'avg_packet_size': 0,
                'traffic_volume': 0,
                'connection_frequency': 0
            }
        }
        return fingerprint
    
    def guess_device_type(self, hostname, mac):
        """Guess device type based on hostname and MAC address"""
        hostname_lower = hostname.lower()
        mac_prefix = mac[:8].upper()
        
        # Common device patterns
        if any(x in hostname_lower for x in ['iphone', 'ipad', 'apple']):
            return 'iOS Device'
        elif any(x in hostname_lower for x in ['android', 'samsung', 'pixel']):
            return 'Android Device'
        elif any(x in hostname_lower for x in ['laptop', 'desktop', 'pc', 'macbook']):
            return 'Computer'
        elif any(x in hostname_lower for x in ['router', 'gateway', 'modem']):
            return 'Network Equipment'
        elif any(x in hostname_lower for x in ['tv', 'roku', 'chromecast', 'firestick']):
            return 'Smart TV/Streaming'
        elif any(x in hostname_lower for x in ['alexa', 'echo', 'google', 'nest']):
            return 'Smart Speaker'
        elif any(x in hostname_lower for x in ['camera', 'doorbell', 'security']):
            return 'Security Device'
        elif any(x in hostname_lower for x in ['thermostat', 'hvac']):
            return 'Smart Thermostat'
        elif any(x in hostname_lower for x in ['light', 'bulb', 'switch']):
            return 'Smart Lighting'
        
        # MAC address OUI lookup (simplified)
        oui_patterns = {
            '00:50:56': 'VMware',
            '08:00:27': 'VirtualBox',
            'B8:27:EB': 'Raspberry Pi',
            'DC:A6:32': 'Raspberry Pi',
            'E4:5F:01': 'Raspberry Pi',
            '00:16:3E': 'Xen Virtual',
            '52:54:00': 'QEMU/KVM'
        }
        
        for oui, device_type in oui_patterns.items():
            if mac.startswith(oui):
                return device_type
        
        return 'Unknown Device'
    
    def discover_devices(self):
        """Main device discovery function"""
        print("🔍 Discovering devices on network...")
        
        # Get devices from ARP table
        arp_devices = self.get_arp_table()
        
        # Perform ping sweep for additional discovery
        if self.local_network:
            network_base = self.local_network.split('/')[0].rsplit('.', 1)[0]
            active_ips = self.ping_sweep(f"{network_base}.1-50")
        else:
            active_ips = self.ping_sweep()
        
        discovered_devices = {}
        
        # Process ARP table devices
        for ip, device_info in arp_devices.items():
            if ip not in self.known_devices:
                # New device discovered
                fingerprint = self.fingerprint_device(
                    ip, device_info['mac'], device_info['hostname']
                )
                discovered_devices[ip] = fingerprint
                print(f"📱 New device: {ip} ({device_info['hostname']}) - {fingerprint['device_type']}")
            else:
                # Update last seen for known device
                self.known_devices[ip]['last_seen'] = datetime.now().isoformat()
                discovered_devices[ip] = self.known_devices[ip]
        
        # Check for unauthorized devices
        self.check_unauthorized_devices(discovered_devices)
        
        # Update known devices
        self.known_devices.update(discovered_devices)
        self.save_known_devices()
        
        return discovered_devices
    
    def check_unauthorized_devices(self, current_devices):
        """Check for potentially unauthorized devices"""
        suspicious_devices = []
        
        for ip, device in current_devices.items():
            # Check for suspicious patterns
            is_suspicious = False
            reasons = []
            
            # Unknown device type
            if device['device_type'] == 'Unknown Device':
                is_suspicious = True
                reasons.append("Unknown device type")
            
            # Suspicious hostnames
            suspicious_names = ['kali', 'parrot', 'hack', 'pen', 'test', 'attack']
            if any(name in device['hostname'].lower() for name in suspicious_names):
                is_suspicious = True
                reasons.append("Suspicious hostname")
            
            # Virtual machines (could be attacker VMs)
            if device['device_type'] in ['VMware', 'VirtualBox', 'QEMU/KVM']:
                is_suspicious = True
                reasons.append("Virtual machine detected")
            
            # New devices appearing at unusual times (simplified check)
            if ip not in self.known_devices:
                current_hour = datetime.now().hour
                if current_hour < 6 or current_hour > 23:  # Late night/early morning
                    is_suspicious = True
                    reasons.append("Device appeared at unusual time")
            
            if is_suspicious:
                suspicious_devices.append({
                    'ip': ip,
                    'device': device,
                    'reasons': reasons,
                    'risk_level': 'high' if len(reasons) > 1 else 'medium'
                })
        
        self.unauthorized_devices = suspicious_devices
        return suspicious_devices
    
    def get_device_summary(self):
        """Get summary of discovered devices"""
        total_devices = len(self.known_devices)
        device_types = defaultdict(int)
        
        for device in self.known_devices.values():
            device_types[device['device_type']] += 1
        
        summary = {
            'total_devices': total_devices,
            'device_types': dict(device_types),
            'unauthorized_count': len(self.unauthorized_devices),
            'unauthorized_devices': self.unauthorized_devices,
            'last_scan': datetime.now().isoformat()
        }
        
        return summary

if __name__ == "__main__":
    discovery = DeviceDiscovery("10.0.0.0/24")
    devices = discovery.discover_devices()
    summary = discovery.get_device_summary()
    
    print(f"\n📊 Device Summary:")
    print(json.dumps(summary, indent=2))
