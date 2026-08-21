#!/usr/bin/env python3
"""Verify latsetter set-local rules by measuring RTT to local ports.

Measures STEADY-STATE RTT: for TCP the connection is established once,
then request/response cycles are timed on the existing socket (so the
connection-setup delay is excluded).

Usage:  python3 verify_set_local.py [--udp] [port ...]
        (defaults to 8080 8082 9999; default protocol is tcp)
"""
import argparse
import socket
import threading
import time


def tcp_server(port: int) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.listen(5)
    while True:
        conn, _ = s.accept()
        while True:
            data = conn.recv(1024)
            if not data:          # client closed -> end this connection
                break
            conn.sendall(b"ok")
        conn.close()


def udp_server(port: int) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    while True:
        data, addr = s.recvfrom(1024)
        s.sendto(data, addr)


def measure_tcp(port: int, n: int = 5) -> list[float]:
    """Steady-state RTT: connect once, then time request/response cycles."""
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    samples = []
    for _ in range(n):
        t0 = time.perf_counter()
        s.sendall(b"ping")
        s.recv(1024)
        samples.append((time.perf_counter() - t0) * 1000)
    s.close()
    return samples


def measure_udp(port: int, n: int = 5) -> list[float]:
    samples = []
    for _ in range(n):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(5)
        t0 = time.perf_counter()
        s.sendto(b"ping", ("127.0.0.1", port))
        s.recvfrom(1024)
        s.close()
        samples.append((time.perf_counter() - t0) * 1000)
    return samples


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--udp", action="store_true", help="test UDP instead of TCP")
    ap.add_argument("ports", nargs="*", type=int, default=[8080, 8082, 9999])
    args = ap.parse_args()

    server_fn = udp_server if args.udp else tcp_server
    measure_fn = measure_udp if args.udp else measure_tcp

    threads = [
        threading.Thread(target=server_fn, args=(p,), daemon=True)
        for p in args.ports
    ]
    for t in threads:
        t.start()
    time.sleep(0.2)

    proto = "udp" if args.udp else "tcp"
    for p in args.ports:
        samples = measure_fn(p)
        avg = sum(samples) / len(samples)
        print(
            f"{proto} port {p:5d}: avg {avg:7.1f} ms   "
            + "  ".join(f"{s:.1f}" for s in samples)
        )


if __name__ == "__main__":
    main()
