-- Snort3 Configuration for AI-Ops Testing
-- This configures Snort3 to use the AI Event Exporter plugin

-- Set plugin path
plugin_path = '/usr/local/lib/snort/plugins'

-- Network configuration
HOME_NET = '192.168.1.0/24'
EXTERNAL_NET = '!$HOME_NET'

-- Configure AI Event Exporter
ai_event_exporter = {
    endpoint = 'tcp://127.0.0.1:5555',
    export_alerts = true,
    export_flows = true,
    export_stats = false,
    min_severity = 'low',
    buffer_size = 10000
}

-- DAQ configuration for reading from PCAP
daq = {
    inputs = { 'test.pcap' },
    snaplen = 1518,
}

-- Basic stream configuration
stream = { }
stream_ip = { }
stream_icmp = { }
stream_tcp = { }
stream_udp = { }

-- Normalizer
normalizer = {
    tcp = {
        ips = true,
    }
}

-- HTTP inspection
http_inspect = { }

-- Port scan detection
port_scan = {
    proto = 'all',
    sense_level = 'medium',
}

-- Alerts configuration
alert_fast = {
    file = true
}

-- IPS policy
ips = {
    enable_builtin_rules = true,
    variables = default_variables,
}

-- Simple rules for testing
ips.rules = [[
alert tcp any any -> any any ( msg:"TCP Traffic Detected"; sid:1000001; rev:1; )
alert udp any any -> any any ( msg:"UDP Traffic Detected"; sid:1000002; rev:1; )
alert icmp any any -> any any ( msg:"ICMP Traffic Detected"; sid:1000003; rev:1; )
alert tcp any any -> any 80 ( msg:"HTTP Traffic to Port 80"; sid:1000004; rev:1; )
alert tcp any any -> any 443 ( msg:"HTTPS Traffic to Port 443"; sid:1000005; rev:1; )
alert tcp any any -> any 22 ( msg:"SSH Traffic Detected"; sid:1000006; rev:1; )
alert tcp any any -> any 3389 ( msg:"RDP Traffic Detected"; sid:1000007; rev:1; )
alert tcp any any -> any 445 ( msg:"SMB Traffic Detected"; sid:1000008; rev:1; )
]]
