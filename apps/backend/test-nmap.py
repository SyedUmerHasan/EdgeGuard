#!/usr/bin/env python3
"""Test nmap scanner."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from service.collectors.nmap_scanner import NmapScanner
from service.collectors.device_tracker import DeviceTracker
from shared.database import init_db

# Initialize database
init_db()

device_tracker = DeviceTracker()

def on_nmap_device(ip, info):
    """Callback for nmap results."""
    print(f"\n{'='*60}")
    print(f"Device: {ip}")
    print(f"  Hostname: {info.get('hostname')}")
    print(f"  MAC: {info.get('mac')}")
    print(f"  Vendor: {info.get('vendor')}")
    print(f"  OS: {info.get('os')}")
    print(f"  State: {info.get('state')}")
    if info.get('ports'):
        print(f"  Open Ports:")
        for port in info['ports']:
            print(f"    - {port['port']}: {port['service']} {port['product']} {port['version']}")
    print('='*60)
    
    # Save to database
    device_tracker.log_nmap_device(ip, info)

# Create scanner
scanner = NmapScanner(on_nmap_device)

# Detect network range
print("Detecting network range...")
import socket
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
network = '.'.join(local_ip.split('.')[:-1]) + '.0/24'

print(f"Scanning network: {network}")
print("This may take 1-2 minutes...\n")

# Run scan
results = scanner.quick_scan(network)

print(f"\n\nScan complete! Found {len(results)} devices")
print("\nCheck database or API for full details")
