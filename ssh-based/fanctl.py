#!/usr/bin/env python3
"""Manual two-node fan controller for coffeepot1 and coffeepot3."""

import argparse
import socket
import subprocess
import sys

HELPER = "/usr/local/sbin/fan-node-helper"
NODES = {"cp1": ("coffeepot1", "coffeepot1-etn"), "cp3": ("coffeepot3", "coffeepot3-etn")}
ZONES = (0, 1)
SSH_TIMEOUT = 10


def local_node():
    host = socket.gethostname().split(".", 1)[0].lower()
    for node, (hostname, _) in NODES.items():
        if host == hostname:
            return node
    return None


def parse_target(value):
    try:
        node_zone, raw_percent = value.split("=", 1)
        node, raw_zone = node_zone.split(":", 1)
        zone, percent = int(raw_zone), int(raw_percent)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError("target must be NODE:ZONE=PERCENT, e.g. cp1:0=50")
    if node not in NODES:
        raise argparse.ArgumentTypeError(f"unknown node {node!r}; choose cp1 or cp3")
    if zone not in ZONES:
        raise argparse.ArgumentTypeError("zone must be 0 or 1")
    if not 0 <= percent <= 100:
        raise argparse.ArgumentTypeError("percent must be from 0 through 100")
    return node, zone, percent


def run(node, args, dry_run=False):
    helper_args = ["sudo", "-n", HELPER, *map(str, args)]
    if node == local_node():
        command = helper_args
    else:
        command = ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={SSH_TIMEOUT}",
                   NODES[node][1], *helper_args]
    if dry_run:
        print(f"{node}: {' '.join(command)}")
        return True, "dry run"
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=SSH_TIMEOUT + 2)
        detail = (result.stdout + result.stderr).strip()
        return result.returncode == 0, detail or f"exit {result.returncode}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)


def main():
    parser = argparse.ArgumentParser(description="Manually control cp1/cp3 fan zones")
    parser.add_argument("--dry-run", action="store_true", help="print commands without contacting nodes")
    subs = parser.add_subparsers(dest="action", required=True)
    p = subs.add_parser("set", help="set one fan zone")
    p.add_argument("--node", choices=NODES, required=True)
    p.add_argument("--zone", type=int, choices=ZONES, required=True)
    p.add_argument("--percent", type=int, required=True)
    p = subs.add_parser("apply", help="apply explicit targets")
    p.add_argument("--target", action="append", type=parse_target, required=True)
    p = subs.add_parser("set-all", help="set both zones on both nodes")
    p.add_argument("--percent", type=int, required=True)
    subs.add_parser("killXthree", help="alias for set-all at 50 percent")
    subs.add_parser("doctor", help="check local identity and both node helpers")
    opts = parser.parse_args()

    if hasattr(opts, "percent") and not 0 <= opts.percent <= 100:
        parser.error("percent must be from 0 through 100")
    if opts.action == "doctor":
        print(f"local node: {local_node() or 'unrecognized; run from a Coffeepot node'}")
        failed = False
        for node in NODES:
            ok, detail = run(node, ["check"], opts.dry_run)
            print(f"{node}: {'OK' if ok else 'FAIL'}: {detail}")
            failed |= not ok
        return int(failed)

    if opts.action == "set":
        targets = [(opts.node, opts.zone, opts.percent)]
    elif opts.action == "apply":
        targets = opts.target
    else:
        percent = 50 if opts.action == "killXthree" else opts.percent
        targets = [(node, zone, percent) for node in NODES for zone in ZONES]

    keys = [(node, zone) for node, zone, _ in targets]
    if len(set(keys)) != len(keys):
        parser.error("duplicate node/zone targets are not allowed")
    nodes = list(dict.fromkeys(node for node, _, _ in targets))
    reachable = set()
    for node in nodes:
        ok, detail = run(node, ["check"], opts.dry_run)
        print(f"preflight {node}: {'OK' if ok else 'FAIL'}: {detail}")
        if ok:
            reachable.add(node)
    if reachable != set(nodes):
        print("No fan changes made because preflight failed.", file=sys.stderr)
        return 1
    if opts.dry_run:
        for node, zone, percent in targets:
            run(node, ["set", zone, percent], True)
        return 0

    failed_nodes = set()
    for node, zone, percent in targets:
        ok, detail = run(node, ["set", zone, percent])
        print(f"set {node} zone {zone} to {percent}%: {'OK' if ok else 'FAIL'}: {detail}")
        if not ok:
            failed_nodes.add(node)
    if failed_nodes:
        print("Attempting 50% recovery on failed nodes.", file=sys.stderr)
        recovery_failed = False
        for node, zone, _ in targets:
            if node in failed_nodes:
                ok, detail = run(node, ["set", zone, 50])
                print(f"recovery {node} zone {zone} to 50%: {'OK' if ok else 'FAIL'}: {detail}")
                recovery_failed |= not ok
        return 2 if recovery_failed else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
