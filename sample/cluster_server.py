#!/usr/bin/env python3
"""Echo server for testing latsetter cluster-mode (set) rules.

Usage:  python3 cluster_server.py [port]   (default 8080)
"""
import socket
import sys


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(5)
    print(f"listening on 0.0.0.0:{port}")
    while True:
        conn, addr = s.accept()
        print(f"connection from {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)
        conn.close()


if __name__ == "__main__":
    main()
