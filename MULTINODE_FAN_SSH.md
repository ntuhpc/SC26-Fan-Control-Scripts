# Multinode Fan Control SSH-based

## Set up of hardware

System: 2 nodes ("coffeepot1" and "coffeepot3"), connected to each other via ethernet. Direct ssh command from one node to each other is:
- `ssh coffeepot1-etn`
- `ssh coffeepot3-etn`

Command to ssh into each node from local computer is
- `ssh coffeepot1`
- `ssh coffeepot3`

## Fan control script

### For coffeepot1

- Before, setting the percentage manually, set to manual mode (default is max speed): `sudo ipmitool raw 0x30 0x45 0x01 0x01`
- Set zone and speed percentage: `sudo ipmitool raw 0x30 0x70 0x66 0x01 0x0<zone> 0x<speed percentage>`
- There are 2 zones (<zone>): 0x00 and 0x01 (zone 0 and zone 1)
- The <speed_percentage> is in hex (for instance, 50% is 0x32 and 100% is 0x64 - so we need to convert from decimal input to hex later to feed into this command later). Its range is 0 to 100 (decimal)

### For coffeepot3

- Before, setting the percentage manually, set to manual mode first: `sudo ipmitool raw 0x30 0x70 0x66 2 1`
- Set zone and speed percentage: ``sudo ipmitool raw 0x30 0x70 0x66 1 <zone> <speed percentage>`
    - <zone> takes value 0 and 1 (zone 0 and zone 1)
    - <speed_percentage> takes a decimal value 0 to 100

## Fan control idea

- Command 1 (setting zone and fan percentage across nodes): set_fan(<node_name>, <zone>, <speed_percentage>)
    - <node_name> takes in an array (for instance [cp1,cp3])
    - <zone> takes an array (for instance [0,1]). Important: you need to do param matching (for instance, the zone array entry 0 is for node array entry 0)
    - <speed_percentage> takes an array of decimals (for instance [50, 100]). Important: you need to do param matching (for instance, the speed percentage array entry 0 is for node array entry 0). Another point: you need to do converting from decimal input to hex for coffeepot1.

- Command 2 (setting every zone and speed to 50): killXthree(void)
    - This commands does need parsing - it launch ssh commands and set the speed for every zone for every fan.

- The commands are executed via ssh. So we can launch these from any nodes.

## Proposed implementation

### Summary

Build a manual Python CLI usable from either `coffeepot1` or `coffeepot3`.

- Execute locally without SSH when targeting the current node.
- Use direct Ethernet SSH for the other node only.
- Use explicit node, zone, and percentage targets instead of parallel arrays.
- Keep automatic temperature-based control out of version 1.
- Use 50% on all reachable zones as the fixed recovery profile after a partial failure.

### CLI and node helper

The CLI should provide commands such as:

```text
fanctl set --node cp1 --zone 0 --percent 50
fanctl apply --target cp1:0=50 --target cp3:1=75
fanctl set-all --percent 50
fanctl killXthree
fanctl doctor
fanctl --dry-run ...
```

`killXthree` is retained as a compatibility alias for `set-all --percent 50`.
The CLI must validate node names, zones `0`/`1`, and percentages `0` through `100`
before issuing any command.

Install a root-owned node helper on each machine. The helper should:

- accept only validated fan operations;
- run the appropriate `ipmitool raw` sequence for that node;
- serialize updates with a local lock; and
- be invoked through `sudo -n`, without handling passwords.

The helper must not expose unrestricted `ipmitool` access. Passwordless execution
should be granted only to the existing administrator/sudo group.

### Node-specific protocols

For `coffeepot1`, enable manual mode with:

```text
sudo ipmitool raw 0x30 0x45 0x01 0x01
```

Set a zone with:

```text
sudo ipmitool raw 0x30 0x70 0x66 0x01 0x0<zone> 0x<speed>
```

The percentage must be converted from decimal to hexadecimal; for example,
50% becomes `0x32`.

For `coffeepot3`, enable manual mode with:

```text
sudo ipmitool raw 0x30 0x70 0x66 2 1
```

Set a zone with:

```text
sudo ipmitool raw 0x30 0x70 0x66 1 <zone> <speed>
```

The zone and percentage are passed as decimal values.

### SSH and failure behavior

Standardize the direct Ethernet aliases as `coffeepot1-etn` and
`coffeepot3-etn`; correct the existing `coffepot3-etn` spelling typo.
SSH must use key-based authentication and `BatchMode=yes`; password prompts are
not supported.

For multi-node operations, run preflight checks before making changes. If an
operation partially fails, attempt to set every reachable affected node to 50%
and return a non-success status with per-node results. A recovery failure must
also be reported explicitly.

### Testing and acceptance

- Unit-test cp1 command generation, including decimal `50` becoming `0x32`.
- Unit-test cp3 command generation with decimal percentages.
- Test invalid zones, percentages, node names, malformed targets, and duplicates.
- Test local execution versus remote direct-Ethernet execution.
- Test SSH timeout, missing key, unreachable node, helper failure, and recovery failure.
- Verify `--dry-run` performs no writes and prints the intended commands.
- On hardware, verify manual mode, both zones at 50%, and the `killXthree` alias on both nodes.
