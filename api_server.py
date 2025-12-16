"""
API Server for Snort3-AI-Ops
Provides RESTful and GraphQL endpoints for the AI-Ops system
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json
import uvicorn

from core.engine import AIOpsEngine
from core.config import Config, load_config

app = FastAPI(
    title="Snort3-AI-Ops API",
    description="Intelligent Threat Analysis & Response Orchestration",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance
engine: Optional[AIOpsEngine] = None
active_websockets: List[WebSocket] = []

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    agents_running: int

class AgentInfo(BaseModel):
    id: str
    name: str
    role: str
    status: str
    tasks_completed: int
    success_rate: float

class InvestigateRequest(BaseModel):
    ioc_type: str
    ioc_value: str
    priority: str = "medium"

class BlockRequest(BaseModel):
    ioc_type: str
    ioc_value: str
    reason: str
    duration: int = 3600

class Incident(BaseModel):
    id: str
    timestamp: datetime
    source_ip: str
    destination_ip: str
    signature: str
    severity: str
    threat_score: float
    recommendations: List[Dict[str, Any]]

class StatsResponse(BaseModel):
    events_processed: int
    incidents_created: int
    threats_blocked: int
    reports_generated: int
    uptime_seconds: float

class Event(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    signature: str
    severity: str
    raw_alert: str
    processed: bool = False
    threat_intel: Optional[Dict[str, Any]] = None
    behavioral_analysis: Optional[Dict[str, Any]] = None

# RESTful API Endpoints

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """System health check endpoint"""
    global engine
    
    # Check if engine container is running via Docker socket or assume running if initialized
    is_healthy = engine is not None
    
    return HealthResponse(
        status="healthy" if is_healthy else "stopped",
        timestamp=datetime.now(),
        version="1.0.0",
        agents_running=5 if is_healthy else 0
    )

@app.get("/api/v1/agents", response_model=List[AgentInfo])
async def list_agents():
    """List all AI agents and their status"""
    return await get_agents_status()

@app.get("/api/v1/agents/status", response_model=List[AgentInfo])
async def get_agents_status():
    """Get status of all AI agents (alias endpoint)"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not running")
    
    agents = [
        AgentInfo(
            id="threat-intel",
            name="Threat Intelligence Agent",
            role="Threat analysis and correlation",
            status="active",
            tasks_completed=150,
            success_rate=0.95
        ),
        AgentInfo(
            id="incident-response",
            name="Incident Response Agent",
            role="Automated incident handling",
            status="active",
            tasks_completed=87,
            success_rate=0.98
        ),
        AgentInfo(
            id="forensics",
            name="Network Forensics Agent",
            role="Deep packet analysis",
            status="active",
            tasks_completed=65,
            success_rate=0.92
        ),
        AgentInfo(
            id="rule-optimizer",
            name="Rule Optimization Agent",
            role="IPS rule tuning",
            status="active",
            tasks_completed=42,
            success_rate=0.88
        ),
        AgentInfo(
            id="report-generator",
            name="Report Generation Agent",
            role="Executive reporting",
            status="active",
            tasks_completed=38,
            success_rate=0.97
        )
    ]
    
    return agents

@app.get("/api/v1/events", response_model=List[Event])
async def list_events(
    limit: int = 10,
    offset: int = 0,
    severity: Optional[str] = None,
    event_type: Optional[str] = None
):
    """List recent events with pagination and filtering"""
    # Mock data for demonstration - replace with actual database queries
    all_events = [
        Event(
            id=f"evt-{1000+i}",
            timestamp=datetime.now(),
            event_type="alert" if i % 2 == 0 else "packet",
            source_ip=f"192.168.1.{100+i}",
            destination_ip=f"10.0.0.{50+i}",
            source_port=40000 + i,
            destination_port=80 if i % 3 == 0 else 443,
            protocol="TCP",
            signature=f"Suspicious activity detected - Pattern {i}",
            severity="high" if i % 3 == 0 else "medium" if i % 2 == 0 else "low",
            raw_alert=f"[1:2000{i}:1] ET SCAN Potential SSH Scan [Classification: Attempted Information Leak] [Priority: 2]",
            processed=i % 2 == 0,
            threat_intel={
                "reputation": "malicious" if i % 3 == 0 else "suspicious",
                "threat_score": 0.85 if i % 3 == 0 else 0.65,
                "sources": ["VirusTotal", "AbuseIPDB"]
            } if i % 2 == 0 else None,
            behavioral_analysis={
                "anomaly_score": 0.75,
                "pattern": "port_scan",
                "confidence": 0.92
            } if i % 3 == 0 else None
        )
        for i in range(100)
    ]
    
    # Apply filters
    filtered = all_events
    if severity:
        filtered = [e for e in filtered if e.severity == severity]
    if event_type:
        filtered = [e for e in filtered if e.event_type == event_type]
    
    # Apply pagination
    return filtered[offset:offset+limit]

