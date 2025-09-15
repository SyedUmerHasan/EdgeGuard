"""Device management endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import get_connection
from api.models.schemas import Device

router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("/", response_model=List[Device])
def get_devices(active_only: bool = False):
    """Get all devices."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM devices"
    if active_only:
        query += " WHERE is_active = 1"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    devices = []
    for row in rows:
        devices.append(Device(
            id=row[0],
            mac_address=row[1],
            ip_address=row[2],
            hostname=row[3],
            vendor=row[4],
            device_type=row[5],
            first_seen=row[6],
            last_seen=row[7],
            is_active=bool(row[8])
        ))
    
    return devices

@router.get("/{device_id}", response_model=Device)
def get_device(device_id: int):
    """Get device by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return Device(
        id=row[0],
        mac_address=row[1],
        ip_address=row[2],
        hostname=row[3],
        vendor=row[4],
        device_type=row[5],
        first_seen=row[6],
        last_seen=row[7],
        is_active=bool(row[8])
    )
