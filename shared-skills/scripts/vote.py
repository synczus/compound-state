#!/usr/bin/env python3
"""
Compound Voting System v1.0 CLI.
Any agent can: propose | vote | tally | commit | show | archive

Usage:
    python3 vote.py propose <agent> <title> <description> [options...]
    python3 vote.py vote <agent> <vote_id> <option>
    python3 vote.py tally <vote_id>
    python3 vote.py commit <vote_id>
    python3 vote.py show [vote_id]
    python3 vote.py archive <vote_id>
"""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VOTE_FILE = Path("/home/synczus/kestrel/vote-board.json")
TODO_FILE = Path("/home/synczus/kestrel/master-todo.md")
EVENT_BUS = Path("/home/synczus/kestrel/event-bus.md")
ARCHIVE_DIR = Path("/home/synczus/kestrel/votes/archive")
ROSTER_FILE = Path("/home/synczus/kestrel/shared-skills/compound-roster.skill.md")

AGENTS = ["Hermes", "OpenClaw", "Kairos", "Shannon", "Nemoclaw"]
DEFAULT_WINDOW_MINUTES = 1440  # 24 hours


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_board() -> dict:
    if not VOTE_FILE.exists():
        return {"proposals": [], "archive_dir": str(ARCHIVE_DIR)}
    return json.loads(VOTE_FILE.read_text(encoding="utf-8"))


def save_board(board: dict):
    VOTE_FILE.write_text(json.dumps(board, indent=2), encoding="utf-8")


def next_vote_id(board: dict) -> str:
    existing = [p["vote_id"] for p in board["proposals"]]
    n = 1
    while f"vote-{n:03d}" in existing:
        n += 1
    return f"vote-{n:03d}"


def append_event_bus(entry: str):
    try:
        ts = now()
        line = f"[{ts}] | [VOTING] | {entry}\n"
        with EVENT_BUS.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def cmd_propose(args: list[str]):
    if len(args) < 4:
        print("Usage: vote.py propose <agent> <title> <description> [options...]")
        print("  Default options: yes, no, abstain")
        print("  Custom options: option1,option2,option3 (comma-separated after description)")
        sys.exit(1)

    agent = args[0]
    title = args[1]
    description = args[2]
    custom_opts = args[3].split(",") if len(args) > 3 and args[3] else ["yes", "no", "abstain"]

    if agent not in AGENTS:
        print(f"Unknown agent '{agent}'. Known: {AGENTS}")
        sys.exit(1)

    board = load_board()
    vid = next_vote_id(board)

    proposal = {
        "vote_id": vid,
        "title": title,
        "description": description,
        "options": custom_opts,
        "proposed_by": agent,
        "proposed_at": now(),
        "voting_window_minutes": DEFAULT_WINDOW_MINUTES,
        "deadline": "",
        "votes": {},
        "status": "open",
        "result": "",
        "winning_option": "",
    }
    # Calculate deadline
    from datetime import timedelta
    deadline = datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_WINDOW_MINUTES)
    proposal["deadline"] = deadline.isoformat()

    # Proposer auto-votes for their first option
    if custom_opts:
        proposal["votes"][agent] = custom_opts[0]

    board["proposals"].append(proposal)
    save_board(board)

    print(f"✅ Vote {vid} proposed by {agent}")
    print(f"   Title: {title}")
    print(f"   Options: {custom_opts}")
    print(f"   Deadline: {deadline.isoformat()}")
    print(f"   Auto-voted: {agent} → {custom_opts[0]}")
    append_event_bus(f"Vote {vid} opened by {agent}: \"{title}\" (options: {custom_opts})")

    # Show the next steps
    print(f"\n📢 Agents vote: python3 <path>/vote.py vote <your_name> {vid} <option>")
    print(f"   Tally:  python3 <path>/vote.py tally {vid}")
    print(f"   Commit: python3 <path>/vote.py commit {vid}")


