# Multinode fan control: user guide

Use `fanctl` to set fan speeds on Coffeepot1 (`cp1`) and Coffeepot3 (`cp3`).
Run it from either node. It controls the current node directly and reaches the
other node through the direct Ethernet SSH connection. Each node has two fan
zones, `0` and `1`.

## 1. Step-by-step setup

Do these steps on **both** cp1 and cp3. Setup is done once per node. The
commands beginning with `sudo` must be run by you or the node administrator.

### Step 1: Log in and clone the repository

From your computer, log in to one node:

```sh
ssh coffeepot1
```

Use `ssh coffeepot3` when setting up cp3. On the node, clone the repository
and enter the directory containing the scripts:

```sh
git clone git@github.com:ntuhpc/SC26-Fan-Control-Scripts.git
cd SC26-Fan-Control-Scripts/ssh-based
```

If the clone says the directory already exists, update the existing copy
instead:

```sh
cd SC26-Fan-Control-Scripts
git pull --ff-only
cd ssh-based
```

### Step 2: Check the required programs and your account

The node needs `python3`, `ipmitool`, and `flock`. These commands show where
each program is installed; a missing program must be installed by the node
administrator:

```sh
command -v python3
command -v ipmitool
command -v flock
```

Check your groups. The output must contain `sudo`:

```sh
id -nG "$USER"
```

If `sudo` is absent, ask the node administrator to add your account to that
group and log out and back in before continuing.

### Step 3: Install the fan helper and set up sudo

From `SC26-Fan-Control-Scripts/ssh-based/`, copy `fan-node-helper` to the
location the CLI expects. The helper runs the node's `ipmitool` fan commands,
so it must be owned by root:

```sh
sudo install -o root -g root -m 0755 fan-node-helper /usr/local/sbin/fan-node-helper
```

The CLI calls this helper with `sudo -n`. That means it cannot answer a
password prompt. Open a sudo configuration file:

```sh
sudo visudo -f /etc/sudoers.d/fanctl
```

Enter this line in the editor, then save and close it:

```text
%sudo ALL=(root) NOPASSWD: /usr/local/sbin/fan-node-helper
```

The rule permits members of the `sudo` group to run this **specific helper**
as root without a password. It does not permit arbitrary passwordless
`ipmitool` commands. Check the saved rule and helper:

```sh
sudo visudo -c -f /etc/sudoers.d/fanctl
sudo -n /usr/local/sbin/fan-node-helper check
```

The last command should report that the node helper is ready. It does not
change fan settings.

### Step 4: Install the `fanctl` command

Still in `ssh-based/`, copy the Python CLI into your own `bin` directory:

```sh
mkdir -p "$HOME/bin"
install -m 0755 fanctl.py "$HOME/bin/fanctl"
```

Make that directory available in your current terminal:

```sh
export PATH="$HOME/bin:$PATH"
```

To make this permanent for Bash, add the same `export PATH=...` line to your
`~/.bashrc` and start a new shell. Check the installed command with:

```sh
fanctl --help
```

### Step 5: Check direct Ethernet SSH between the nodes

The CLI uses the SSH aliases `coffeepot1-etn` and `coffeepot3-etn`. From cp1,
check the connection to cp3:

```sh
ssh -o BatchMode=yes coffeepot3-etn true
```

From cp3, check the connection to cp1:

```sh
ssh -o BatchMode=yes coffeepot1-etn true
```

Each command should exit successfully without asking for a password. If an
alias is missing, configure it in that node's `~/.ssh/config` using the other
node's **direct Ethernet IP address**. For example, on cp1:

```text
Host coffeepot3-etn
    HostName <cp3-direct-Ethernet-IP>
    User <your-username-on-cp3>
```

On cp3, use `Host coffeepot1-etn` and cp1's direct Ethernet IP instead. You
need an SSH key accepted by the other node. If SSH asks for a password, stop
and fix key authentication before using `fanctl`.

### Step 6: Check the complete setup

After completing steps 1–5 on **both** nodes, run this from either node:

```sh
fanctl doctor
```

`doctor` checks access to the helper on cp1 and cp3. It does not change fan
settings. Both nodes should report `OK`. At that point setup is complete.

## 2. Using the commands

The general form is `fanctl COMMAND OPTIONS`. Run it from a terminal on cp1
or cp3. You do not put `sudo` before `fanctl`; it uses the approved helper.

Parameter meanings:

- `--node cp1` or `--node cp3`: select Coffeepot1 or Coffeepot3.
- `--zone 0` or `--zone 1`: select one of that node's two zones.
- `--percent N`: choose a whole-number speed from `0` to `100` percent.
- `--target NODE:ZONE=PERCENT`: combine those three values. For example,
  `cp1:0=50` means cp1, zone 0, at 50 percent.

### `set`: change one zone

The first command sets cp1 zone 0 to 50%. The second sets cp3 zone 1 to 75%:

```sh
fanctl set --node cp1 --zone 0 --percent 50
fanctl set --node cp3 --zone 1 --percent 75
```

### `apply`: change selected zones together

Repeat `--target` for every zone you want to set. This example sets cp1 zone
0 to 50% and cp3 zone 1 to 75%:

```sh
fanctl apply --target cp1:0=50 --target cp3:1=75
```

Each node/zone pair may appear only once in an `apply` command.

### `set-all`: change every zone on both nodes

Set cp1 zones 0 and 1 and cp3 zones 0 and 1 to the same percentage:

```sh
fanctl set-all --percent 50
```

Replace `50` with your chosen percentage from `0` through `100`.

### `killXthree`: set every zone to 50%

This is an alias for `fanctl set-all --percent 50`. It takes no parameters:

```sh
fanctl killXthree
```

### `doctor`: check connections without changing fans

This checks that the helper can be reached on both nodes:

```sh
fanctl doctor
```

### `--dry-run`: preview a command without changing fans

Place `--dry-run` **before** the command name. This example prints the planned
SSH and helper commands but does not contact either node:

```sh
fanctl --dry-run apply --target cp1:0=50 --target cp3:1=75
```

`--dry-run` also works with `set`, `set-all`, `killXthree`, and `doctor`.

Before an operation involving both nodes, `fanctl` checks that each requested
node is reachable. If a fan update fails after that check, it attempts to set
each requested zone on the affected node to 50% and reports the results. On
cp1, the helper converts the percentage to hexadecimal for `ipmitool`. On
cp3, it sends the percentage as a decimal number. Both helpers enable manual
fan control before setting a zone and leave manual mode enabled.
