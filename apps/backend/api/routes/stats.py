"""Statistics endpoints."""
from fastapi import APIRouter
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import get_connection
from api.models.schemas import Stats

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/", response_model=Stats)
def get_stats():
    """Get system statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM devices")
    total_devices = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM devices WHERE is_active = 1")
    active_devices = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM threats")
    total_threats = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM threats WHERE resolved = 0")
    unresolved_threats = cursor.fetchone()[0]
    
    conn.close()
    
    return Stats(
        total_devices=total_devices,
        active_devices=active_devices,
        total_threats=total_threats,
        unresolved_threats=unresolved_threats
    )
