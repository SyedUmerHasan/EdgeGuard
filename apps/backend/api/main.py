"""FastAPI backend server for EdgeGuard."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from shared.database import init_db
from api.routes import devices, threats, stats, dns, connections, http, sites, websites, discover

# Initialize database
init_db()

app = FastAPI(
    title="EdgeGuard API",
    description="AI-Powered IoT Security for Home Networks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(devices.router)
app.include_router(threats.router)
app.include_router(stats.router)
app.include_router(dns.router)
app.include_router(connections.router)
app.include_router(http.router)
app.include_router(sites.router)
app.include_router(websites.router, prefix="/websites", tags=["websites"])
app.include_router(discover.router)

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "EdgeGuard API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
