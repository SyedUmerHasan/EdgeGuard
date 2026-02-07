"""IoT device identification database with known signatures."""

# Device signatures based on vendor, DNS patterns, ports, and services
DEVICE_SIGNATURES = {
    # Smart Home Hubs
    "amazon_echo": {
        "vendors": ["Amazon Technologies"],
        "dns_patterns": ["device-metrics-us", "dp-gw-na", "todo-ta-g7g"],
        "ports": [443, 4070, 33434],
        "device_type": "Smart Speaker",
        "category": "smart_home",
        "icon": "speaker"
    },
    "google_home": {
        "vendors": ["Google", "Nest Labs"],
        "dns_patterns": ["googleusercontent.com", "gvt1.com", "clients.google.com"],
        "ports": [8008, 8009, 443],
        "device_type": "Smart Speaker",
        "category": "smart_home",
        "icon": "speaker"
    },
    
    # Security Cameras & Doorbells
    "ring_doorbell": {
        "vendors": ["Ring LLC", "Ring Solutions"],
        "dns_patterns": ["ring.com", "ring-iot"],
        "ports": [443, 6667],
        "device_type": "Video Doorbell",
        "category": "security",
        "icon": "doorbell"
    },
    "nest_camera": {
        "vendors": ["Nest Labs"],
        "dns_patterns": ["dropcam.com", "nest.com"],
        "ports": [443, 11095],
        "device_type": "Security Camera",
        "category": "security",
        "icon": "camera"
    },
    "arlo_camera": {
        "vendors": ["Arlo Technologies"],
        "dns_patterns": ["arlo.com", "netgear.com"],
        "ports": [443, 80],
        "device_type": "Security Camera",
        "category": "security",
        "icon": "camera"
    },
    
    # Smart Thermostats
    "nest_thermostat": {
        "vendors": ["Nest Labs"],
        "dns_patterns": ["nest.com", "nestlabs.com"],
        "ports": [443, 9543],
        "device_type": "Smart Thermostat",
        "category": "climate",
        "icon": "thermostat"
    },
    "ecobee": {
        "vendors": ["ecobee"],
        "dns_patterns": ["ecobee.com"],
        "ports": [443],
        "device_type": "Smart Thermostat",
        "category": "climate",
        "icon": "thermostat"
    },
    
    # Smart Lights
    "philips_hue": {
        "vendors": ["Philips", "Signify"],
        "dns_patterns": ["meethue.com", "philips-hue"],
        "ports": [80, 443, 2100],
        "device_type": "Smart Light",
        "category": "lighting",
        "icon": "lightbulb"
    },
    "lifx": {
        "vendors": ["LIFX"],
        "dns_patterns": ["lifx.co"],
        "ports": [56700],
        "device_type": "Smart Light",
        "category": "lighting",
        "icon": "lightbulb"
    },
    
    # Smart Plugs & Switches
    "tp_link_plug": {
        "vendors": ["TP-Link"],
        "dns_patterns": ["tplinkcloud.com", "tplinknbu.com"],
        "ports": [9999],
        "device_type": "Smart Plug",
        "category": "power",
        "icon": "plug"
    },
    "wemo": {
        "vendors": ["Belkin"],
        "dns_patterns": ["wemo.com"],
        "ports": [49152, 49153, 49154],
        "device_type": "Smart Plug",
        "category": "power",
        "icon": "plug"
    },
    
    # Smart TVs & Streaming
    "roku": {
        "vendors": ["Roku"],
        "dns_patterns": ["roku.com"],
        "ports": [8060, 8443],
        "device_type": "Streaming Device",
        "category": "entertainment",
        "icon": "tv"
    },
    "chromecast": {
        "vendors": ["Google"],
        "dns_patterns": ["googleusercontent.com", "gvt1.com"],
        "ports": [8008, 8009],
        "device_type": "Streaming Device",
        "category": "entertainment",
        "icon": "cast"
    },
    "apple_tv": {
        "vendors": ["Apple"],
        "dns_patterns": ["apple.com", "icloud.com"],
        "ports": [3689, 5000, 7000],
        "device_type": "Streaming Device",
        "category": "entertainment",
        "icon": "tv"
    },
    
    # Smart Sensors
    "samsung_smartthings": {
        "vendors": ["SAMJIN Co., Ltd.", "Samsung"],
        "dns_patterns": ["smartthings.com"],
        "ports": [443],
        "device_type": "Smart Sensor",
        "category": "sensor",
        "icon": "sensor"
    },
    
    # Routers & Network
    "netgear_router": {
        "vendors": ["NETGEAR", "Netgear"],
        "dns_patterns": ["netgear.com"],
        "ports": [80, 443, 53],
        "device_type": "Router",
        "category": "network",
        "icon": "router"
    },
    
    # Computers & Mobile
    "apple_device": {
        "vendors": ["Apple"],
        "dns_patterns": ["apple.com", "icloud.com", "apple-dns.net"],
        "ports": [5353],
        "device_type": "Apple Device",
        "category": "computer",
        "icon": "laptop"
    },
    "windows_pc": {
        "vendors": ["Microsoft", "Dell", "HP", "Lenovo"],
        "dns_patterns": ["microsoft.com", "windows.com"],
        "ports": [135, 139, 445],
        "device_type": "Windows PC",
        "category": "computer",
        "icon": "desktop"
    },
    
    # IoT Generic
    "esp_device": {
        "vendors": ["Espressif"],
        "dns_patterns": [],
        "ports": [80, 443],
        "device_type": "IoT Device",
        "category": "iot",
        "icon": "chip"
    },
    "texas_instruments": {
        "vendors": ["Texas Instruments"],
        "dns_patterns": [],
        "ports": [],
        "device_type": "IoT Sensor",
        "category": "sensor",
        "icon": "sensor"
    },
    "murata": {
        "vendors": ["Murata Manufacturing"],
        "dns_patterns": [],
        "ports": [],
        "device_type": "IoT Module",
        "category": "iot",
        "icon": "chip"
    }
}

