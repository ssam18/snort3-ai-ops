-- Initialize AI-Ops database schema

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    source_ip VARCHAR(45),
    dest_ip VARCHAR(45),
    severity VARCHAR(20),
    signature TEXT,
    raw_data JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    source_ip VARCHAR(45),
    dest_ip VARCHAR(45),
    severity VARCHAR(20),
    threat_score FLOAT,
    signature TEXT,
    recommendations JSONB,
    status VARCHAR(20) DEFAULT 'open',
    assigned_to VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS threat_intel (
    id SERIAL PRIMARY KEY,
    indicator VARCHAR(255) NOT NULL,
    indicator_type VARCHAR(50) NOT NULL,
    threat_score FLOAT,
    reputation VARCHAR(20),
    sources JSONB,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(indicator, indicator_type)
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(100) UNIQUE NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    generated_by VARCHAR(100),
    timerange VARCHAR(50),
    format VARCHAR(20),
    file_path TEXT,
    recipients JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_source_ip ON events(source_ip);
CREATE INDEX idx_incidents_timestamp ON incidents(timestamp);
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_threat_intel_indicator ON threat_intel(indicator);
CREATE INDEX idx_agent_tasks_agent ON agent_tasks(agent_name);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
