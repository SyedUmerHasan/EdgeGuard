#!/usr/bin/env python3
"""
EdgeGuard - Home IoT AI Threat Detector
A lightweight tool for detecting IoT threats using local AI analysis
"""

import time
import json
import requests
from scapy.all import sniff, IP, TCP, UDP
from datetime import datetime
import threading
import signal
import sys

class EdgeGuard:
    def __init__(self):
        self.packet_count = 0
        self.traffic_summary = {}
        self.running = True
        
    def analyze_with_llm(self, traffic_data):
        """Send traffic summary to local Ollama for analysis"""
        prompt = f"""
        Analyze this home network traffic summary for suspicious IoT activity:
        
        Traffic Data:
        {json.dumps(traffic_data, indent=2)}
        
        Rate suspicion level 1-10 and explain if this looks like:
        - Botnet command & control
        - Port scanning
        - Unusual data exfiltration
        - AI-powered attack patterns
        
        Respond in JSON format: {{"suspicion_level": X, "analysis": "explanation", "threat_type": "type or none"}}
        """
        
        try:
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2:3b',
                    'prompt': prompt,
                    'stream': False
                })
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No analysis available')
            else:
                return f"LLM Error: {response.status_code}"
                
        except Exception as e:
            return f"Connection Error: {str(e)}"
    
    def packet_handler(self, packet):
        """Process captured packets"""
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            
            # Track traffic patterns
            key = f"{src_ip}->{dst_ip}"
            if key not in self.traffic_summary:
                self.traffic_summary[key] = {
                    'packet_count': 0,
                    'total_bytes': 0,
                    'ports': set(),
                    'protocols': set()
                }
            
            self.traffic_summary[key]['packet_count'] += 1
            self.traffic_summary[key]['total_bytes'] += len(packet)
            
            if TCP in packet:
                self.traffic_summary[key]['ports'].add(packet[TCP].dport)
                self.traffic_summary[key]['protocols'].add('TCP')
            elif UDP in packet:
                self.traffic_summary[key]['ports'].add(packet[UDP].dport)
                self.traffic_summary[key]['protocols'].add('UDP')
            
            self.packet_count += 1
            
            # Analyze every 50 packets
            if self.packet_count % 50 == 0:
                self.analyze_traffic()
    
    def analyze_traffic(self):
        """Analyze collected traffic with LLM"""
        if not self.traffic_summary:
            return
            
        # Convert sets to lists for JSON serialization
        analysis_data = {}
        for key, data in self.traffic_summary.items():
            analysis_data[key] = {
                'packet_count': data['packet_count'],
                'total_bytes': data['total_bytes'],
                'ports': list(data['ports']),
                'protocols': list(data['protocols'])
            }
        
        print(f"\n[{datetime.now()}] Analyzing {self.packet_count} packets...")
        analysis = self.analyze_with_llm(analysis_data)
        print(f"LLM Analysis: {analysis}")
        
        # Log to file
        with open('logs/analysis.log', 'a') as f:
            f.write(f"{datetime.now()}: {analysis}\n")
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\nShutting down EdgeGuard...")
        self.running = False
        sys.exit(0)
    
    def start_monitoring(self):
        """Start packet capture and monitoring"""
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("EdgeGuard starting...")
        print("Monitoring network traffic for IoT threats...")
        print("Press Ctrl+C to stop")
        
        try:
            sniff(prn=self.packet_handler, store=0)
        except PermissionError:
            print("Error: Need sudo privileges for packet capture")
            print("Run: sudo python3 main.py")

if __name__ == "__main__":
    guard = EdgeGuard()
    guard.start_monitoring()
