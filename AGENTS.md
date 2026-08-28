# Insruction for agents to access Coffeepot1 (cp1) and Coffeepot2 (cp2)

## SSH commands
- For Coffeepot1: `ssh coffeepot1`

- For Coffeepot2: `ssh coffeepot2`

- Notes: ssh should be key-based, since user had set it up. If the ssh commands request for passwords, that means the key-based method is failing. Stop and inform the user.

## General rules
- Agents are allowed flexibility to execute commands to solve problems as per request. However, they must strictly honour 1 rule: for any commands that requires `sudo`, the agents must inform user of the situtation, and give user the command so that the user can execute that command manually.

