## Latency setter script

Simulates the latencies among regions and availability zones, just like Amazon EC2.

## Requirements

Linux machine with `tc` (iproute2) installed; the script uses only the Python 3 standard library.

## Installation

Install the script to a directory in your PATH (defaults to `/usr/local/sbin`):

    sudo make install

or manually:

    sudo install -m 755 latsetter.py /usr/local/sbin/latsetter

## Usage

### Cluster mode (`set` / `unset`)

Run once per node to emulate inter-zone latencies between machines. You need two CSV files:

- `ips.csv` — maps each node IP to its zone (header `Zone,IP`).
- `latencies.csv` — latency matrix in ms (first row = destination zones, first column = source zones).

Examples of both files are under `./sample`.

To set the latencies for this node:

    sudo latsetter set <ips.csv> <latencies.csv> <interface-name>

The script looks up the interface's IPv4 address in `ips.csv` to find this node's zone, then installs a delay rule per destination zone. To undo:

    sudo latsetter unset <interface-name>

To set latencies for all nodes in a cluster, loop over the IPs:

    for i in `tail -n +2 <ips.csv> | cut -d , -f 2`; do
        ssh $i "sudo latsetter set <ips.csv> <latencies.csv> <interface-name>"
    done

### Local mode (`set-local`)

Emulate per-destination latencies on a single machine: all processes run on `127.0.0.1` with distinct ports. Provide a CSV with the destination port and its latency in ms (header optional):

    Port,Latency
    8080,90
    8081,90
    8082,3

Apply the rules (TCP by default; use `--protocol udp` for UDP):

    sudo latsetter set-local destinations.csv

To undo:

    sudo latsetter unset lo

## Notes

- You must run the commands as `root`
- Don't forget to undo the changes after running your experiments