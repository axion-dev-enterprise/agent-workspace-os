#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Payment Webhook Cryptographic Signer & Dispatcher -- AXION Enterprise
Generates valid HMAC-SHA256 signatures for Stripe and generic payment webhooks.
Tests webhook endpoints locally without needing external adquirente / Stripe CLI.

Runs on Python 3 standard library. Zero external dependencies.
"""

import os
import sys
import hmac
import hashlib
import time
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any

def generate_stripe_signature(payload_bytes: bytes, secret: str, timestamp: int) -> str:
    """Generates standard Stripe-Signature header: t=12345,v1=hex_hmac"""
    signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
    sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"

def generate_generic_hmac(payload_bytes: bytes, secret: str) -> str:
    """Generates standard sha256 hex HMAC signature"""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

def dispatch_webhook(url: str, payload: Dict[str, Any], secret: str, mode: str = "stripe") -> bool:
    payload_bytes = json.dumps(payload).encode("utf-8")
    now = int(time.time())

    headers = {"Content-Type": "application/json"}
    if mode == "stripe":
        headers["Stripe-Signature"] = generate_stripe_signature(payload_bytes, secret, now)
    else:
        headers["X-Webhook-Signature"] = generate_generic_hmac(payload_bytes, secret)
        headers["X-Webhook-Timestamp"] = str(now)

    print(f"[*] Dispatching {mode.upper()} webhook to {url}...")
    req = urllib.request.Request(url, data=payload_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            print(f"[PASS] Webhook delivered successfully! HTTP {resp.status}")
            print(f"       Response Body: {body[:150]}")
            return True
    except urllib.error.HTTPError as e:
        print(f"[FAIL] Server responded with HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[FAIL] Network error delivering webhook: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Payment Webhook Signer & Simulator CLI")
    parser.add_argument("--url", help="Target webhook endpoint URL (e.g. http://localhost:3000/api/webhooks/stripe)")
    parser.add_argument("--secret", default="whsec_test_secret_key_12345", help="Webhook signing secret")
    parser.add_argument("--mode", choices=["stripe", "generic"], default="stripe", help="Webhook signature format")
    parser.add_argument("--event", default="checkout.session.completed", help="Stripe event type to simulate")
    parser.add_argument("--amount-cents", type=int, default=4990, help="Transaction amount in cents")

    args = parser.parse_args()

    sample_payload = {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "type": args.event,
        "data": {
            "object": {
                "id": "cs_test_sample_12345",
                "object": "checkout.session",
                "amount_total": args.amount_cents,
                "currency": "brl",
                "customer": "cus_test_999",
                "payment_status": "paid",
                "status": "complete"
            }
        }
    }

    if args.url:
        ok = dispatch_webhook(args.url, sample_payload, args.secret, args.mode)
        sys.exit(0 if ok else 1)

    # If no URL given, generate signature and print sample
    payload_bytes = json.dumps(sample_payload).encode("utf-8")
    sig = generate_stripe_signature(payload_bytes, args.secret, int(time.time()))
    print("================ SAMPLE WEBHOOK SIGNATURE ================")
    print(f"Stripe-Signature Header: {sig}")
    print(f"Sample Payload:\n{json.dumps(sample_payload, indent=2)}")

if __name__ == "__main__":
    main()
