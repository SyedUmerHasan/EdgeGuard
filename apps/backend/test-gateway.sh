#!/bin/bash
# Test gateway - check if we're capturing traffic from other devices

echo "=== EdgeGuard Gateway Test ==="
echo ""

# Check DNS queries by device in last 5 minutes
echo "DNS queries by device (last 5 minutes):"
sqlite3 /var/lib/edgeguard/edgeguard.db "
SELECT 
    d.ip_address,
    d.hostname,
    COUNT(dns.id) as queries,
    COUNT(DISTINCT dns.domain) as unique_domains
FROM devices d
LEFT JOIN dns_queries dns ON d.id = dns.device_id
WHERE dns.timestamp > datetime('now', '-5 minutes')
GROUP BY d.id
ORDER BY queries DESC;
" | column -t -s '|'

echo ""
echo "Recent domains accessed (last 2 minutes):"
sqlite3 /var/lib/edgeguard/edgeguard.db "
SELECT 
    d.ip_address,
    dns.domain,
    dns.timestamp
FROM dns_queries dns
JOIN devices d ON dns.device_id = d.id
WHERE dns.timestamp > datetime('now', '-2 minutes')
  AND dns.domain NOT LIKE '%.in-addr.arpa'
  AND dns.domain NOT LIKE '%.local'
ORDER BY dns.timestamp DESC
LIMIT 20;
" | column -t -s '|'

echo ""
echo "Total devices seen: $(sqlite3 /var/lib/edgeguard/edgeguard.db 'SELECT COUNT(*) FROM devices')"
echo ""
