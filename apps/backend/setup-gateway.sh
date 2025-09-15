#!/bin/bash
# Setup EdgeGuard as transparent gateway to capture all network traffic

set -e

echo "=== EdgeGuard Gateway Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

# Get network interface
INTERFACE=$(ip route | grep default | awk '{print $5}')
echo "Network interface: $INTERFACE"

# Get current IP
CURRENT_IP=$(ip -4 addr show $INTERFACE | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
echo "Current IP: $CURRENT_IP"

# Get gateway
GATEWAY=$(ip route | grep default | awk '{print $3}')
echo "Gateway (router): $GATEWAY"
echo ""

# Backup current iptables
echo "Backing up iptables..."
iptables-save > /tmp/iptables-backup-$(date +%s).rules

# Enable IP forwarding
echo "Enabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# Setup iptables for transparent proxy
echo "Setting up iptables rules..."

# NAT for forwarding traffic
iptables -t nat -A POSTROUTING -o $INTERFACE -j MASQUERADE

# Forward packets
iptables -A FORWARD -i $INTERFACE -o $INTERFACE -j ACCEPT
iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT

# Intercept DNS (port 53) - redirect to local
iptables -t nat -A PREROUTING -i $INTERFACE -p udp --dport 53 -j REDIRECT --to-ports 53
iptables -t nat -A PREROUTING -i $INTERFACE -p tcp --dport 53 -j REDIRECT --to-ports 53

# Save iptables rules
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

echo ""
echo "✅ Gateway setup complete!"
echo ""
echo "NEXT STEPS:"
echo "1. Configure your router DHCP settings:"
echo "   - Login to router: http://$GATEWAY"
echo "   - Go to LAN Settings > DHCP"
echo "   - Set Default Gateway to: $CURRENT_IP"
echo "   - Save and reboot router"
echo ""
echo "2. Restart EdgeGuard monitor to capture all traffic"
echo ""
echo "To UNDO this setup, run:"
echo "  sudo ./restore-gateway.sh"
echo ""
