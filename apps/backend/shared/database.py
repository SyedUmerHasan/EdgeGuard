"""Shared database schema and connection for EdgeGuard backend."""
import sqlite3
from pathlib import Path
from datetime import datetime
from threading import Lock
from queue import Queue
import threading

DB_PATH = Path("/var/lib/edgeguard/edgeguard.db")
db_lock = Lock()

# Write queue for serializing database operations
write_queue = Queue()
_writer_thread = None

def _database_writer():
    """Background thread to process database writes."""
    while True:
        try:
            operation = write_queue.get()
            if operation is None:  # Shutdown signal
                break
            
            func, args, kwargs = operation
            with db_lock:
                func(*args, **kwargs)
            
            write_queue.task_done()
        except Exception as e:
            import logging
            logging.error(f"Database write error: {e}")

def start_writer_thread():
    """Start the database writer thread."""
    global _writer_thread
    if _writer_thread is None or not _writer_thread.is_alive():
        _writer_thread = threading.Thread(target=_database_writer, daemon=True)
        _writer_thread.start()

def queue_write(func, *args, **kwargs):
    """Queue a database write operation."""
    start_writer_thread()
    write_queue.put((func, args, kwargs))

def init_db():
    """Initialize SQLite database with schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    
    cursor = conn.cursor()
    
    # Devices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac_address TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            hostname TEXT,
            vendor TEXT,
            device_type TEXT,
            device_name TEXT,
            os_name TEXT,
            os_version TEXT,
            dhcp_fingerprint TEXT,
            dhcp_vendor_class TEXT,
            fingerbank_score INTEGER,
            open_ports TEXT,
            ja3_hash TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            total_bytes_sent INTEGER DEFAULT 0,
            total_bytes_received INTEGER DEFAULT 0,
            total_packets_sent INTEGER DEFAULT 0,
            total_packets_received INTEGER DEFAULT 0
        )
    """)
    
    # Traffic table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bytes_sent INTEGER DEFAULT 0,
            bytes_received INTEGER DEFAULT 0,
            packets_sent INTEGER DEFAULT 0,
            packets_received INTEGER DEFAULT 0,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # Threats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            threat_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # Alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            threat_id INTEGER,
            message TEXT NOT NULL,
            action_taken TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            acknowledged BOOLEAN DEFAULT 0,
            FOREIGN KEY (threat_id) REFERENCES threats(id)
        )
    """)
    
    # DNS queries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dns_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            domain TEXT NOT NULL,
            query_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # Connections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            protocol TEXT,
            src_ip TEXT,
            src_port INTEGER,
            dst_ip TEXT,
            dst_port INTEGER,
            dst_country TEXT,
            bytes_sent INTEGER DEFAULT 0,
            bytes_received INTEGER DEFAULT 0,
            packets_sent INTEGER DEFAULT 0,
            packets_received INTEGER DEFAULT 0,
            session_duration INTEGER DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # HTTP metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS http_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            method TEXT,
            host TEXT,
            path TEXT,
            full_url TEXT,
            user_agent TEXT,
            referer TEXT,
            status_code INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # TLS/SSL metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tls_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            server_name TEXT,
            tls_version TEXT,
            cipher_suite TEXT,
            cert_issuer TEXT,
            cert_subject TEXT,
            cert_expiry TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # Port scan attempts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS port_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            target_ip TEXT,
            target_port INTEGER,
            scan_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # Service discovery table (mDNS, SSDP, etc)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_discovery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            service_type TEXT,
            service_name TEXT,
            service_info TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # DHCP events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dhcp_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            event_type TEXT,
            requested_ip TEXT,
            lease_time INTEGER,
            hostname TEXT,
            vendor_class TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # ICMP events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS icmp_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            icmp_type TEXT,
            src_ip TEXT,
            dst_ip TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # Packet statistics table (for timing analysis)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packet_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            protocol TEXT,
            avg_packet_size REAL,
            min_packet_size INTEGER,
            max_packet_size INTEGER,
            avg_inter_arrival_time REAL,
            burst_count INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    
    # HTTPS/TLS visited sites table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visited_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            domain TEXT NOT NULL,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            visit_count INTEGER DEFAULT 1,
            FOREIGN KEY (device_id) REFERENCES devices(id),
            UNIQUE(device_id, domain)
        )
    """)
    
    # JA3 fingerprints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ja3_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            ja3_hash TEXT NOT NULL,
            ja3_string TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id),
            UNIQUE(device_id, ja3_hash)
        )
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    """Get database connection with lock."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn
