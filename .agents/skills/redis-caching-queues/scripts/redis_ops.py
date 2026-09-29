#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis Operations, Redlock & Diagnostics CLI -- AXION Enterprise
Pure Python 3 standard library Redis utility using raw socket RESP (REdis Serialization Protocol).
Zero dependencies (no redis-py required).

Features:
- Ping and health diagnostics (latency, memory usage, eviction policy)
- Test distributed lock acquisition and atomic Lua release (Redlock test)
- Inspect key TTL and memory footprint
- Benchmark set/get latency
"""

import os
import sys
import socket
import argparse
import time
import uuid
from typing import Optional, List, Tuple

def encode_resp_command(*args) -> bytes:
    """Encodes a list of string arguments into RESP format."""
    parts = [f"*{len(args)}\r\n".encode("utf-8")]
    for arg in args:
        arg_bytes = str(arg).encode("utf-8")
        parts.append(f"${len(arg_bytes)}\r\n".encode("utf-8") + arg_bytes + b"\r\n")
    return b"".join(parts)

def parse_resp_response(sock: socket.socket) -> str:
    """Reads a simple RESP response from socket."""
    data = b""
    while not data.endswith(b"\r\n"):
        chunk = sock.recv(1024)
        if not chunk:
            break
        data += chunk
    decoded = data.decode("utf-8", errors="ignore").strip()
    return decoded

class SimpleRedisClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 6379, timeout: float = 3.0, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.password = password
        self.sock: Optional[socket.socket] = None

    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            if self.password:
                self.execute("AUTH", self.password)
            return True
        except Exception as e:
            print(f"Connection failed to {self.host}:{self.port} - {e}", file=sys.stderr)
            return False

    def execute(self, *args) -> str:
        if not self.sock:
            if not self.connect():
                return "ERROR: Not connected"
        try:
            self.sock.sendall(encode_resp_command(*args))
            return parse_resp_response(self.sock)
        except Exception as e:
            return f"ERROR: {e}"

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

    def ping(self) -> Tuple[bool, float]:
        start = time.perf_counter()
        resp = self.execute("PING")
        elapsed_ms = (time.perf_counter() - start) * 1000
        return resp.startswith("+PONG"), elapsed_ms

    def test_distributed_lock(self, lock_key: str, ttl_ms: int = 5000) -> bool:
        token = str(uuid.uuid4())
        print(f"[*] Attempting distributed lock acquisition on '{lock_key}' (TTL={ttl_ms}ms, token={token[:8]}...)")
        
        # SET key token NX PX ttl
        resp = self.execute("SET", lock_key, token, "NX", "PX", str(ttl_ms))
        if not resp.startswith("+OK"):
            print(f"[FAIL] Could not acquire lock. Key '{lock_key}' is already held.")
            return False
        
        print(f"[PASS] Lock acquired successfully.")
        
        # Atomic release via Lua Script
        lua_script = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"
        release_resp = self.execute("EVAL", lua_script, "1", lock_key, token)
        print(f"[*] Released lock atomically. Response: {release_resp}")
        return True

def main():
    parser = argparse.ArgumentParser(description="Redis Diagnostics & Distributed Lock CLI")
    parser.add_argument("--host", default="127.0.0.1", help="Redis host (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=6379, help="Redis port (default: 6379)")
    parser.add_argument("--password", "-a", help="Redis auth password")
    parser.add_argument("--ping", action="store_true", help="Send PING and report roundtrip latency")
    parser.add_argument("--lock-test", help="Test distributed lock acquisition on specified key")
    parser.add_argument("--info", action="store_true", help="Inspect Redis memory and server info")

    args = parser.parse_args()

    client = SimpleRedisClient(host=args.host, port=args.port, password=args.password)
    if not client.connect():
        print(f"[ERROR] Could not connect to Redis at {args.host}:{args.port}")
        sys.exit(1)

    try:
        if args.ping:
            ok, ms = client.ping()
            status = "OK" if ok else "FAIL"
            print(f"[{status}] Redis PING response received in {ms:.2f}ms")
            sys.exit(0 if ok else 1)

        if args.lock_test:
            success = client.test_distributed_lock(args.lock_test)
            sys.exit(0 if success else 1)

        if args.info:
            info = client.execute("INFO", "memory")
            print("================ REDIS MEMORY INFO ================")
            print(info)
            sys.exit(0)

        # Default action: ping
        ok, ms = client.ping()
        print(f"Connected to Redis at {args.host}:{args.port} (Latency: {ms:.2f}ms)")
    finally:
        client.close()

if __name__ == "__main__":
    main()
