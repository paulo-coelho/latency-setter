#!/usr/bin/env python3
"""Measure steady-state RTT to a server to verify latsetter cluster-mode (set) rules.

Usage:  python3 cluster_client.py <server-ip> [port] [samples]
        (default port 8080, 5 samples)
"""
import socket
import sys
import time


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    s = socket.create_connection((host, port), timeout=5)
    samples = []
    for _ in range(n):
        t0 = time.perf_counter()
        s.sendall(b"ping")
        s.recv(1024)
        samples.append((time.perf_counter() - t0) * 1000)
    s.close()

    avg = sum(samples) / len(samples)
    print(
        f"RTT to {host}:{port}: avg {avg:.1f} ms   "
        + "  ".join(f"{x:.1f}" for x in samples)
    )


if __name__ == "__main__":
    main()
