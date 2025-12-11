//--------------------------------------------------------------------------
// Copyright (C) 2025 Snort3-AI-Ops Contributors
//
// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License Version 2 as published
// by the Free Software Foundation.  You may not use, modify or distribute
// this program under any other version of the GNU General Public License.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//--------------------------------------------------------------------------
// ai_event_exporter.h - Export Snort3 events to AI-Ops framework

#ifndef AI_EVENT_EXPORTER_H
#define AI_EVENT_EXPORTER_H

#include "framework/inspector.h"
#include "framework/module.h"
#include <zmq.hpp>
#include <string>
#include <queue>
#include <mutex>

//-------------------------------------------------------------------------
// Configuration
//-------------------------------------------------------------------------

struct AIEventExporterConfig
{
    std::string endpoint;
    bool export_alerts;
    bool export_flows;
    bool export_stats;
    std::string min_severity;
    size_t buffer_size;
    uint32_t flush_interval;
};

//-------------------------------------------------------------------------
// Module
//-------------------------------------------------------------------------

class AIEventExporterModule : public snort::Module
{
public:
    AIEventExporterModule();
    ~AIEventExporterModule() override = default;

    bool set(const char*, snort::Value&, snort::SnortConfig*) override;
    bool begin(const char*, int, snort::SnortConfig*) override;
    bool end(const char*, int, snort::SnortConfig*) override;

    Usage get_usage() const override
    { return INSPECT; }

    bool is_bindable() const override
    { return false; }

    AIEventExporterConfig* get_config()
    { return &config; }

private:
    AIEventExporterConfig config;
};

//-------------------------------------------------------------------------
// Inspector
//-------------------------------------------------------------------------

class AIEventExporter : public snort::Inspector
{
public:
    AIEventExporter(AIEventExporterConfig* c);
    ~AIEventExporter() override;

    void show(const snort::SnortConfig*) const override;
    void eval(snort::Packet*) override;
    
    bool configure(snort::SnortConfig*) override;
    void tinit() override;
    void tterm() override;

private:
    void export_alert(snort::Packet* p);
    void export_flow(snort::Packet* p);
    void send_event(const std::string& event_json);
    void flush_buffer();
    
    std::string serialize_packet(snort::Packet* p);
    std::string serialize_flow(snort::Flow* f);

private:
    AIEventExporterConfig* config;
    zmq::context_t* zmq_context;
    zmq::socket_t* zmq_socket;
    std::queue<std::string> event_buffer;
    std::mutex buffer_mutex;
    uint64_t events_sent;
    uint64_t events_dropped;
};

#endif