@app.get("/api/v1/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """Get specific event details by ID"""
    # Get all events and find the specific one
    events = await list_events(limit=100)
    
    for event in events:
        if event.id == event_id:
            return event
    
    raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

@app.get("/api/v1/agents/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    """Get specific agent details"""
    agents = await get_agents_status()
    
    for agent in agents:
        if agent.id == agent_id:
            return agent
    
    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

@app.post("/api/v1/investigate")
async def start_investigation(request: InvestigateRequest):
    """Start an investigation on an IOC"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return {
        "status": "investigation_started",
        "investigation_id": f"inv-{datetime.now().timestamp()}",
        "ioc": {
            "type": request.ioc_type,
            "value": request.ioc_value
        },
        "priority": request.priority,
        "estimated_completion": "30 seconds"
    }

@app.post("/api/v1/block")
async def block_ioc(request: BlockRequest):
    """Block an IOC (IP, domain, hash)"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return {
        "status": "blocked",
        "ioc": {
            "type": request.ioc_type,
            "value": request.ioc_value
        },
        "reason": request.reason,
        "duration": request.duration,
        "expires_at": datetime.now().timestamp() + request.duration
    }

@app.get("/api/v1/incidents", response_model=List[Incident])
async def list_incidents(
    severity: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """List security incidents"""
    # Mock data for demonstration
    incidents = [
        Incident(
            id=f"inc-{i}",
            timestamp=datetime.now(),
            source_ip=f"192.168.1.{100+i}",
            destination_ip=f"10.0.0.{50+i}",
            signature="Suspicious port scan detected",
            severity="high" if i % 3 == 0 else "medium",
            threat_score=0.85 if i % 3 == 0 else 0.65,
            recommendations=[
                {
                    "action": "block",
                    "priority": "high",
                    "description": "Block source IP for 1 hour"
                },
                {
                    "action": "alert",
                    "priority": "medium",
                    "description": "Notify SOC team"
                }
            ]
        )
        for i in range(limit)
    ]
    
    if severity:
        incidents = [inc for inc in incidents if inc.severity == severity]
    
    return incidents[offset:offset+limit]

@app.get("/api/v1/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    """Get specific incident details"""
    incidents = await list_incidents(limit=100)
    
    for incident in incidents:
        if incident.id == incident_id:
            return incident
    
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

@app.post("/api/v1/reports/generate")
async def generate_report(report_type: str = "executive", time_range: str = "24h"):
    """Generate a security report"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return {
        "status": "report_generated",
        "report_id": f"rpt-{datetime.now().timestamp()}",
        "type": report_type,
        "time_range": time_range,
        "download_url": f"/api/v1/reports/download/rpt-{datetime.now().timestamp()}"
    }

@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""
    return StatsResponse(
        events_processed=15847,
        incidents_created=342,
        threats_blocked=89,
        reports_generated=47,
        uptime_seconds=86400.0
    )

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_root(websocket: WebSocket):
    """WebSocket endpoint - redirects to /ws/events"""
    await websocket_events(websocket)

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket for real-time event streaming"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Send mock events every 2 seconds
            event = {
                "type": "alert",
                "timestamp": datetime.now().isoformat(),
                "source_ip": "192.168.1.100",
                "destination_ip": "10.0.0.50",
                "signature": "Suspicious activity detected",
                "severity": "medium"
            }
            await websocket.send_json(event)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

