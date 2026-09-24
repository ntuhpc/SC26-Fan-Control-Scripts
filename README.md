# Coffeepot multinode fan control

This repository contains a manual fan controller for Coffeepot1 (`cp1`) and
Coffeepot3 (`cp3`). You can run it from either node. It controls the local node
directly and connects to the other over the direct Ethernet link using SSH.
The controller does not adjust fan speeds automatically from temperature.

## Before you start

On both nodes, make sure `ipmitool` and `flock` are installed and that the
direct Ethernet SSH aliases `coffeepot1-etn` and `coffeepot3-etn` work with
key-based authentication. Password prompts are not supported. The account
running the controller must be in the `sudo` group.

Install the helper on both nodes from the `ssh-based/` directory:

```sh
sudo install -o root -g root -m 0755 fan-node-helper /usr/local/sbin/fan-node-helper
```

Install the CLI in a user executable directory, for example:

```sh
mkdir -p "$HOME/bin"
install -m 0755 fanctl.py "$HOME/bin/fanctl"
```

Ensure `~/bin` is on your `PATH`. Repeat on both nodes if you want to run the
CLI from either one.

## Sudo setup

The CLI calls the root-owned helper using `sudo -n`, so it never asks for a
password. On each node, create a sudoers entry that permits members of the
existing `sudo` group to run this helper only:

```sh
sudo visudo -f /etc/sudoers.d/fanctl
```

Add this line in the editor:

```text
%sudo ALL=(root) NOPASSWD: /usr/local/sbin/fan-node-helper
```

Validate the entry:

```sh
sudo visudo -c -f /etc/sudoers.d/fanctl
```

This does not grant passwordless access to arbitrary `ipmitool` commands. The
helper accepts only validated `check` and `set` requests.

## Commands

Set one zone on one node:

```sh
fanctl set --node cp1 --zone 0 --percent 50
fanctl set --node cp3 --zone 1 --percent 75
```

Apply multiple explicit targets in one operation:

```sh
fanctl apply --target cp1:0=50 --target cp3:1=75
```

Set every zone on both nodes, or use the compatibility alias for 50%:

```sh
fanctl set-all --percent 50
fanctl killXthree
```

Check helper connectivity and print commands without making changes:

```sh
fanctl doctor
fanctl --dry-run apply --target cp1:0=50 --target cp3:1=75
```

Zones must be `0` or `1`; percentages must be from `0` to `100`. Coffeepot1
receives the percentage in hexadecimal (`50` becomes `0x32`); Coffeepot3
receives decimal values. Each cp3 set enables manual fan control first and
leaves manual control enabled afterward.

Multi-node requests check all target nodes before changing any fans. If a set
fails after preflight, the controller attempts to set each requested zone on
the affected node to 50% and reports both the original and recovery results.

## Files

- [`MULTINODE_FAN_SSH.md`](MULTINODE_FAN_SSH.md): design and implementation plan.
- [`ssh-based/`](ssh-based/): CLI, node helper, and setup notes.
