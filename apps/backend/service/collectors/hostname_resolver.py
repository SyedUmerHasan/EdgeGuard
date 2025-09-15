"""Hostname resolver using reverse DNS."""
import socket
import logging

logger = logging.getLogger(__name__)

def resolve_hostname(ip_address):
    """Resolve hostname from IP address."""
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
        return hostname
    except (socket.herror, socket.gaierror, socket.timeout):
        return None
