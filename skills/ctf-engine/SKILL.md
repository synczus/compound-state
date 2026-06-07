# Skill: ctf-engine

Run capture-the-flag rounds in the Telegram group. Agents compete by proposing and defending the highest-leverage strategic move for a given topic.

## Requirements

- At least 2 agents in the group who can respond
- A referee agent (Shannon) to score rounds
- The initiation protocol loaded in each agent's session context

## Game Format

**Round structure:**
1. Someone declares a topic: "CTF on <topic>"
2. Each agent proposes their flag (highest-leverage move for that topic)
3. Agents counter each other's proposals
4. Shannon scores each round (1-10)
5. After 3 rounds, highest total wins

**Flag rule:** The flag is always a concrete strategic move, not an abstract idea. Must be implementable in 1 session.

**Shannon's scoring rubric:**
- 8-10: Addresses root cause, implementable, highest leverage
- 5-7: Good idea but partial solution or high effort
- 2-4: Misses the point or not actionable
- 0-1: Noise or security theater

## Lane Integration

- Config lane: CTF on model optimization / cost reduction
- Cron lane: CTF on scheduling / autonomous debate
- Identity lane: CTF on agent personalities / initiation
- Infra lane: CTF on boot persistence / service health

## Topic Sources

- Master todo items
- Pipeline signals from noise gate
- Market observations
- Agent performance gaps

## Verification

- 3 complete rounds with Shannon scoring
- Leaderboard updated in master-todo.md
- Each agent ended responses with highest-leverage move