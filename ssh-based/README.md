# SSH based multinode fan control

This is the manual first version described in `../MULTINODE_FAN_SSH.md`. Run
`fanctl.py` from either Coffeepot node. It calls the helper locally for the
current node and uses key based SSH over the direct Ethernet alias for the
other. There is no temperature feedback. For cp3, a set operation enables
manual mode before setting the zone and leaves manual mode enabled afterward.

## Install

Install `fan-node-helper` on both nodes as `/usr/local/sbin/fan-node-helper`,
owned by root and writable only by root. Install `fanctl.py` in a user
executable location, for example as `~/bin/fanctl`. Configure
`coffeepot1-etn` and `coffeepot3-etn` in
SSH config on each node and verify key access works without a password prompt.

Examples:

```text
fanctl set --node cp1 --zone 0 --percent 50
fanctl apply --target cp1:0=50 --target cp3:1=75
fanctl set-all --percent 50
fanctl killXthree
fanctl doctor
fanctl --dry-run apply --target cp1:0=50 --target cp3:1=75
```

Multi-node commands preflight each requested node before changes. If a set
fails, the CLI attempts 50% on each requested zone of each failed node and
reports set and recovery results separately. `killXthree` sets both zones on
both nodes to 50%.

## Manual privileged setup

Run these commands yourself on each node. They allow members of the existing
`sudo` group to invoke only the validated helper without a password. They do
not grant unrestricted `ipmitool` access. The account running `fanctl` must be
a member of `sudo`.

```sh
sudo install -o root -g root -m 0755 fan-node-helper /usr/local/sbin/fan-node-helper
sudo visudo -f /etc/sudoers.d/fanctl
```

Add this rule in the editor opened by `visudo`:

```text
%sudo ALL=(root) NOPASSWD: /usr/local/sbin/fan-node-helper
```

Then validate the rule:

```sh
sudo visudo -c -f /etc/sudoers.d/fanctl
```

The helper requires `flock` and `ipmitool` on each node. SSH key access to the
other node's direct Ethernet alias is also required.
