"""Connection tracking endpoints."""
from fastapi import APIRouter
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import get_connection

router = APIRouter(prefix="/connections", tags=["connections"])

@router.get("/")
def get_connections(device_id: int = None, active_only: bool = True):
    """Get network connections."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT c.protocol, c.src_ip, c.src_port, c.dst_ip, c.dst_port, 
               c.bytes_sent, c.bytes_received, c.first_seen, c.last_seen,
               d.hostname, d.vendor
        FROM connections c
        JOIN devices d ON c.device_id = d.id
    """
    
    conditions = []
    params = []
    
    if device_id:
        conditions.append("c.device_id = ?")
        params.append(device_id)
    
    if active_only:
        conditions.append("datetime(c.last_seen) > datetime('now', '-5 minutes')")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY c.last_seen DESC LIMIT 100"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "protocol": row[0],
            "src_ip": row[1],
            "src_port": row[2],
            "dst_ip": row[3],
            "dst_port": row[4],
            "bytes_sent": row[5],
            "bytes_received": row[6],
            "first_seen": row[7],
            "last_seen": row[8],
            "device_hostname": row[9],
            "device_vendor": row[10]
        }
        for row in rows
    ]

@router.get("/top-destinations")
def get_top_destinations(limit: int = 10):
    """Get most contacted destinations."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT dst_ip, dst_port, protocol, COUNT(*) as count, SUM(bytes_sent) as total_bytes
        FROM connections
        GROUP BY dst_ip, dst_port, protocol
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "dst_ip": row[0],
            "dst_port": row[1],
            "protocol": row[2],
            "connection_count": row[3],
            "total_bytes": row[4]
        }
        for row in rows
    ]
