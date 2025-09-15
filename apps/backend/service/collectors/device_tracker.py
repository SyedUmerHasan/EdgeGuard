"""Device tracker for managing discovered devices."""
import logging
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import get_connection
from service.collectors.hostname_resolver import resolve_hostname
from service.collectors.vendor_lookup import get_vendor
from service.collectors.fingerbank_api import identify_device_exact

logger = logging.getLogger(__name__)

class DeviceTracker:
    """Track and store discovered devices."""
    
    def add_or_update_device(self, mac_address, ip_address=None, hostname=None, dhcp_fingerprint=None, vendor_class=None):
        """Add new device or update existing one."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if device exists
        cursor.execute("SELECT id, hostname, vendor, device_name, dhcp_fingerprint FROM devices WHERE mac_address = ?", (mac_address,))
        existing = cursor.fetchone()
        
        if existing:
            device_id = existing[0]
            # Update existing device
            cursor.execute("""
                UPDATE devices 
                SET ip_address = ?, last_seen = CURRENT_TIMESTAMP, is_active = 1
                WHERE mac_address = ?
            """, (ip_address, mac_address))
            logger.debug(f"Updated device: {mac_address} -> {ip_address}")
            
            # Resolve hostname if not set
            if not existing[1] and ip_address:
                resolved_hostname = hostname or resolve_hostname(ip_address)
                if resolved_hostname:
                    cursor.execute("UPDATE devices SET hostname = ? WHERE id = ?", (resolved_hostname, device_id))
                    logger.info(f"Resolved hostname for {ip_address}: {resolved_hostname}")
            
            # Lookup vendor if not set
            if not existing[2]:
                vendor = get_vendor(mac_address)
                if vendor:
                    cursor.execute("UPDATE devices SET vendor = ? WHERE id = ?", (vendor, device_id))
                    logger.info(f"Found vendor for {mac_address}: {vendor}")
            
            # Update DHCP info if provided
            if dhcp_fingerprint and not existing[4]:
                cursor.execute("""
                    UPDATE devices 
                    SET dhcp_fingerprint = ?, dhcp_vendor_class = ?
                    WHERE id = ?
                """, (dhcp_fingerprint, vendor_class, device_id))
                
                # Query Fingerbank for exact device identification
                self.identify_device_with_fingerbank(device_id, mac_address, dhcp_fingerprint, hostname)
                
        else:
            # Resolve hostname
            resolved_hostname = hostname or (resolve_hostname(ip_address) if ip_address else None)
            
            # Lookup vendor
            vendor = get_vendor(mac_address)
            
            # Insert new device
            cursor.execute("""
                INSERT INTO devices (mac_address, ip_address, hostname, vendor, dhcp_fingerprint, dhcp_vendor_class)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (mac_address, ip_address, resolved_hostname, vendor, dhcp_fingerprint, vendor_class))
            
            device_id = cursor.lastrowid
            logger.info(f"New device: {mac_address} -> {ip_address} ({resolved_hostname or 'unknown'}) [{vendor or 'unknown'}]")
            
            # Query Fingerbank for exact device identification
            if dhcp_fingerprint:
                self.identify_device_with_fingerbank(device_id, mac_address, dhcp_fingerprint, resolved_hostname)
        
        conn.commit()
        conn.close()
    
    def identify_device_with_fingerbank(self, device_id, mac_address, dhcp_fingerprint, hostname):
        """Use Fingerbank API to get exact device identification."""
        device_info = identify_device_exact(mac_address, dhcp_fingerprint, hostname=hostname)
        
        if device_info and device_info['score'] > 30:  # Only use if confidence is reasonable
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE devices 
                SET device_name = ?, device_type = ?, os_name = ?, os_version = ?, fingerbank_score = ?
                WHERE id = ?
            """, (
                device_info['device_name'],
                device_info['device_type'],
                device_info['os'],
                device_info['version'],
                device_info['score'],
                device_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Exact device identified: {device_info['device_name']} (confidence: {device_info['score']}%)")
    
    def update_traffic_stats(self, ip_address, bytes_sent=0, bytes_received=0, packets_sent=0, packets_received=0):
        """Update traffic statistics for device."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE devices 
            SET total_bytes_sent = total_bytes_sent + ?,
                total_bytes_received = total_bytes_received + ?,
                total_packets_sent = total_packets_sent + ?,
                total_packets_received = total_packets_received + ?
            WHERE ip_address = ?
        """, (bytes_sent, bytes_received, packets_sent, packets_received, ip_address))
        
        conn.commit()
        conn.close()
    
    def log_dns_query(self, ip_address, domain, query_type):
        """Log DNS query."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get device ID
        cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip_address,))
        result = cursor.fetchone()
        
        if result:
            device_id = result[0]
            cursor.execute("""
                INSERT INTO dns_queries (device_id, domain, query_type)
                VALUES (?, ?, ?)
            """, (device_id, domain, str(query_type)))
            logger.debug(f"DNS query: {ip_address} -> {domain}")
        
        conn.commit()
        conn.close()
    
    def log_connection(self, src_ip, src_port, dst_ip, dst_port, protocol, bytes_sent):
        """Log network connection (batched to reduce DB writes)."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get device ID
            cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (src_ip,))
            result = cursor.fetchone()
            
            if result:
                device_id = result[0]
                
                # Check if connection exists (simplified query)
                cursor.execute("""
                    SELECT id FROM connections 
                    WHERE device_id = ? AND dst_ip = ? AND dst_port = ? AND protocol = ?
                    LIMIT 1
                """, (device_id, dst_ip, dst_port, protocol))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing connection
                    cursor.execute("""
                        UPDATE connections 
                        SET bytes_sent = bytes_sent + ?, 
                            packets_sent = packets_sent + 1,
                            last_seen = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (bytes_sent, existing[0]))
                else:
                    # Insert new connection
                    cursor.execute("""
                        INSERT INTO connections (device_id, protocol, src_ip, src_port, dst_ip, dst_port, bytes_sent, packets_sent)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """, (device_id, protocol, src_ip, src_port, dst_ip, dst_port, bytes_sent))
            
            conn.commit()
        except sqlite3.OperationalError:
            # Skip if database is locked
            pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def log_http_metadata(self, src_ip, method, host, path, full_url, user_agent, referer):
        """Log HTTP request metadata."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (src_ip,))
        result = cursor.fetchone()
        
        if result:
            device_id = result[0]
            cursor.execute("""
                INSERT INTO http_metadata (device_id, method, host, path, full_url, user_agent, referer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (device_id, method, host, path, full_url, user_agent, referer))
            logger.info(f"HTTP: {method} {full_url} - {user_agent}")
        
        conn.commit()
        conn.close()
    
    def log_tls_metadata(self, src_ip, dst_ip, tls_version):
        """Log TLS/SSL metadata."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (src_ip,))
        result = cursor.fetchone()
        
        if result:
            device_id = result[0]
            cursor.execute("""
                INSERT INTO tls_metadata (device_id, tls_version)
                VALUES (?, ?)
            """, (device_id, tls_version))
        
        conn.commit()
        conn.close()
    
    def log_port_scan(self, src_ip, target_ip, ports):
        """Log port scan attempt."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (src_ip,))
        result = cursor.fetchone()
        
        if result:
            device_id = result[0]
            for port in ports:
                cursor.execute("""
                    INSERT INTO port_scans (device_id, target_ip, target_port, scan_type)
                    VALUES (?, ?, ?, 'SYN')
                """, (device_id, target_ip, port))
            logger.warning(f"Port scan detected: {src_ip} -> {target_ip} ({len(ports)} ports)")
        
        conn.commit()
        conn.close()
    
    def log_dhcp_event(self, src_ip, event_type, packet):
        """Log DHCP event."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (src_ip,))
        result = cursor.fetchone()
        
        if result:
            device_id = result[0]
            cursor.execute("""
                INSERT INTO dhcp_events (device_id, event_type)
                VALUES (?, ?)
            """, (device_id, str(event_type)))
        
        conn.commit()
        conn.close()
    
    def log_icmp_event(self, src_ip, dst_ip, icmp_type, icmp_code):
        """Log ICMP event."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (src_ip,))
        result = cursor.fetchone()
        
        if result:
            device_id = result[0]
            cursor.execute("""
                INSERT INTO icmp_events (device_id, icmp_type, src_ip, dst_ip)
                VALUES (?, ?, ?, ?)
            """, (device_id, f"{icmp_type}/{icmp_code}", src_ip, dst_ip))
        
        conn.commit()
        conn.close()
    
    def log_service_discovery(self, ip_address, service_type, service_name, service_info):
        """Log discovered service."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip_address,))
        result = cursor.fetchone()
        
        if result:
            device_id = result[0]
            cursor.execute("""
                INSERT INTO service_discovery (device_id, service_type, service_name, service_info)
                VALUES (?, ?, ?, ?)
            """, (device_id, service_type, service_name, service_info))
            logger.info(f"Service discovered: {service_name} on {ip_address}")
            
            # Update device type if we can infer it
            if service_type:
                self.update_device_type_from_service(device_id, service_type)
        
        conn.commit()
        conn.close()
    
    def update_device_type_from_service(self, device_id, service_type):
        """Infer device type from discovered services."""
        device_type_map = {
            '_airplay': 'Apple TV / AirPlay Device',
            '_googlecast': 'Chromecast / Google Cast Device',
            '_spotify-connect': 'Spotify Connect Device',
            '_homekit': 'HomeKit Device',
            '_hap': 'HomeKit Accessory',
            '_printer': 'Network Printer',
            '_scanner': 'Network Scanner',
            '_smb': 'File Server / NAS',
            '_http': 'Web Server',
            '_ssh': 'SSH Server',
            '_ipp': 'Internet Printing Protocol',
            '_raop': 'AirPlay Audio Device'
        }
        
        for service_key, device_type in device_type_map.items():
            if service_key in service_type.lower():
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE devices SET device_type = ? WHERE id = ? AND device_type IS NULL", 
                             (device_type, device_id))
                conn.commit()
                conn.close()
                break
    
    def log_tcp_fingerprint(self, ip_address, os_name, ttl, window_size, tcp_options, mss):
        """Log TCP/IP fingerprint for OS detection."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip_address,))
        result = cursor.fetchone()
        
        if result:
            device_id = result[0]
            # Update device with OS information
            cursor.execute("""
                UPDATE devices 
                SET os_name = ?
                WHERE id = ? AND os_name IS NULL
            """, (os_name, device_id))
            
            logger.info(f"TCP/IP OS detected: {ip_address} -> {os_name}")
        
        conn.commit()
        conn.close()
    
    def log_visited_site(self, ip_address, domain):
        """Log visited website from SNI."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip_address,))
            result = cursor.fetchone()
            
            if result:
                device_id = result[0]
                
                # Insert or update visited site
                cursor.execute("""
                    INSERT INTO visited_sites (device_id, domain, visit_count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(device_id, domain) DO UPDATE SET
                        last_seen = CURRENT_TIMESTAMP,
                        visit_count = visit_count + 1
                """, (device_id, domain))
                
                logger.info(f"Site visited: {domain} from {ip_address}")
            
            conn.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def log_ja3_fingerprint(self, ip_address, ja3_hash, ja3_string):
        """Log JA3 TLS fingerprint."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip_address,))
            result = cursor.fetchone()
            
            if result:
                device_id = result[0]
                
                # Update device with JA3
                cursor.execute("""
                    UPDATE devices 
                    SET ja3_hash = ?
                    WHERE id = ? AND ja3_hash IS NULL
                """, (ja3_hash, device_id))
                
                # Store in JA3 table
                cursor.execute("""
                    INSERT INTO ja3_fingerprints (device_id, ja3_hash, ja3_string)
                    VALUES (?, ?, ?)
                    ON CONFLICT(device_id, ja3_hash) DO UPDATE SET
                        last_seen = CURRENT_TIMESTAMP
                """, (device_id, ja3_hash, ja3_string))
                
                logger.info(f"JA3 fingerprint: {ip_address} -> {ja3_hash}")
            
            conn.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def log_open_ports(self, ip_address, ports):
        """Log discovered open ports."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip_address,))
            result = cursor.fetchone()
            
            if result:
                device_id = result[0]
                ports_str = ','.join(map(str, sorted(ports)))
                
                cursor.execute("""
                    UPDATE devices 
                    SET open_ports = ?
                    WHERE id = ?
                """, (ports_str, device_id))
                
                logger.info(f"Open ports on {ip_address}: {ports_str}")
            
            conn.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def log_netdisco_device(self, ip_address, device_type, device_name, manufacturer, model, raw_info):
        """Log device discovered by netdisco."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip_address,))
            result = cursor.fetchone()
            
            if result:
                device_id = result[0]
                # Update with netdisco info
                cursor.execute("""
                    UPDATE devices 
                    SET device_type = COALESCE(device_type, ?),
                        device_name = COALESCE(device_name, ?),
                        vendor = COALESCE(vendor, ?)
                    WHERE id = ?
                """, (device_type, device_name, manufacturer, device_id))
                
                logger.info(f"Netdisco updated: {ip_address} - {device_name} ({device_type})")
            
            conn.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def log_nmap_device(self, ip_address, nmap_info):
        """Log device discovered by nmap."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if device exists
            cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip_address,))
            result = cursor.fetchone()
            
            mac = nmap_info.get('mac')
            hostname = nmap_info.get('hostname')
            vendor = nmap_info.get('vendor')
            os_name = nmap_info.get('os')
            ports = nmap_info.get('ports', [])
            
            if result:
                device_id = result[0]
                # Update existing device
                cursor.execute("""
                    UPDATE devices 
                    SET hostname = COALESCE(hostname, ?),
                        vendor = COALESCE(vendor, ?),
                        os_name = COALESCE(os_name, ?),
                        open_ports = ?
                    WHERE id = ?
                """, (hostname, vendor, os_name, ','.join(str(p['port']) for p in ports), device_id))
            elif mac:
                # Insert new device
                cursor.execute("""
                    INSERT INTO devices (mac_address, ip_address, hostname, vendor, os_name, open_ports)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (mac, ip_address, hostname, vendor, os_name, ','.join(str(p['port']) for p in ports)))
            
            logger.info(f"Nmap updated: {ip_address} - {hostname} ({vendor})")
            
            conn.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            try:
                conn.close()
            except:
                pass
    
    def mark_inactive_devices(self, timeout_minutes=30):
        """Mark devices as inactive if not seen recently."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE devices 
            SET is_active = 0 
            WHERE datetime(last_seen) < datetime('now', '-' || ? || ' minutes')
        """, (timeout_minutes,))
        
        if cursor.rowcount > 0:
            logger.info(f"Marked {cursor.rowcount} devices as inactive")
        
        conn.commit()
        conn.close()
