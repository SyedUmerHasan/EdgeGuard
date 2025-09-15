"""Threat management endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import get_connection
from api.models.schemas import Threat

router = APIRouter(prefix="/threats", tags=["threats"])

@router.get("/", response_model=List[Threat])
def get_threats(unresolved_only: bool = False):
    """Get all threats."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM threats"
    if unresolved_only:
        query += " WHERE resolved = 0"
    query += " ORDER BY detected_at DESC"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    threats = []
    for row in rows:
        threats.append(Threat(
            id=row[0],
            device_id=row[1],
            threat_type=row[2],
            severity=row[3],
            description=row[4],
            detected_at=row[5],
            resolved=bool(row[6])
        ))
    
    return threats

@router.patch("/{threat_id}/resolve")
def resolve_threat(threat_id: int):
    """Mark threat as resolved."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE threats SET resolved = 1 WHERE id = ?", (threat_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Threat not found")
    
    conn.close()
    return {"status": "resolved"}
