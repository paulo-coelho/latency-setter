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

## Sample files

The `./sample` folder contains example inputs and a helper script:

- `ips.csv` — example `Zone,IP` mapping for cluster mode.
- `latencies.csv` — example latency matrix (ms) for cluster mode.
- `cluster_server.py` / `cluster_client.py` — echo server + RTT client to test
  cluster-mode (`set`) rules between two nodes. Run the server on the
  destination node, then the client on the source node:

      # on the destination node
      python3 sample/cluster_server.py 8080
      # on the source node
      python3 sample/cluster_client.py <server-ip> 8080

  Expected RTT is `D(A→B) + D(B→A)` (both directions are delayed in cluster
  mode). No protocol flag is needed — `set` filters on destination IP only.
- `set_local_destinations.csv` — example `Port,Latency` file for `set-local`.
- `verify_set_local.py` — measures steady-state RTT to local ports to confirm
  `set-local` rules are working. Run it with the rules active:

      sudo latsetter set-local sample/set_local_destinations.csv
      python3 sample/verify_set_local.py 8080 8082 9999

  It spins up a server on each port and times request/response cycles on an
  already-established connection (TCP) or per-datagram (UDP). Use `--udp` to
  test UDP rules (apply them with `--protocol udp` first). The default ports
  include `9999`, which is not in the destinations file, so it exercises the
  no-delay default class as a control.

## Notes

- You must run the commands as `root`
- Don't forget to undo the changes after running your experiments

## Latency semantics: one-way delay vs RTT

The CSV values are **one-way per-packet delays** (netem delays each matching
packet by that amount). What you observe as RTT depends on the mode and the
traffic pattern:

- **Cluster mode (`set`):** each node delays its own egress to the peer's IP,
  so both directions are always delayed. RTT between two nodes is
  `D(A→B) + D(B→A)` — constant for both connection setup and steady-state
  traffic. If the matrix is symmetric (`D(A→B)=D(B→A)=D`), you'll see `2D`.
- **Local mode (`set-local`):** the delay is per *destination port*, and the
  response returns to the client's *ephemeral* source port, which is not in
  the rules. So only the client→server direction is delayed:
  - **Steady-state RTT ≈ the CSV value** (1×) for both TCP and UDP on an
    established connection.
  - **During TCP connection setup** the client→server direction carries two
    delayed packets (SYN + data), so the first request can appear as ~2× the
    CSV value. This is transient and amortized once the connection is reused.

In short: for real framework traffic over persistent connections, the CSV
value is a good approximation of the RTT you'll observe in both modes.