def cmd_vote(args: list[str]):
    if len(args) < 3:
        print("Usage: vote.py vote <agent> <vote_id> <option>")
        sys.exit(1)

    agent = args[0]
    vid = args[1]
    option = args[2]

    if agent not in AGENTS:
        print(f"Unknown agent '{agent}'. Known: {AGENTS}")
        sys.exit(1)

    board = load_board()
    proposal = next((p for p in board["proposals"] if p["vote_id"] == vid), None)
    if not proposal:
        print(f"Vote {vid} not found")
        sys.exit(1)

    if proposal["status"] != "open":
        print(f"Vote {vid} is {proposal['status']} — not accepting votes")
        sys.exit(1)

    if option not in proposal["options"]:
        print(f"Invalid option '{option}'. Valid options: {proposal['options']}")
        sys.exit(1)

    # Check deadline
    if proposal.get("deadline"):
        from datetime import datetime
        try:
            dead = datetime.fromisoformat(proposal["deadline"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > dead:
                print(f"Vote {vid} deadline ({proposal['deadline']}) has passed")
                print("Run tally to close it")
                sys.exit(1)
        except Exception:
            pass

    old_vote = proposal["votes"].get(agent)
    proposal["votes"][agent] = option
    save_board(board)

    if old_vote:
        print(f"🔄 {agent} changed vote on {vid}: {old_vote} → {option}")
    else:
        print(f"🗳️  {agent} voted on {vid}: {option}")

    # Check if all voted — auto-tally
    voted = set(proposal["votes"].keys())
    remaining = set(AGENTS) - voted
    if not remaining:
        print(f"   All agents have voted! Run tally to close: vote.py tally {vid}")


def cmd_tally(args: list[str]):
    if len(args) < 1:
        print("Usage: vote.py tally <vote_id>")
        sys.exit(1)

    vid = args[0]
    board = load_board()
    proposal = next((p for p in board["proposals"] if p["vote_id"] == vid), None)
    if not proposal:
        print(f"Vote {vid} not found")
        sys.exit(1)

    if proposal["status"] != "open":
        print(f"Vote {vid} is already {proposal['status']}")
        return

    votes = proposal["votes"]
    options = [o for o in proposal["options"] if o != "abstain"]
    total_votes = len(votes)
    non_abstain = {a: v for a, v in votes.items() if v != "abstain"}
    agents_voted = len(non_abstain)
    quorum = agents_voted >= 3

    # Find winner
    from collections import Counter
    counts = Counter(non_abstain.values())
    if not counts:
        print("No non-abstain votes cast. Proposal fails.")
        proposal["status"] = "failed"
        proposal["result"] = f"0 votes cast — no quorum"
        save_board(board)
        return

    winner = counts.most_common(1)[0]
    winner_option = winner[0]
    winner_count = winner[1]

    # Check tie
    top_two = counts.most_common(2)
    tied = len(top_two) > 1 and top_two[0][1] == top_two[1][1]

    if not quorum:
        proposal["status"] = "failed"
        proposal["result"] = f"Quorum not met: {agents_voted}/3 voted (excluding abstentions)"
        print(f"❌ Vote {vid} FAILED — Quorum not met ({agents_voted}/3)")
    elif tied:
        proposal["status"] = "failed"
        proposal["result"] = f"Tie: {top_two[0][0]}={top_two[0][1]} vs {top_two[1][0]}={top_two[1][1]}"
        print(f"❌ Vote {vid} FAILED — Tie: {top_two[0][0]}={top_two[0][1]}, {top_two[1][0]}={top_two[1][1]}")
    elif agents_voted < 3:
        proposal["status"] = "failed"
        proposal["result"] = f"Only {agents_voted} agents voted (excluding abstentions). Need 3."
        print(f"❌ Vote {vid} FAILED — Only {agents_voted}/{3} agents voted")
    elif winner_count > agents_voted / 2:
        proposal["status"] = "passed"
        proposal["result"] = f"{winner_option} ({winner_count}/{agents_voted})"
        proposal["winning_option"] = winner_option
        print(f"✅ Vote {vid} PASSED — {winner_option} ({winner_count}/{agents_voted})")
    else:
        proposal["status"] = "failed"
        proposal["result"] = f"{winner_option} ({winner_count}/{agents_voted}) — majority not reached"
        print(f"❌ Vote {vid} FAILED — {winner_option} only {winner_count}/{agents_voted}")

    # Print breakdown
    print(f"\n   Breakdown:")
    for opt in proposal["options"]:
        count = counts.get(opt, 0)
        voters = [a for a, v in non_abstain.items() if v == opt]
        label = f"  {opt}: {count} vote(s)"
        if voters:
            label += f" ({', '.join(voters)})"
        print(label)
    if total_votes - agents_voted > 0:
        abstainers = [a for a, v in votes.items() if v == "abstain"]
        print(f"  abstain: {len(abstainers)} ({', '.join(abstainers)})")

    save_board(board)
    append_event_bus(f"Vote {vid} \"{proposal['title']}\" → {proposal['status'].upper()} ({proposal['result']})")


def cmd_commit(args: list[str]):
    if len(args) < 1:
        print("Usage: vote.py commit <vote_id>")
        sys.exit(1)

    vid = args[0]
    board = load_board()
    proposal = next((p for p in board["proposals"] if p["vote_id"] == vid), None)
    if not proposal:
        print(f"Vote {vid} not found")
        sys.exit(1)

    if proposal["status"] != "passed":
        print(f"Vote {vid} is {proposal['status']} — only 'passed' votes can be committed")
        sys.exit(1)

    # Write to master-todo.md completed section
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    entry = f"- [x] {ts} | {proposal['proposed_by']} | Vote {vid}: {proposal['title']} — {proposal['result']}"
    try:
        with TODO_FILE.open("a", encoding="utf-8") as f:
            f.write(f"\n{entry}\n")
    except Exception:
        pass

    # Write to event-bus
    append_event_bus(f"Vote {vid} COMMITTED: \"{proposal['title']}\" — {proposal['result']}")

    proposal["status"] = "committed"
    save_board(board)
    print(f"✅ Vote {vid} committed to master-todo.md + event-bus.md")
    print(f"   Decision: {proposal['title']} → {proposal['winning_option']}")


def cmd_show(args: list[str]):
    board = load_board()
    proposals = board["proposals"]

    if args:
        vid = args[0]
        proposal = next((p for p in proposals if p["vote_id"] == vid), None)
        if not proposal:
            print(f"Vote {vid} not found")
            sys.exit(1)
        proposals = [proposal]

    if not proposals:
        print("No votes found on the board")
        return

    for p in proposals:
        status_color = {
            "open": "🟢",
            "passed": "✅",
            "failed": "❌",
            "committed": "📌",
        }.get(p["status"], "⚪")

        print(f"\n{status_color} {p['vote_id']}: {p['title']}")
        print(f"   By: {p['proposed_by']} | Status: {p['status']} | Options: {p['options']}")
        print(f"   Description: {p['description'][:120]}...")
        if p.get("deadline"):
            print(f"   Deadline: {p['deadline']}")
        if p.get("result"):
            print(f"   Result: {p['result']}")
        votes = p.get("votes", {})
        if votes:
            print(f"   Votes: {json.dumps(votes)}")
        else:
            print("   Votes: none yet")


def cmd_archive(args: list[str]):
    if len(args) < 1:
        print("Usage: vote.py archive <vote_id>")
        sys.exit(1)

    vid = args[0]
    board = load_board()
    proposal = next((p for p in board["proposals"] if p["vote_id"] == vid), None)
    if not proposal:
        print(f"Vote {vid} not found")
        sys.exit(1)

    if proposal["status"] not in ("passed", "failed", "committed"):
        print(f"Vote {vid} is {proposal['status']} — only closed votes can be archived")
        sys.exit(1)

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / f"{vid}.json"
    archive_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")

    board["proposals"] = [p for p in board["proposals"] if p["vote_id"] != vid]
    save_board(board)
    print(f"📦 Vote {vid} archived to {archive_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: vote.py <command> [args...]")
        print("Commands: propose | vote | tally | commit | show | archive")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "propose": cmd_propose,
        "vote": cmd_vote,
        "tally": cmd_tally,
        "commit": cmd_commit,
        "show": cmd_show,
        "archive": cmd_archive,
    }

    if cmd not in commands:
        print(f"Unknown command '{cmd}'")
        print(f"Commands: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[cmd](args)


if __name__ == "__main__":
    main()