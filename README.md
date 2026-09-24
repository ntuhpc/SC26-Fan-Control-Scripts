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

From this repository's `ssh-based/` directory, install the helper on each
node. The helper must be root owned because it runs the hardware commands:

```sh
sudo install -o root -g root -m 0755 fan-node-helper /usr/local/sbin/fan-node-helper
```

Install the CLI in a user executable directory on each node where you want to
run it. Run these commands from `ssh-based/`:

```sh
mkdir -p "$HOME/bin"
install -m 0755 fanctl.py "$HOME/bin/fanctl"
```

Ensure `~/bin` is on your `PATH`. If it is not already in your shell setup, add
this line to `~/.bashrc`, then open a new shell:

```sh
export PATH="$HOME/bin:$PATH"
```

Repeat the helper and CLI installation on both cp1 and cp3 if you want to use
the CLI from either node. SSH must already be configured so the aliases
`coffeepot1-etn` and `coffeepot3-etn` connect directly over Ethernet using keys.

## Sudo setup

Perform these steps separately on cp1 and cp3. The CLI calls the root-owned
helper with `sudo -n`, which means sudo must be configured to allow the helper
without prompting for a password.

First, check that your account belongs to the existing `sudo` group. In the
output, look for the word `sudo`:

```sh
id -nG "$USER"
```

Next, open the sudoers drop-in file with `visudo`. This validates the file's
syntax when it is saved:

```sh
sudo visudo -f /etc/sudoers.d/fanctl
```

In the editor, add this rule and save the file. It lets members of the `sudo`
group run only `/usr/local/sbin/fan-node-helper` as root without a password:

```text
%sudo ALL=(root) NOPASSWD: /usr/local/sbin/fan-node-helper
```

Finally, check that the new sudoers file parses correctly:

```sh
sudo visudo -c -f /etc/sudoers.d/fanctl
```

This does not grant passwordless access to arbitrary `ipmitool` commands. The
helper accepts only validated `check` and `set` requests.

## Commands and parameters

Run commands in a terminal on either Coffeepot node. The general form is:

```text
fanctl [--dry-run] COMMAND [OPTIONS]
```

`--dry-run` is optional and must come before the command name. It prints the
helper and SSH commands that would run. It does not contact the nodes or
change fan settings.

Parameters used by the commands:

- `--node cp1` or `--node cp3` selects Coffeepot1 or Coffeepot3.
- `--zone 0` or `--zone 1` selects one of that node's two fan zones.
- `--percent N` sets the speed to a whole number from `0` to `100`.
- `--target NODE:ZONE=PERCENT` combines the node, zone, and speed. For example,
  `cp1:0=50` means zone 0 on cp1 at 50 percent.

### Set one zone

`set` changes a single zone on one selected node. This example sets cp1, zone
0, to 50 percent:

```sh
fanctl set --node cp1 --zone 0 --percent 50
```

This example sets cp3, zone 1, to 75 percent:

```sh
fanctl set --node cp3 --zone 1 --percent 75
```

### Apply selected targets

`apply` takes one or more `--target` parameters. Each target uses the format
`NODE:ZONE=PERCENT`. This command sets cp1 zone 0 to 50% and cp3 zone 1 to
75%:

```sh
fanctl apply --target cp1:0=50 --target cp3:1=75
```

You can also select several zones on the same node. Do not repeat a node/zone
pair:

```sh
fanctl apply --target cp1:0=40 --target cp1:1=60 --target cp3:0=50
```

### Set all zones

`set-all --percent N` sets both zones on both nodes to the same speed. Replace
`N` with a whole number from `0` to `100`. This example sets all four zones to
50%:

```sh
fanctl set-all --percent 50
```

`killXthree` is a compatibility alias for setting both zones on both nodes to
50%. It takes no parameters:

```sh
fanctl killXthree
```

### Check setup and preview a change

`doctor` checks whether the helper can be reached on both nodes and reports
whether the local machine is recognized:

```sh
fanctl doctor
```

Put `--dry-run` before a command to preview it. This example prints the
preflight and helper commands for two targets without connecting to either
node:

```sh
fanctl --dry-run apply --target cp1:0=50 --target cp3:1=75
```

### Node behavior and failures

The CLI validates node names, zones, percentages, malformed targets, and
duplicate node/zone pairs before running a helper. It runs the helper directly
for the local machine and uses SSH for the other node. The helper serializes
fan updates with a lock.

On cp1, each update enables manual mode and sets the selected zone. The speed
is converted to hexadecimal for `ipmitool`; for example, 50% becomes `0x32`.
On cp3, each update enables manual mode and sets the selected zone using the
decimal percentage. Manual mode stays enabled after the update. Temperature
based automatic speed changes are not part of this version.

For multi-node requests, the CLI checks every target node before changing any
fans. If a preflight check fails, it makes no changes. If a fan update fails
after preflight, it attempts 50% recovery on each requested zone of the
affected node. It reports both the original update and recovery result, and
returns a failure status.

## Files

- [`MULTINODE_FAN_SSH.md`](MULTINODE_FAN_SSH.md): design and implementation plan.
- [`ssh-based/`](ssh-based/): CLI, node helper, and setup notes.
