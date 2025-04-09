#!/bin/bash

# Generate output filename with timestamp
output_file="system_info.txt"

# Start output capturing
{
echo "=========================================="
echo "System Information Report"
echo "=========================================="

# Server Name
echo -e "\nServer Information:"
echo "----------------------------------------"
echo "Server Name:"
hostname

# Operating System Version
echo -e "\nOperating System Version:"
cat /etc/os-release | grep "PRETTY_NAME" | cut -d'"' -f2

# IP Address
echo -e "\nNetwork Information:"
echo "----------------------------------------"
echo "IP Address:"
ip addr | grep 'inet ' | grep -v '127.0.0.1' | awk '
BEGIN { count = 0 }
{
    if (count % 4 == 0) {
        if (count > 0) printf "]\n"
        printf "["
    } else {
        printf ", "
    }
    printf "%s", $2
    count++
}
END {
    if (count > 0) printf "]\n"
}'

# MAC Address
echo -e "\nMAC Address:"
ip link | grep "link/ether" | awk '
BEGIN { count = 0 }
{
    if (count % 4 == 0) {
        if (count > 0) printf "]\n"
        printf "["
    } else {
        printf ", "
    }
    printf "%s", $2
    count++
}
END {
    if (count > 0) printf "]\n"
}'

echo -e "\nProcessor Information:"
echo "----------------------------------------"
# CPU Model
echo "Processor Model:"
cat /proc/cpuinfo | grep "model name" | head -n 1 | cut -d':' -f2 | sed 's/^[ \t]*//'

# CPU Architecture
echo -e "\nProcessor Architecture:"
uname -m

# CPU Frequency
echo -e "\nProcessor Frequency Information:"
# Get base frequency from model name
echo -n "Base Frequency: "
cat /proc/cpuinfo | grep "model name" | head -n 1 | grep -o "@.*GHz" | sed 's/@ //'

# Get max frequency - works in both English and Chinese environments
echo -n "Maximum Frequency: "
lscpu | grep -E "CPU max MHz|CPU 最大 MHz" | awk '{printf "%.2f GHz\n", $NF/1000}'
lscpu -e

# CPU Flags
echo -e "\nProcessor Flags:"
# Get flags from lscpu, supporting both English and Chinese environments
lscpu | grep -E "Flags:|标记：" | sed -E 's/^(Flags:|标记：)\s*//' | fold -s -w 75

# CPU Cache Information
echo -e "\nProcessor Cache Information:"
lscpu | awk '
    /^L1d/ {gsub(/^L1d.*:|^L1d.*：/, "L1 Data Cache:      "); print}
    /^L1i/ {gsub(/^L1i.*:|^L1i.*：/, "L1 Instruction Cache:"); print}
    /^L2/  {gsub(/^L2.*:|^L2.*：/,   "L2 Cache:           "); print}
    /^L3/  {gsub(/^L3.*:|^L3.*：/,   "L3 Cache:           "); print}
'

# CPU Information
echo -e "\nProcessor Details:"
echo "Number of Physical CPUs: $(grep "physical id" /proc/cpuinfo | sort -u | wc -l)"
echo "CPU Cores: $(grep "cpu cores" /proc/cpuinfo | head -n 1 | cut -d':' -f2 | sed 's/^[ \t]*//')"
echo "Logical CPU Cores: $(grep "processor" /proc/cpuinfo | wc -l)"

echo -e "\nMemory Information:"
echo "----------------------------------------"
# Memory Usage
echo "Memory Usage:"
LANG=C free -h | awk 'NR==2 {print "Total Memory: " $2 "\nUsed Memory: " $3 "\nAvailable Memory: " $7}'

echo -e "\nStorage Information:"
echo "----------------------------------------"
# Disk Usage
echo "Disk Usage:"
df -h | grep '^/dev/' | awk '{print $1 " Total Size: " $2 " Used: " $3 " Available: " $4 " Usage: " $5 " Mount Point: " $6}'

} | tee "$output_file"
 