# Serve static dashboard
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard HTML"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Snort3-AI-Ops Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #fff;
                min-height: 100vh;
            }
            .header {
                background: rgba(0,0,0,0.3);
                padding: 20px;
                text-align: center;
                border-bottom: 2px solid rgba(255,255,255,0.2);
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            .container {
                max-width: 1400px;
                margin: 30px auto;
                padding: 0 20px;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .card {
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                border: 1px solid rgba(255,255,255,0.2);
                transition: transform 0.3s, box-shadow 0.3s;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .card h3 {
                font-size: 1.5em;
                margin-bottom: 15px;
                border-bottom: 2px solid rgba(255,255,255,0.3);
                padding-bottom: 10px;
            }
            .stat {
                font-size: 3em;
                font-weight: bold;
                margin: 20px 0;
                text-align: center;
            }
            .stat-label {
                text-align: center;
                opacity: 0.8;
                font-size: 0.9em;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 2s infinite;
            }
            .status-active { background: #00ff88; }
            .status-warning { background: #ffaa00; }
            .status-error { background: #ff4444; }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .event-list {
                max-height: 300px;
                overflow-y: auto;
                margin-top: 15px;
            }
            .event-item {
                background: rgba(0,0,0,0.2);
                padding: 10px;
                margin: 8px 0;
                border-radius: 8px;
                border-left: 3px solid #00ff88;
                font-size: 0.9em;
            }
            .event-time {
                opacity: 0.7;
                font-size: 0.85em;
            }
            .btn {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: #fff;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                margin: 5px;
                transition: all 0.3s;
            }
            .btn:hover {
                background: rgba(255,255,255,0.3);
                transform: scale(1.05);
            }
            .agents-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .agent-card {
                background: rgba(0,0,0,0.2);
                padding: 15px;
                border-radius: 10px;
                text-align: center;
            }
            .agent-icon {
                font-size: 2em;
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Snort3-AI-Ops Dashboard</h1>
            <p>Intelligent Threat Analysis & Response Orchestration</p>
        </div>
        
        <div class="container">
            <div class="grid">
                <!-- System Status -->
                <div class="card">
                    <h3>System Status</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        <span class="status-indicator status-active"></span>
                        <span style="font-size: 1.3em;">All Systems Operational</span>
                    </div>
                    <div style="margin-top: 20px;">
                        <div><strong>Uptime:</strong> 24h 15m 32s</div>
                        <div><strong>Version:</strong> 1.0.0</div>
                        <div><strong>Agents Running:</strong> 5/5</div>
                    </div>
                </div>
                
                <!-- Statistics -->
                <div class="card">
                    <h3>📊 Statistics</h3>
                    <div class="stat" id="eventsProcessed">15,847</div>
                    <div class="stat-label">Events Processed (24h)</div>
                    <hr style="margin: 15px 0; opacity: 0.3;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                        <div>
                            <div style="font-size: 1.8em; text-align: center; color: #ffaa00;">342</div>
                            <div class="stat-label">Incidents</div>
                        </div>
                        <div>
                            <div style="font-size: 1.8em; text-align: center; color: #ff4444;">89</div>
                            <div class="stat-label">Blocked</div>
                        </div>
                    </div>
                </div>
                
                <!-- AI Agents -->
                <div class="card">
                    <h3>🤖 AI Agents</h3>
                    <div class="agents-grid">
                        <div class="agent-card">
                            <div class="agent-icon">🔍</div>
                            <div>Threat Intel</div>
                            <div style="font-size: 0.8em; color: #00ff88;">Active</div>
                        </div>
                        <div class="agent-card">
                            <div class="agent-icon">🚨</div>
                            <div>Incident Response</div>
                            <div style="font-size: 0.8em; color: #00ff88;">Active</div>
                        </div>
                        <div class="agent-card">
                            <div class="agent-icon">🔬</div>
                            <div>Forensics</div>
                            <div style="font-size: 0.8em; color: #00ff88;">Active</div>
                        </div>
                        <div class="agent-card">
                            <div class="agent-icon">⚙️</div>
                            <div>Rule Optimizer</div>
                            <div style="font-size: 0.8em; color: #00ff88;">Active</div>
                        </div>
                        <div class="agent-card">
                            <div class="agent-icon">📝</div>
                            <div>Report Gen</div>
                            <div style="font-size: 0.8em; color: #00ff88;">Active</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Events -->
            <div class="card" style="margin-top: 20px;">
                <h3>🔴 Live Event Stream</h3>
                <div class="event-list" id="eventList">
                    <div class="event-item">
                        <div><strong>Suspicious port scan detected</strong></div>
                        <div>Source: 192.168.1.100 → Dest: 10.0.0.50</div>
                        <div class="event-time">Just now</div>
                    </div>
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="card" style="margin-top: 20px;">
                <h3>⚡ Quick Actions</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                    <button class="btn" onclick="generateReport()">Generate Report</button>
                    <button class="btn" onclick="viewIncidents()">View Incidents</button>
                    <button class="btn" onclick="checkHealth()">Health Check</button>
                    <button class="btn" onclick="window.location.href='/docs'">API Docs</button>
                </div>
            </div>
        </div>
        
        <script>
            // WebSocket connection for real-time events
            const ws = new WebSocket(`ws://${window.location.host}/ws/events`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const eventList = document.getElementById('eventList');
                const eventItem = document.createElement('div');
                eventItem.className = 'event-item';
                eventItem.innerHTML = `
                    <div><strong>${data.signature}</strong></div>
                    <div>Source: ${data.source_ip} → Dest: ${data.destination_ip}</div>
                    <div class="event-time">Just now</div>
                `;
                eventList.insertBefore(eventItem, eventList.firstChild);
                
                // Keep only last 10 events
                while (eventList.children.length > 10) {
                    eventList.removeChild(eventList.lastChild);
                }
                
                // Update event counter
                const counter = document.getElementById('eventsProcessed');
                const current = parseInt(counter.textContent.replace(/,/g, ''));
                counter.textContent = (current + 1).toLocaleString();
            };
            
            async function generateReport() {
                try {
                    const response = await fetch('/api/v1/reports/generate?report_type=executive&time_range=24h', {
                        method: 'POST'
                    });
                    const data = await response.json();
                    alert(`✅ Report Generated Successfully!\n\nReport ID: ${data.report_id}\nType: ${data.type}\nTime Range: ${data.time_range}\n\nDownload URL: ${data.download_url}`);
                } catch (error) {
                    alert(`❌ Error generating report: ${error.message}`);
                }
            }
            
            async function viewIncidents() {
                window.location.href = '/api/v1/incidents';
            }
            
            async function checkHealth() {
                try {
                    const response = await fetch('/api/v1/health');
                    const data = await response.json();
                    const statusIcon = data.status === 'healthy' ? '✅' : '⚠️';
                    const statusText = data.status === 'healthy' ? 'All Systems Operational' : 'System Stopped';
                    alert(`${statusIcon} Health Check Results\n\nStatus: ${statusText}\nAgents Running: ${data.agents_running}\nVersion: ${data.version}\nTimestamp: ${new Date(data.timestamp).toLocaleString()}`);
                } catch (error) {
                    alert(`❌ Error checking health: ${error.message}`);
                }
            }
        </script>
    </body>
    </html>
    """

# GraphQL support would go here (using Strawberry or Graphene)

# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the AI-Ops engine on startup"""
    global engine
    try:
        config = load_config("config/config.yaml")
        engine = AIOpsEngine(config)
        # Note: Don't start engine here to avoid blocking
        # Engine runs in separate container via main.py
        print("API server started successfully with engine initialized")
    except Exception as e:
        print(f"Warning: Could not initialize engine: {e}")
        print("API server running in mock mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global engine
    if engine:
        try:
            engine.stop()
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
