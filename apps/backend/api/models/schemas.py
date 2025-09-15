"""Pydantic models for API."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Device(BaseModel):
    id: Optional[int] = None
    mac_address: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_active: bool = True

class Threat(BaseModel):
    id: Optional[int] = None
    device_id: int
    threat_type: str
    severity: str
    description: Optional[str] = None
    detected_at: Optional[datetime] = None
    resolved: bool = False

class Alert(BaseModel):
    id: Optional[int] = None
    threat_id: int
    message: str
    action_taken: Optional[str] = None
    created_at: Optional[datetime] = None
    acknowledged: bool = False

class Stats(BaseModel):
    total_devices: int
    active_devices: int
    total_threats: int
    unresolved_threats: int