# Category definitions
DEVICE_CATEGORIES = {
    "security": {"name": "Security", "color": "#ef4444"},
    "smart_home": {"name": "Smart Home", "color": "#3b82f6"},
    "climate": {"name": "Climate Control", "color": "#10b981"},
    "lighting": {"name": "Lighting", "color": "#f59e0b"},
    "power": {"name": "Power & Energy", "color": "#8b5cf6"},
    "entertainment": {"name": "Entertainment", "color": "#ec4899"},
    "sensor": {"name": "Sensors", "color": "#06b6d4"},
    "network": {"name": "Network", "color": "#6366f1"},
    "computer": {"name": "Computers", "color": "#64748b"},
    "iot": {"name": "IoT Devices", "color": "#84cc16"}
}

def identify_device(vendor, dns_domains, open_ports, hostname=None):
    """
    Identify device type based on vendor, DNS patterns, and ports.
    
    Returns: {
        'device_id': str,
        'device_type': str,
        'category': str,
        'icon': str,
        'confidence': float (0-1)
    }
    """
    scores = {}
    
    for device_id, signature in DEVICE_SIGNATURES.items():
        score = 0
        max_score = 0
        
        # Vendor match (highest weight)
        if vendor:
            max_score += 3
            for sig_vendor in signature["vendors"]:
                if sig_vendor.lower() in vendor.lower():
                    score += 3
                    break
        
        # DNS pattern match
        if dns_domains:
            max_score += 2
            for pattern in signature["dns_patterns"]:
                if any(pattern.lower() in domain.lower() for domain in dns_domains):
                    score += 2
                    break
        
        # Port match
        if open_ports:
            max_score += 1
            common_ports = set(open_ports) & set(signature["ports"])
            if common_ports:
                score += 1
        
        if max_score > 0:
            confidence = score / max_score
            scores[device_id] = {
                'device_id': device_id,
                'device_type': signature['device_type'],
                'category': signature['category'],
                'icon': signature['icon'],
                'confidence': confidence
            }
    
    # Return best match
    if scores:
        best_match = max(scores.values(), key=lambda x: x['confidence'])
        if best_match['confidence'] >= 0.5:  # At least 50% confidence
            return best_match
    
    # Default unknown device
    return {
        'device_id': 'unknown',
        'device_type': 'Unknown Device',
        'category': 'iot',
        'icon': 'device',
        'confidence': 0.0
    }
