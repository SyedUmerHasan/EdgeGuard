#!/usr/bin/env python3
"""
EdgeGuard - Home IoT AI Threat Detector
A lightweight tool for detecting IoT threats using local AI analysis
Enhanced with network routing analysis capabilities
"""

import time
import json
import requests
from scapy.all import sniff, IP, TCP, UDP
from datetime import datetime
import threading
import signal
import sys
from routing_analyzer import NetworkRoutingAnalyzer

class EdgeGuard:
    def __init__(self):
        self.packet_count = 0
        self.traffic_summary = {}
        self.running = True
        self.routing_analyzer = NetworkRoutingAnalyzer()
        print(f"🌐 Network Info: Gateway={self.routing_analyzer.gateway_ip}, Network={self.routing_analyzer.local_network}")
        
    def analyze_with_llm(self, traffic_data, routing_summary):
        """Send traffic summary and routing analysis to local Ollama for analysis"""
        prompt = f"""
        Analyze this home network traffic and routing patterns for suspicious IoT activity:
        
        Traffic Data:
        {json.dumps(traffic_data, indent=2)}
        
        Routing Analysis:
        {json.dumps(routing_summary, indent=2)}
        
        Focus on:
        - Unusual routing patterns or data flows
        - Devices communicating outside normal patterns
        - Potential botnet command & control through routing
        - Suspicious internal network scanning
        - Data exfiltration through routing manipulation
        
        Rate suspicion level 1-10 and explain findings.
        Respond in JSON format: {{"suspicion_level": X, "routing_analysis": "explanation", "threat_type": "type or none", "recommended_action": "action"}}
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
        """Process captured packets with routing analysis"""
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            packet_size = len(packet)
            
            # Determine protocol
            protocol = "OTHER"
            if TCP in packet:
                protocol = "TCP"
            elif UDP in packet:
                protocol = "UDP"
            
            # Analyze routing pattern
            routing_record = self.routing_analyzer.analyze_routing_pattern(
                src_ip, dst_ip, packet_size, protocol
            )
            
            # Track traffic patterns (existing logic)
            key = f"{src_ip}->{dst_ip}"
            if key not in self.traffic_summary:
                self.traffic_summary[key] = {
                    'packet_count': 0,
                    'total_bytes': 0,
                    'ports': set(),
                    'protocols': set(),
                    'flow_type': routing_record['flow_type']  # Add flow type
                }
            
            self.traffic_summary[key]['packet_count'] += 1
            self.traffic_summary[key]['total_bytes'] += packet_size
            
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
        """Analyze collected traffic with routing patterns and LLM"""
        if not self.traffic_summary:
            return
            
        # Convert sets to lists for JSON serialization
        analysis_data = {}
        for key, data in self.traffic_summary.items():
            analysis_data[key] = {
                'packet_count': data['packet_count'],
                'total_bytes': data['total_bytes'],
                'ports': list(data['ports']),
                'protocols': list(data['protocols']),
                'flow_type': data.get('flow_type', 'unknown')
            }
        
        # Get routing analysis summary
        routing_summary = self.routing_analyzer.get_routing_summary()
        
        print(f"\n[{datetime.now()}] 🔍 Analyzing {self.packet_count} packets...")
        print(f"📊 Routing Summary: {routing_summary['total_flows']} flows, {routing_summary['suspicious_count']} suspicious")
        
        # Enhanced logging with routing details
        if routing_summary['suspicious_patterns']:
            print("⚠️  SUSPICIOUS ROUTING DETECTED:")
            for pattern in routing_summary['suspicious_patterns']:
                print(f"   {pattern['severity'].upper()}: {pattern['description']}")
        
        # Send to LLM for analysis
        analysis = self.analyze_with_llm(analysis_data, routing_summary)
        print(f"🤖 AI Analysis: {analysis}")
        
        # Log to file
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'packet_count': self.packet_count,
            'routing_summary': routing_summary,
            'ai_analysis': analysis
        }
        
        with open('logs/analysis.log', 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")
    
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
