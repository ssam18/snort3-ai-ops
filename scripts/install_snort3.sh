#!/bin/bash
#
# Snort3 Installation Script for Ubuntu/Debian
# This script installs Snort3 and all required dependencies
#
# Usage: sudo ./scripts/install_snort3.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SNORT3_VERSION="3.1.78.0"
DAQ_VERSION="3.0.13"
INSTALL_PREFIX="/usr/local"
BUILD_DIR="/tmp/snort3_build"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Snort3 Installation Script                        ║${NC}"
echo -e "${BLUE}║         Version: ${SNORT3_VERSION}                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Install dependencies
echo -e "${GREEN}[1/7]${NC} Installing build dependencies..."
apt-get update
apt-get install -y \
    build-essential \
    cmake \
    libpcap-dev \
    libpcre3-dev \
    libdumbnet-dev \
    bison \
    flex \
    zlib1g-dev \
    liblzma-dev \
    libssl-dev \
    libhwloc-dev \
    libluajit-5.1-dev \
    libunwind-dev \
    pkg-config \
    libmnl-dev \
    uuid-dev \
    libsafec-dev \
    libtool \
    autoconf \
    automake \
    git \
    wget

echo -e "${GREEN}✓${NC} Dependencies installed"

# Create build directory
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# Step 2: Install libdaq
echo -e "${GREEN}[2/7]${NC} Building and installing libdaq ${DAQ_VERSION}..."
if [ ! -d "libdaq-${DAQ_VERSION}" ]; then
    wget https://github.com/snort3/libdaq/archive/refs/tags/v${DAQ_VERSION}.tar.gz -O libdaq-${DAQ_VERSION}.tar.gz
    tar -xzf libdaq-${DAQ_VERSION}.tar.gz
fi

cd libdaq-${DAQ_VERSION}
./bootstrap
./configure --prefix=$INSTALL_PREFIX
make -j$(nproc)
make install
ldconfig

echo -e "${GREEN}✓${NC} libdaq installed"

cd $BUILD_DIR

# Step 3: Install Snort3
echo -e "${GREEN}[3/7]${NC} Building and installing Snort3 ${SNORT3_VERSION}..."
if [ ! -d "snort3-${SNORT3_VERSION}" ]; then
    wget https://github.com/snort3/snort3/archive/refs/tags/${SNORT3_VERSION}.tar.gz -O snort3-${SNORT3_VERSION}.tar.gz
    tar -xzf snort3-${SNORT3_VERSION}.tar.gz
fi

cd snort3-${SNORT3_VERSION}

# Configure with all features
./configure_cmake.sh \
    --prefix=$INSTALL_PREFIX

cd build
make -j$(nproc)
make install
ldconfig

echo -e "${GREEN}✓${NC} Snort3 installed"

# Step 4: Verify installation
echo -e "${GREEN}[4/7]${NC} Verifying Snort3 installation..."
snort -V
echo -e "${GREEN}✓${NC} Snort3 verified"

# Step 5: Create directory structure
echo -e "${GREEN}[5/7]${NC} Creating Snort3 directory structure..."
mkdir -p /etc/snort
mkdir -p /etc/snort/rules
mkdir -p /var/log/snort
mkdir -p /usr/local/lib/snort_dynamicrules
mkdir -p /usr/local/lib/snort/plugins

echo -e "${GREEN}✓${NC} Directories created"

# Step 6: Download and install community rules
echo -e "${GREEN}[6/7]${NC} Installing Snort3 community rules..."
cd /tmp
if [ ! -f "snort3-community-rules.tar.gz" ]; then
    wget https://www.snort.org/downloads/community/snort3-community-rules.tar.gz
    tar -xzf snort3-community-rules.tar.gz -C /etc/snort/rules/
fi

echo -e "${GREEN}✓${NC} Community rules installed"

# Step 7: Set permissions
echo -e "${GREEN}[7/7]${NC} Setting permissions..."
chmod -R 755 /etc/snort
chmod -R 755 /var/log/snort
chmod -R 755 /usr/local/lib/snort

# Create snort user and group
if ! id -u snort >/dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin -M -c "Snort IDS" snort
    echo -e "${GREEN}✓${NC} Snort user created"
fi

chown -R snort:snort /var/log/snort

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Snort3 Installation Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Installation Details:"
echo "  Snort3 Version: ${SNORT3_VERSION}"
echo "  DAQ Version: ${DAQ_VERSION}"
echo "  Install Location: ${INSTALL_PREFIX}"
echo "  Configuration: /etc/snort/"
echo "  Logs: /var/log/snort/"
echo "  Plugins: /usr/local/lib/snort/plugins/"
echo ""
echo "Next Steps:"
echo "  1. Build the AI Event Exporter plugin:"
echo "     cd snort3-plugins/event_exporter"
echo "     mkdir build && cd build"
echo "     cmake .."
echo "     make"
echo "     sudo make install"
echo ""
echo "  2. Configure Snort3:"
echo "     sudo cp config/snort.lua /etc/snort/"
echo ""
echo "  3. Test Snort3:"
echo "     sudo snort -c /etc/snort/snort.lua"
echo ""
echo "  4. Start AI-Ops engine:"
echo "     python main.py start"
echo ""

# Cleanup
echo -e "${YELLOW}→${NC} Cleaning up build directory..."
rm -rf $BUILD_DIR
echo -e "${GREEN}✓${NC} Cleanup complete"

echo ""
echo "For more information, see:"
echo "  - SETUP_GUIDE.md"
echo "  - README.md"
echo ""
