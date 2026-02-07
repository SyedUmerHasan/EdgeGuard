"""Fing-like device discovery API endpoints."""
from fastapi import APIRouter
from shared.database import get_connection
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from service.device_signatures import identify_device, DEVICE_CATEGORIES

router = APIRouter(prefix="/discover", tags=["discovery"])

@router.get("/devices")
def discover_all_devices():
    """Get all discovered devices with Fing-like identification."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all devices with their data
    cursor.execute("""
        SELECT 
            d.id,
            d.ip_address,
            d.mac_address,
            d.hostname,
            d.vendor,
            d.device_name,
            d.device_type,
            d.os_name,
            d.open_ports,
            d.first_seen,
            d.last_seen,
            d.packets_sent,
            d.packets_received,
            d.bytes_sent,
            d.bytes_received
        FROM devices d
        ORDER BY d.last_seen DESC
    """)
    
    devices = []
    for row in cursor.fetchall():
        device_id, ip, mac, hostname, vendor, device_name, device_type, os_name, \
        open_ports, first_seen, last_seen, pkts_sent, pkts_recv, bytes_sent, bytes_recv = row
        
        # Get DNS domains for this device
        cursor.execute("""
            SELECT DISTINCT domain 
            FROM dns_queries 
            WHERE device_id = ? 
              AND domain NOT LIKE '%.in-addr.arpa'
              AND domain NOT LIKE '%.local'
            LIMIT 10
        """, (device_id,))
        dns_domains = [r[0] for r in cursor.fetchall()]
        
        # Parse open ports
        ports = []
        if open_ports:
            try:
                ports = [int(p.strip()) for p in open_ports.split(',') if p.strip()]
            except:
                pass
        
        # Identify device
        identification = identify_device(vendor, dns_domains, ports, hostname)
        
        # Calculate online status (seen in last 5 minutes)
        from datetime import datetime, timedelta
        try:
            last_seen_dt = datetime.fromisoformat(last_seen)
            is_online = (datetime.now() - last_seen_dt) < timedelta(minutes=5)
        except:
            is_online = False
        
        devices.append({
            'ip_address': ip,
            'mac_address': mac,
            'hostname': hostname or 'Unknown',
            'vendor': vendor or 'Unknown',
            'device_type': identification['device_type'],
            'category': identification['category'],
            'icon': identification['icon'],
            'confidence': identification['confidence'],
            'os': os_name,
            'open_ports': ports,
            'dns_domains': dns_domains,
            'is_online': is_online,
            'first_seen': first_seen,
            'last_seen': last_seen,
            'traffic': {
                'packets_sent': pkts_sent or 0,
                'packets_received': pkts_recv or 0,
                'bytes_sent': bytes_sent or 0,
                'bytes_received': bytes_recv or 0
            }
        })
    
    conn.close()
    
    # Group by category
    by_category = {}
    for device in devices:
        cat = device['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(device)
    
    return {
        'total_devices': len(devices),
        'online_devices': sum(1 for d in devices if d['is_online']),
        'devices': devices,
        'by_category': by_category,
        'categories': DEVICE_CATEGORIES
    }

@router.get("/device/{ip}")
def get_device_details(ip: str):
    """Get detailed information about a specific device."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get device
    cursor.execute("""
        SELECT 
            d.id, d.ip_address, d.mac_address, d.hostname, d.vendor,
            d.device_name, d.device_type, d.os_name, d.open_ports,
            d.first_seen, d.last_seen, d.packets_sent, d.packets_received,
            d.bytes_sent, d.bytes_received, d.ja3_hash
        FROM devices d
        WHERE d.ip_address = ?
    """, (ip,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {'error': 'Device not found'}
    
    device_id = row[0]
    
    # Get DNS queries
    cursor.execute("""
        SELECT domain, COUNT(*) as count, MAX(timestamp) as last_seen
        FROM dns_queries
        WHERE device_id = ?
          AND domain NOT LIKE '%.in-addr.arpa'
          AND domain NOT LIKE '%.local'
        GROUP BY domain
        ORDER BY count DESC
        LIMIT 20
    """, (device_id,))
    dns_queries = [{'domain': r[0], 'count': r[1], 'last_seen': r[2]} for r in cursor.fetchall()]
    
    # Get connections
    cursor.execute("""
        SELECT protocol, dst_ip, dst_port, COUNT(*) as count
        FROM connections
        WHERE device_id = ?
        GROUP BY protocol, dst_ip, dst_port
        ORDER BY count DESC
        LIMIT 20
    """, (device_id,))
    connections = [{'protocol': r[0], 'dst_ip': r[1], 'dst_port': r[2], 'count': r[3]} for r in cursor.fetchall()]
    
    # Get services discovered
    cursor.execute("""
        SELECT service_type, service_name, service_info
        FROM service_discovery
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (device_id,))
    services = [{'type': r[0], 'name': r[1], 'info': r[2]} for r in cursor.fetchall()]
    
    conn.close()
    
    # Parse ports
    ports = []
    if row[8]:
        try:
            ports = [int(p.strip()) for p in row[8].split(',') if p.strip()]
        except:
            pass
    
    # Identify device
    dns_domains = [q['domain'] for q in dns_queries]
    identification = identify_device(row[4], dns_domains, ports, row[3])
    
    return {
        'ip_address': row[1],
        'mac_address': row[2],
        'hostname': row[3],
        'vendor': row[4],
        'device_type': identification['device_type'],
        'category': identification['category'],
        'icon': identification['icon'],
        'confidence': identification['confidence'],
        'os': row[7],
        'open_ports': ports,
        'ja3_hash': row[15],
        'first_seen': row[9],
        'last_seen': row[10],
        'traffic': {
            'packets_sent': row[11] or 0,
            'packets_received': row[12] or 0,
            'bytes_sent': row[13] or 0,
            'bytes_received': row[14] or 0
        },
        'dns_queries': dns_queries,
        'connections': connections,
        'services': services
    }

@router.get("/categories")
def get_categories():
    """Get all device categories with counts."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, vendor FROM devices")
    devices = cursor.fetchall()
    conn.close()
    
    category_counts = {}
    for device_id, vendor in devices:
        identification = identify_device(vendor, [], [], None)
        cat = identification['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    categories = []
    for cat_id, cat_info in DEVICE_CATEGORIES.items():
        categories.append({
            'id': cat_id,
            'name': cat_info['name'],
            'color': cat_info['color'],
            'count': category_counts.get(cat_id, 0)
        })
    
    return {'categories': categories}
