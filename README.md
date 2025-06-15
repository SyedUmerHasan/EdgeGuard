# EdgeGuard - Home IoT AI Threat Detector

A lightweight, privacy-preserving AI tool that monitors home network traffic to detect IoT threats using local LLM analysis.

## What It Does

EdgeGuard captures network packet metadata and uses a local AI model (Ollama + Llama 3.2) to analyze traffic patterns for suspicious activity targeting IoT devices and smartphones.

## Why It Matters

- **Privacy-First**: All analysis happens locally - no data sent to cloud
- **National Security**: Protects against IoT botnets that threaten critical infrastructure
- **Accessible**: Runs on affordable hardware (Raspberry Pi, old laptop)
- **Open Source**: MIT licensed for wide adoption

## How to Run

```bash
# Activate environment
source venv/bin/activate

# Run EdgeGuard (requires sudo for packet capture)
sudo python3 main.py
```

## Requirements

- Python 3.8+
- Ollama with llama3.2:3b model
- Root/sudo access for network monitoring

## License

MIT License - See LICENSE file
