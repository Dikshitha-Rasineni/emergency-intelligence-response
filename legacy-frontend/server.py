"""
RESQ.AI - Operational Backend & Platform Server
Unified server providing real PostgreSQL REST endpoints & serving the frontend platform.
Bridges the canonical emergency-intelligence-response-main backend with the frontend UI.
"""

import sys
import os
import uvicorn
from fastapi.staticfiles import StaticFiles

# Add canonical backend to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(root_dir, "..", "emergency-intelligence-response-main", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import canonical app
from app.main import app
from fastapi.responses import FileResponse

# Remove default backend root JSON route so '/' serves index.html
for i, route in enumerate(app.routes):
    if getattr(route, "path", None) == "/" and "GET" in getattr(route, "methods", set()):
        del app.routes[i]
        break

@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(os.path.join(root_dir, "index.html"))

# Mount static files of the frontend platform
app.mount("/", StaticFiles(directory=root_dir, html=True), name="static")

if __name__ == "__main__":
    print("\n" + "="*75)
    print(" RESQ.AI Emergency Intelligence & Operational Platform Server")
    print(" Serving UI & PostgreSQL REST API at http://localhost:8000")
    print(" API Documentation: http://localhost:8000/docs")
    print(" Citizen Portal:    http://localhost:8000/#user")
    print(" Hospital Triage:   http://localhost:8000/#hospital")
    print(" Police Ops:        http://localhost:8000/#police")
    print(" Fire & Rescue:     http://localhost:8000/#fire")
    print(" Admin CAD:         http://localhost:8000/#admin")
    print("="*75 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
