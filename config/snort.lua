-- Snort3 Configuration for AI-Ops Integration
-- This is a basic example configuration

-- Setup paths
HOME_NET = '192.168.0.0/16'
EXTERNAL_NET = '!$HOME_NET'

-- Include default rules
include = 'snort3-community-rules/snort3-community.rules'

-- Configure IPS mode
ips = {
    mode = 'inline',
    variables = {
        nets = {
            HOME_NET = HOME_NET,
            EXTERNAL_NET = EXTERNAL_NET
        }
    }
}

-- Configure Detection Engine
detection = {
    max_queue_events = 5
}

-- Configure Event Logging
alerts = {
    order = 'pass reset block drop alert log'
}

-- Load AI Event Exporter Plugin
ai_event_exporter = {
    endpoint = 'tcp://127.0.0.1:5555',
    export_alerts = true,
    export_flows = true,
    export_stats = false,
    min_severity = 'low',
    buffer_size = 10000,
    flush_interval = 1000
}

-- Configure Performance Statistics
perf_monitor = {
    seconds = 60,
    flow = true,
    flow_ip = true
}

-- Configure Network Analysis Policy
network = {
    checksum_eval = 'all'
}

-- Stream configuration
stream = {
    max_flows = 256000
}

stream_tcp = {
    policy = 'linux'
}

stream_udp = {}

stream_icmp = {}

-- Configure normalizer
normalizer = {
    tcp = {
        ips = true
    }
}

-- Configure Port Scan detection
port_scan = {
    protos = 'tcp udp'
}

-- Output modules
alert_fast = {
    file = true,
    packet = false
}

unified2 = {
    legacy_events = true,
    limit = 10
}
