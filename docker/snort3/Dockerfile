FROM ubuntu:22.04

# Snort3 with AI Event Exporter Plugin
LABEL maintainer="Snort3-AI-Ops"
LABEL description="Snort3 IPS with AI Event Exporter Plugin"

ENV DEBIAN_FRONTEND=noninteractive
ENV SNORT_VERSION=3.1.78.0

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libpcap-dev \
    libpcre3-dev \
    libdnet-dev \
    libdumbnet-dev \
    zlib1g-dev \
    liblzma-dev \
    libssl-dev \
    libhwloc-dev \
    libluajit-5.1-dev \
    pkg-config \
    bison \
    flex \
    libdaq-dev \
    libzmq3-dev \
    libmsgpackc2 \
    libmsgpack-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Snort3
WORKDIR /tmp
RUN wget https://github.com/snort3/snort3/archive/refs/tags/${SNORT_VERSION}.tar.gz && \
    tar xzf ${SNORT_VERSION}.tar.gz && \
    cd snort3-${SNORT_VERSION} && \
    ./configure_cmake.sh --prefix=/usr/local/snort --enable-tcmalloc && \
    cd build && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd /tmp && \
    rm -rf snort3-${SNORT_VERSION}*

# Copy AI Event Exporter plugin
COPY snort3-plugins/event_exporter /tmp/ai_event_exporter

# Build and install AI Event Exporter
WORKDIR /tmp/ai_event_exporter
RUN mkdir -p build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local/snort .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Create directories
RUN mkdir -p /etc/snort /var/log/snort /usr/local/lib/snort/plugins

# Add Snort to PATH
ENV PATH="/usr/local/snort/bin:${PATH}"
ENV LUA_PATH="/usr/local/snort/include/snort/lua/?.lua;;"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep snort || exit 1

WORKDIR /usr/local/snort
CMD ["snort", "--version"]
