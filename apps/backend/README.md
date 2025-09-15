# EdgeGuard Backend

AI-Powered IoT Security Backend for Raspberry Pi

## Architecture

- **FastAPI Server** (`api/`) - REST API for dashboard/CLI
- **Background Service** (`service/`) - Network monitoring daemon

## Components

### FastAPI Server
- REST endpoints for devices, threats, stats
- SQLite database access
- CORS enabled for web dashboard
- Auto-generated API docs at `/docs`

### Background Monitor
- ARP packet listener for device discovery
- Automatic device tracking
- Inactive device cleanup
- Runs as systemd service

## Installation

### On Raspberry Pi:

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install python3-pip

# Install Python packages
pip3 install -r requirements.txt

# Copy to /opt
sudo mkdir -p /opt/edgeguard
sudo cp -r . /opt/edgeguard/

# Install systemd services
sudo cp edgeguard-monitor.service /etc/systemd/system/
sudo cp edgeguard-api.service /etc/systemd/system/

# Create service user
sudo useradd -r -s /bin/false edgeguard

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable edgeguard-monitor
sudo systemctl enable edgeguard-api
sudo systemctl start edgeguard-monitor
sudo systemctl start edgeguard-api
```

## Usage

### Check service status:
```bash
sudo systemctl status edgeguard-monitor
sudo systemctl status edgeguard-api
```

### View logs:
```bash
sudo journalctl -u edgeguard-monitor -f
sudo journalctl -u edgeguard-api -f
```

### API Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Database

SQLite database stored at: `~/.edgeguard/edgeguard.db`

### Tables:
- `devices` - Discovered network devices
- `traffic` - Traffic statistics
- `threats` - Detected threats
- `alerts` - Security alerts

## Development

### Run API locally:
```bash
./dev-api.sh
# Or manually:
cd api
python3 main.py
```

### Run monitor locally:
```bash
sudo ./dev-monitor.sh
# Or manually:
cd service
sudo python3 monitor.py  # Requires root for packet capture
```

### Test database:
```bash
python3 -c "from shared.database import init_db; init_db(); print('Database initialized')"
```

## API Endpoints

- `GET /devices` - List all devices
- `GET /devices/{id}` - Get device details
- `GET /threats` - List threats
- `PATCH /threats/{id}/resolve` - Mark threat resolved
- `GET /stats` - System statistics
