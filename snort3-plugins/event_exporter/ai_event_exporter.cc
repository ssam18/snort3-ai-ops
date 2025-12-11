//--------------------------------------------------------------------------
// ai_event_exporter.cc - Implementation of AI Event Exporter Plugin
//--------------------------------------------------------------------------

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "ai_event_exporter.h"

#include "detection/detection_engine.h"
#include "events/event.h"
#include "flow/flow.h"
#include "framework/data_bus.h"
#include "log/messages.h"
#include "packet_io/active.h"
#include "protocols/packet.h"
#include "pub_sub/intrinsic_event_ids.h"
#include "time/packet_time.h"

#include <nlohmann/json.hpp>
#include <chrono>

using namespace snort;
using namespace std;
using json = nlohmann::json;

//-------------------------------------------------------------------------
// Module Implementation
//-------------------------------------------------------------------------

static const Parameter ai_event_params[] =
{
    { "endpoint", Parameter::PT_STRING, nullptr, "tcp://127.0.0.1:5555",
      "ZeroMQ endpoint for event streaming" },

    { "export_alerts", Parameter::PT_BOOL, nullptr, "true",
      "export alert events" },

    { "export_flows", Parameter::PT_BOOL, nullptr, "true",
      "export flow events" },

    { "export_stats", Parameter::PT_BOOL, nullptr, "false",
      "export statistics events" },

    { "min_severity", Parameter::PT_STRING, nullptr, "low",
      "minimum severity level to export (low|medium|high|critical)" },

    { "buffer_size", Parameter::PT_INT, "100:100000", "10000",
      "maximum number of events to buffer" },

    { "flush_interval", Parameter::PT_INT, "100:10000", "1000",
      "flush interval in milliseconds" },

    { nullptr, Parameter::PT_MAX, nullptr, nullptr, nullptr }
};

AIEventExporterModule::AIEventExporterModule()
    : Module("ai_event_exporter", "AI-Ops event exporter plugin", ai_event_params)
{
    config.endpoint = "tcp://127.0.0.1:5555";
    config.export_alerts = true;
    config.export_flows = true;
    config.export_stats = false;
    config.min_severity = "low";
    config.buffer_size = 10000;
    config.flush_interval = 1000;
}

bool AIEventExporterModule::set(const char*, Value& v, SnortConfig*)
{
    if ( v.is("endpoint") )
        config.endpoint = v.get_string();
    else if ( v.is("export_alerts") )
        config.export_alerts = v.get_bool();
    else if ( v.is("export_flows") )
        config.export_flows = v.get_bool();
    else if ( v.is("export_stats") )
        config.export_stats = v.get_bool();
    else if ( v.is("min_severity") )
        config.min_severity = v.get_string();
    else if ( v.is("buffer_size") )
        config.buffer_size = v.get_size();
    else if ( v.is("flush_interval") )
        config.flush_interval = v.get_uint32();

    return true;
}

bool AIEventExporterModule::begin(const char*, int, SnortConfig*)
{
    return true;
}

bool AIEventExporterModule::end(const char*, int, SnortConfig*)
{
    return true;
}

//-------------------------------------------------------------------------
// Inspector Implementation
//-------------------------------------------------------------------------

AIEventExporter::AIEventExporter(AIEventExporterConfig* c)
    : config(c), zmq_context(nullptr), zmq_socket(nullptr),
      events_sent(0), events_dropped(0)
{
}

AIEventExporter::~AIEventExporter()
{
    if (zmq_socket)
    {
        zmq_socket->close();
        delete zmq_socket;
    }
    if (zmq_context)
    {
        zmq_context->close();
        delete zmq_context;
    }
}

bool AIEventExporter::configure(SnortConfig*)
{
    try
    {
        zmq_context = new zmq::context_t(1);
        zmq_socket = new zmq::socket_t(*zmq_context, ZMQ_PUSH);
        
        // Set socket options
        int hwm = config->buffer_size;
        zmq_socket->set(zmq::sockopt::sndbuf, hwm);
        zmq_socket->set(zmq::sockopt::linger, 1000);
        
        LogMessage("AI Event Exporter: Connecting to %s\n", config->endpoint.c_str());
        zmq_socket->connect(config->endpoint);
        
        LogMessage("AI Event Exporter configured successfully\n");
        return true;
    }
    catch (const exception& e)
    {
        ErrorMessage("AI Event Exporter: Failed to configure - %s\n", e.what());
        return false;
    }
}

void AIEventExporter::tinit()
{
    // Thread initialization if needed
}

void AIEventExporter::tterm()
{
    flush_buffer();
}

void AIEventExporter::show(const SnortConfig*) const
{
    LogMessage("AI Event Exporter Configuration:\n");
    LogMessage("  Endpoint: %s\n", config->endpoint.c_str());
    LogMessage("  Export Alerts: %s\n", config->export_alerts ? "yes" : "no");
    LogMessage("  Export Flows: %s\n", config->export_flows ? "yes" : "no");
    LogMessage("  Export Stats: %s\n", config->export_stats ? "yes" : "no");
    LogMessage("  Min Severity: %s\n", config->min_severity.c_str());
    LogMessage("  Buffer Size: %zu\n", config->buffer_size);
    LogMessage("  Events Sent: %lu\n", events_sent);
    LogMessage("  Events Dropped: %lu\n", events_dropped);
}

void AIEventExporter::eval(Packet* p)
{
    if (!p)
        return;

    // Export alerts
    if (config->export_alerts && p->active && p->active->get_action() > Active::ACT_PASS)
    {
        export_alert(p);
    }

    // Export flows
    if (config->export_flows && p->flow && p->flow->flow_state == Flow::FlowState::INSPECT)
    {
        export_flow(p);
    }
}

