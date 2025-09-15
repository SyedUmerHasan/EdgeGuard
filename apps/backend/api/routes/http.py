"""HTTP/URL tracking endpoints."""
from fastapi import APIRouter
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import get_connection

router = APIRouter(prefix="/http", tags=["http"])

@router.get("/urls")
def get_urls(device_id: int = None, limit: int = 100):
    """Get visited URLs."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if device_id:
        cursor.execute("""
            SELECT h.full_url, h.method, h.host, h.path, h.user_agent, h.referer, h.timestamp,
                   d.ip_address, d.hostname, d.vendor
            FROM http_metadata h
            JOIN devices d ON h.device_id = d.id
            WHERE h.device_id = ? AND h.full_url IS NOT NULL
            ORDER BY h.timestamp DESC
            LIMIT ?
        """, (device_id, limit))
    else:
        cursor.execute("""
            SELECT h.full_url, h.method, h.host, h.path, h.user_agent, h.referer, h.timestamp,
                   d.ip_address, d.hostname, d.vendor
            FROM http_metadata h
            JOIN devices d ON h.device_id = d.id
            WHERE h.full_url IS NOT NULL
            ORDER BY h.timestamp DESC
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "url": row[0],
            "method": row[1],
            "host": row[2],
            "path": row[3],
            "user_agent": row[4],
            "referer": row[5],
            "timestamp": row[6],
            "device_ip": row[7],
            "device_hostname": row[8],
            "device_vendor": row[9]
        }
        for row in rows
    ]

@router.get("/top-sites")
def get_top_sites(limit: int = 20):
    """Get most visited websites."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT host, COUNT(*) as visit_count
        FROM http_metadata
        WHERE host IS NOT NULL
        GROUP BY host
        ORDER BY visit_count DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"host": row[0], "visits": row[1]} for row in rows]

@router.get("/user-agents")
def get_user_agents():
    """Get unique user agents (device fingerprinting)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT user_agent, COUNT(*) as count
        FROM http_metadata
        WHERE user_agent IS NOT NULL
        GROUP BY user_agent
        ORDER BY count DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"user_agent": row[0], "count": row[1]} for row in rows]
