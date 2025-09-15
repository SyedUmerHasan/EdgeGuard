"""Visited websites tracking endpoints."""
from fastapi import APIRouter
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import get_connection

router = APIRouter(prefix="/sites", tags=["sites"])

@router.get("/visited")
def get_visited_sites(device_id: int = None, limit: int = 100):
    """Get visited websites from SNI extraction."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if device_id:
        cursor.execute("""
            SELECT v.domain, v.visit_count, v.first_seen, v.last_seen,
                   d.ip_address, d.hostname, d.vendor
            FROM visited_sites v
            JOIN devices d ON v.device_id = d.id
            WHERE v.device_id = ?
            ORDER BY v.last_seen DESC
            LIMIT ?
        """, (device_id, limit))
    else:
        cursor.execute("""
            SELECT v.domain, v.visit_count, v.first_seen, v.last_seen,
                   d.ip_address, d.hostname, d.vendor
            FROM visited_sites v
            JOIN devices d ON v.device_id = d.id
            ORDER BY v.last_seen DESC
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "domain": row[0],
            "visit_count": row[1],
            "first_seen": row[2],
            "last_seen": row[3],
            "device_ip": row[4],
            "device_hostname": row[5],
            "device_vendor": row[6]
        }
        for row in rows
    ]

@router.get("/top-sites")
def get_top_sites(limit: int = 20):
    """Get most visited websites."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT domain, SUM(visit_count) as total_visits
        FROM visited_sites
        GROUP BY domain
        ORDER BY total_visits DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"domain": row[0], "visits": row[1]} for row in rows]

@router.get("/by-device/{device_id}")
def get_sites_by_device(device_id: int):
    """Get all sites visited by specific device."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT domain, visit_count, first_seen, last_seen
        FROM visited_sites
        WHERE device_id = ?
        ORDER BY last_seen DESC
    """, (device_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "domain": row[0],
            "visits": row[1],
            "first_seen": row[2],
            "last_seen": row[3]
        }
        for row in rows
    ]
