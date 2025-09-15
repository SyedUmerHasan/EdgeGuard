"""DNS query endpoints."""
from fastapi import APIRouter
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import get_connection

router = APIRouter(prefix="/dns", tags=["dns"])

@router.get("/queries")
def get_dns_queries(device_id: int = None, limit: int = 100):
    """Get DNS queries."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if device_id:
        cursor.execute("""
            SELECT d.domain, d.query_type, d.timestamp, dev.ip_address, dev.hostname
            FROM dns_queries d
            JOIN devices dev ON d.device_id = dev.id
            WHERE d.device_id = ?
            ORDER BY d.timestamp DESC
            LIMIT ?
        """, (device_id, limit))
    else:
        cursor.execute("""
            SELECT d.domain, d.query_type, d.timestamp, dev.ip_address, dev.hostname
            FROM dns_queries d
            JOIN devices dev ON d.device_id = dev.id
            ORDER BY d.timestamp DESC
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "domain": row[0],
            "query_type": row[1],
            "timestamp": row[2],
            "device_ip": row[3],
            "device_hostname": row[4]
        }
        for row in rows
    ]

@router.get("/top-domains")
def get_top_domains(limit: int = 10):
    """Get most queried domains."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT domain, COUNT(*) as count
        FROM dns_queries
        GROUP BY domain
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"domain": row[0], "count": row[1]} for row in rows]