string AIEventExporter::serialize_packet(Packet* p)
{
    json j;
    
    j["type"] = "alert";
    j["timestamp"] = chrono::duration_cast<chrono::milliseconds>(
        chrono::system_clock::now().time_since_epoch()).count();
    
    // Packet info
    if (p->has_ip())
    {
        char src_ip[INET6_ADDRSTRLEN], dst_ip[INET6_ADDRSTRLEN];
        p->ptrs.ip_api.get_src()->ntop(src_ip, sizeof(src_ip));
        p->ptrs.ip_api.get_dst()->ntop(dst_ip, sizeof(dst_ip));
        
        j["src_ip"] = src_ip;
        j["dst_ip"] = dst_ip;
        j["ip_proto"] = to_utype(p->get_ip_proto_next());
    }
    
    if (p->type() == PktType::TCP && p->ptrs.tcph)
    {
        j["src_port"] = p->ptrs.tcph->src_port();
        j["dst_port"] = p->ptrs.tcph->dst_port();
        j["tcp_flags"] = p->ptrs.tcph->th_flags;
    }
    else if (p->type() == PktType::UDP && p->ptrs.udph)
    {
        j["src_port"] = p->ptrs.udph->src_port();
        j["dst_port"] = p->ptrs.udph->dst_port();
    }
    
    j["packet_length"] = p->pktlen;
    
    // Detection info
    if (p->active)
    {
        j["action"] = p->active->get_action();
        j["verdict"] = p->active->get_status();
    }
    
    return j.dump();
}

string AIEventExporter::serialize_flow(Flow* f)
{
    json j;
    
    j["type"] = "flow";
    j["timestamp"] = chrono::duration_cast<chrono::milliseconds>(
        chrono::system_clock::now().time_since_epoch()).count();
    
    // Flow info
    char src_ip[INET6_ADDRSTRLEN], dst_ip[INET6_ADDRSTRLEN];
    f->client_ip.ntop(src_ip, sizeof(src_ip));
    f->server_ip.ntop(dst_ip, sizeof(dst_ip));
    
    j["src_ip"] = src_ip;
    j["dst_ip"] = dst_ip;
    j["src_port"] = f->client_port;
    j["dst_port"] = f->server_port;
    j["protocol"] = to_utype(f->pkt_type);
    
    // Flow state
    j["flow_state"] = to_utype(f->flow_state);
    j["session_flags"] = f->get_session_flags();
    
    // Statistics
    j["packets_to_server"] = f->flowstats.client_pkts;
    j["packets_to_client"] = f->flowstats.server_pkts;
    j["bytes_to_server"] = f->flowstats.client_bytes;
    j["bytes_to_client"] = f->flowstats.server_bytes;
    
    return j.dump();
}

void AIEventExporter::export_alert(Packet* p)
{
    try
    {
        string event_json = serialize_packet(p);
        send_event(event_json);
    }
    catch (const exception& e)
    {
        ErrorMessage("Failed to export alert: %s\n", e.what());
        events_dropped++;
    }
}

void AIEventExporter::export_flow(Packet* p)
{
    try
    {
        string event_json = serialize_flow(p->flow);
        send_event(event_json);
    }
    catch (const exception& e)
    {
        ErrorMessage("Failed to export flow: %s\n", e.what());
        events_dropped++;
    }
}

void AIEventExporter::send_event(const string& event_json)
{
    lock_guard<mutex> lock(buffer_mutex);
    
    if (event_buffer.size() >= config->buffer_size)
    {
        // Drop oldest event if buffer is full
        event_buffer.pop();
        events_dropped++;
    }
    
    event_buffer.push(event_json);
    
    // Send if buffer reached threshold
    if (event_buffer.size() >= config->buffer_size / 10)
    {
        flush_buffer();
    }
}

void AIEventExporter::flush_buffer()
{
    lock_guard<mutex> lock(buffer_mutex);
    
    while (!event_buffer.empty())
    {
        const string& event = event_buffer.front();
        
        try
        {
            zmq::message_t message(event.size());
            memcpy(message.data(), event.data(), event.size());
            
            if (zmq_socket->send(message, zmq::send_flags::dontwait))
            {
                events_sent++;
            }
            else
            {
                events_dropped++;
                break; // Stop if send would block
            }
        }
        catch (const exception& e)
        {
            ErrorMessage("Failed to send event: %s\n", e.what());
            events_dropped++;
        }
        
        event_buffer.pop();
    }
}

//-------------------------------------------------------------------------
// API
//-------------------------------------------------------------------------

static Module* mod_ctor()
{
    return new AIEventExporterModule;
}

static void mod_dtor(Module* m)
{
    delete m;
}

static Inspector* ai_event_ctor(Module* m)
{
    AIEventExporterModule* mod = (AIEventExporterModule*)m;
    return new AIEventExporter(mod->get_config());
}

static void ai_event_dtor(Inspector* p)
{
    delete p;
}

static const InspectApi ai_event_api =
{
    {
        PT_INSPECTOR,
        sizeof(InspectApi),
        INSAPI_VERSION,
        0,
        API_RESERVED,
        API_OPTIONS,
        "ai_event_exporter",
        "Export Snort3 events to AI-Ops framework via ZeroMQ",
        mod_ctor,
        mod_dtor
    },
    IT_PROBE,
    PROTO_BIT__ALL,
    nullptr, // buffers
    "ai-ops",
    nullptr, // pinit
    nullptr, // pterm
    nullptr, // tinit
    nullptr, // tterm
    ai_event_ctor,
    ai_event_dtor,
    nullptr, // ssn
    nullptr  // reset
};

SO_PUBLIC const BaseApi* snort_plugins[] =
{
    &ai_event_api.base,
    nullptr
};
