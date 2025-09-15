#!/bin/bash
# Restore original network settings

set -e

echo "=== Restoring Original Gateway Settings ==="

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# Disable IP forwarding
echo "Disabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=0
sed -i '/net.ipv4.ip_forward=1/d' /etc/sysctl.conf

# Flush iptables
echo "Flushing iptables rules..."
iptables -t nat -F
iptables -t nat -X
iptables -F
iptables -X

# Restore default policies
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

echo ""
echo "✅ Gateway settings restored!"
echo ""
echo "IMPORTANT: Reset router DHCP gateway back to router IP"
echo ""
