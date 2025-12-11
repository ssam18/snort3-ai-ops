cmake_minimum_required(VERSION 3.10)
project(ai_event_exporter)

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find dependencies
find_package(PkgConfig REQUIRED)
pkg_check_modules(SNORT3 REQUIRED snort>=3.0)

# Find ZeroMQ
find_path(ZMQ_INCLUDE_DIR zmq.hpp)
find_library(ZMQ_LIBRARY NAMES zmq)

# Find nlohmann/json
find_path(JSON_INCLUDE_DIR nlohmann/json.hpp)

# Source files
set(SOURCES
    ai_event_exporter.cc
)

# Create shared library
add_library(ai_event_exporter MODULE ${SOURCES})

# Include directories
target_include_directories(ai_event_exporter PRIVATE
    ${SNORT3_INCLUDE_DIRS}
    ${ZMQ_INCLUDE_DIR}
    ${JSON_INCLUDE_DIR}
)

# Link libraries
target_link_libraries(ai_event_exporter
    ${ZMQ_LIBRARY}
)

# Compiler flags
target_compile_options(ai_event_exporter PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -fPIC
)

# Install
install(TARGETS ai_event_exporter
    LIBRARY DESTINATION lib/snort/plugins
)

# Print configuration summary
message(STATUS "AI Event Exporter Plugin Configuration:")
message(STATUS "  Snort3 include dirs: ${SNORT3_INCLUDE_DIRS}")
message(STATUS "  ZeroMQ include: ${ZMQ_INCLUDE_DIR}")
message(STATUS "  ZeroMQ library: ${ZMQ_LIBRARY}")
message(STATUS "  JSON include: ${JSON_INCLUDE_DIR}")
message(STATUS "  Install prefix: ${CMAKE_INSTALL_PREFIX}")
