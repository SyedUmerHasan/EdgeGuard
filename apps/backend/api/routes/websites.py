"""Comprehensive website tracking - all sources combined."""
from fastapi import APIRouter
from shared.database import get_connection

router = APIRouter()

@router.get("/all")
def get_all_websites():
    """Get all websites from all sources (DNS, SNI, HTTP)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Combine DNS queries, SNI, and HTTP
    query = """
    SELECT DISTINCT domain as website, 'dns' as source, COUNT(*) as count, MAX(timestamp) as last_seen
    FROM dns_queries 
    WHERE domain NOT LIKE '%.in-addr.arpa' 
      AND domain NOT LIKE '%.local'
      AND domain NOT LIKE '_%.%'
    GROUP BY domain
    
    UNION ALL
    
    SELECT DISTINCT domain as website, 'https' as source, visit_count as count, last_seen
    FROM visited_sites
    
    UNION ALL
    
    SELECT DISTINCT full_url as website, 'http' as source, 1 as count, timestamp as last_seen
    FROM http_metadata
    
    ORDER BY last_seen DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    # Deduplicate and aggregate
    websites = {}
    for row in results:
        domain = row[0]
        source = row[1]
        count = row[2]
        last_seen = row[3]
        
        if domain not in websites:
            websites[domain] = {
                'domain': domain,
                'sources': [],
                'total_requests': 0,
                'last_seen': last_seen
            }
        
        websites[domain]['sources'].append(source)
        websites[domain]['total_requests'] += count
        if last_seen > websites[domain]['last_seen']:
            websites[domain]['last_seen'] = last_seen
    
    return {
        'total': len(websites),
        'websites': sorted(websites.values(), key=lambda x: x['last_seen'], reverse=True)
    }

@router.get("/by-device/{ip}")
def get_websites_by_device(ip: str):
    """Get all websites accessed by a specific device."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get device ID
    cursor.execute("SELECT id FROM devices WHERE ip_address = ?", (ip,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return {'error': 'Device not found'}
    
    device_id = result[0]
    
    # Get DNS queries
    cursor.execute("""
        SELECT DISTINCT domain, COUNT(*) as count, MAX(timestamp) as last_seen
        FROM dns_queries 
        WHERE device_id = ? 
          AND domain NOT LIKE '%.in-addr.arpa'
          AND domain NOT LIKE '%.local'
        GROUP BY domain
        ORDER BY last_seen DESC
    """, (device_id,))
    
    websites = [{'domain': row[0], 'requests': row[1], 'last_seen': row[2]} for row in cursor.fetchall()]
    conn.close()
    
    return {
        'device_ip': ip,
        'device_id': device_id,
        'total_websites': len(websites),
        'websites': websites
    }

@router.get("/stats")
def get_website_stats():
    """Get website access statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total unique domains
    cursor.execute("""
        SELECT COUNT(DISTINCT domain) FROM dns_queries 
        WHERE domain NOT LIKE '%.in-addr.arpa' AND domain NOT LIKE '%.local'
    """)
    total_dns = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT domain) FROM visited_sites")
    total_https = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT full_url) FROM http_metadata")
    total_http = cursor.fetchone()[0]
    
    # Top domains
    cursor.execute("""
        SELECT domain, COUNT(*) as count 
        FROM dns_queries 
        WHERE domain NOT LIKE '%.in-addr.arpa' AND domain NOT LIKE '%.local'
        GROUP BY domain 
        ORDER BY count DESC 
        LIMIT 20
    """)
    top_domains = [{'domain': row[0], 'requests': row[1]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'total_unique_dns': total_dns,
        'total_unique_https': total_https,
        'total_unique_http': total_http,
        'top_domains': top_domains
    }
