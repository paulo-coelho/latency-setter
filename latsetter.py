#!/usr/bin/env python3

import csv
import subprocess
import os
import sys
import netifaces as nif


def usage():
    print("Usage: \t", sys.argv[0], "set ip-list latency-list iface-name")
    print("\tOR:\t", sys.argv[0], "unset iface-name")
    exit()


def run_command(cmd_list):
    """Executes system commands. Script must be run as root."""
    try:
        subprocess.run(cmd_list, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        # We ignore errors for 'del' as the qdisc might not exist yet
        if "del" not in cmd_list:
            print(f"Error executing {' '.join(cmd_list)}: {e.stderr}")


if os.geteuid() != 0:
    print("This script must be run as root. Please use: sudo", sys.argv[0], "...")
    sys.exit(1)

if len(sys.argv) < 3:
    usage()

if sys.argv[1] == "unset":
    iface = sys.argv[2]
    print(f"# Removing tc rules for {iface}")
    run_command(["tc", "qdisc", "del", "dev", iface, "root"])
    exit()

if sys.argv[1] != "set":
    usage()

ips_file = sys.argv[2]
lats_file = sys.argv[3]
iface = sys.argv[4]

with open(ips_file, "r") as f:
    ipData = list(csv.DictReader(f))

try:
    myip = nif.ifaddresses(iface)[nif.AF_INET][0]["addr"]
except (KeyError, ValueError, IndexError):
    print(f"Error: Could not find IP for interface {iface}")
    exit()

with open(lats_file, "r") as f:
    lats_rows = list(csv.reader(f))

# Find my zone
myzone = next((item["Zone"] for item in ipData if item["IP"] == myip), "")
if not myzone:
    print(f"IP {myip} not in IP file")
    exit()

# Map latencies
azs = lats_rows[0]
tlats = {}
for row in lats_rows[1:]:
    row_zone = row[0]
    for i in range(1, len(azs)):
        col_zone = azs[i]
        try:
            tlats[(row_zone, col_zone)] = float(row[i])
        except (ValueError, IndexError):
            continue

print(f"# Setting rules for interface {iface} in zone {myzone} with IP {myip}")

# Clear existing root (silently)
run_command(["tc", "qdisc", "del", "dev", iface, "root"])

run_command(
    [
        "tc",
        "qdisc",
        "add",
        "dev",
        iface,
        "root",
        "handle",
        "1:",
        "htb",
        "default",
        "10",
        "r2q",
        "1000",
    ]
)
run_command(
    [
        "tc",
        "class",
        "add",
        "dev",
        iface,
        "parent",
        "1:",
        "classid",
        "1:1",
        "htb",
        "rate",
        "1gbit",
    ]
)
run_command(
    [
        "tc",
        "class",
        "add",
        "dev",
        iface,
        "parent",
        "1:1",
        "classid",
        "1:10",
        "htb",
        "rate",
        "1gbit",
    ]
)
run_command(
    [
        "tc",
        "qdisc",
        "add",
        "dev",
        iface,
        "parent",
        "1:10",
        "handle",
        "10:",
        "sfq",
        "perturb",
        "10",
    ]
)

nextHandle = 11
for az in azs[1:]:
    lat = tlats.get((myzone, az))

    # Apply rules if latency > 0
    if lat is not None and lat > 0:
        delta = 0.05 * lat
        print(f"# Setting latency to {lat}ms for zone {az}")

        # Create class for this zone
        run_command(
            [
                "tc",
                "class",
                "add",
                "dev",
                iface,
                "parent",
                "1:1",
                "classid",
                f"1:{nextHandle}",
                "htb",
                "rate",
                "1gbit",
            ]
        )

        # Apply netem delay
        run_command(
            [
                "tc",
                "qdisc",
                "add",
                "dev",
                iface,
                "parent",
                f"1:{nextHandle}",
                "handle",
                f"{nextHandle}:",
                "netem",
                "delay",
                f"{lat}ms",
                f"{delta}ms",
                "distribution",
                "normal",
            ]
        )

        # Add filters for IPs in this zone
        for item in ipData:
            if item["Zone"] == az:
                target_ip = item["IP"]
                print(
                    f"\t# Latency from {myip} to {target_ip} set to {lat} +/- {delta}"
                )
                run_command(
                    [
                        "tc",
                        "filter",
                        "add",
                        "dev",
                        iface,
                        "protocol",
                        "ip",
                        "parent",
                        "1:",
                        "prio",
                        "1",
                        "u32",
                        "match",
                        "ip",
                        "dst",
                        f"{target_ip}/32",
                        "flowid",
                        f"1:{nextHandle}",
                    ]
                )

        nextHandle += 1
