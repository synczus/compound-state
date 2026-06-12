#!/usr/bin/env python3
"""tally-polls.py — Check all active polls, count votes, close finished ones.
Run this on any agent's cron cycle to process compound voting.
Usage: python3 /home/synczus/kestrel/baton/polls/tally-polls.py
"""
import json, time, os, shutil
from pathlib import Path

POLLS = Path("/home/synczus/kestrel/baton/polls")
ACTIVE = POLLS / "active"
ARCHIVED = POLLS / "archived"
MASTER = POLLS / "master-poll.json"
EVENT_BUS = Path("/home/synczus/kestrel/event-bus.md")
TODO = Path("/home/synczus/kestrel/master-todo.md")

AGENTS = ["hermes", "nemoclaw", "openclaw", "kairos", "shannon"]

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M")
    line = f"| {ts} | Poll Tally | {msg} |"
    print(line)
    if EVENT_BUS.exists():
        with open(EVENT_BUS, "a") as f:
            f.write("\n" + line)

def tally_poll(poll):
    """Count votes for a single poll. Returns (winner_id, vote_counts, total_votes)."""
    votes = {opt["id"]: len(opt["votes"]) for opt in poll["options"]}
    # Also count voter slots
    voter_votes = {}
    for agent in AGENTS:
        vote = poll["voters"].get(agent)
        if vote and vote in votes:
            voter_votes[vote] = voter_votes.get(vote, 0) + 1

    # Merge both counting methods (prefer voter slots)
    total = sum(voter_votes.values())
    if total == 0:
        # Check votes arrays
        total = sum(votes.values())
        voter_votes = votes
    else:
        votes = voter_votes

    if not votes:
        return None, votes, 0

    winner = max(votes, key=votes.get)
    return winner, votes, total

def process_polls():
    master = json.loads(MASTER.read_text()) if MASTER.exists() else {"current_poll_id": None, "poll_history": []}
    
    for poll_file in sorted(ACTIVE.glob("*.json")):
        poll = json.loads(poll_file.read_text())
        if poll["status"] != "open":
            continue

        now = time.time()
        closes_at = None
        try:
            closes_at = time.mktime(time.strptime(poll["closes_at"].replace("-04:00", ""), "%Y-%m-%dT%H:%M:%S"))
            # HACK: adjust for timezone offset
            closes_at += 4 * 3600
        except:
            closes_at = now + 1800  # default 30 min from creation

        # Check timed closure
        time_up = now >= closes_at
        
        # Count votes
        winner, vote_counts, total_votes = tally_poll(poll)
        
        # Count quorum
        voted = sum(1 for a in AGENTS if poll["voters"].get(a) is not None)
        
        print(f"  Poll: {poll['poll_id']} — {poll['question']}")
        print(f"    Votes: {vote_counts} | Voted: {voted}/5 | Time up: {time_up}")
        
        should_close = time_up or (voted >= 3)
        
        if should_close and total_votes > 0:
            # Check for tie
            max_votes = max(vote_counts.values())
            winners = [k for k, v in vote_counts.items() if v == max_votes]
            
            if len(winners) > 1:
                poll["status"] = "tied"
                label = "TIED"
            else:
                poll["status"] = "passed"
                poll["winner"] = winners[0]
                label = f"WINNER: {winners[0]} ({max_votes} votes)"
            
            print(f"    -> {label}")
            log(f"Poll '{poll['question']}' {poll['status']}: {label}")
        elif should_close and total_votes == 0:
            poll["status"] = "closed"
            poll["winner"] = "no_quorum"
            log(f"Poll '{poll['question']}' closed: no votes cast")

        # Write updated poll
        poll_file.write_text(json.dumps(poll, indent=2))
        
        # If passed, archive it and update master
        if poll["status"] in ("passed", "tied", "closed"):
            archive_path = ARCHIVED / poll_file.name
            poll_file.rename(archive_path)
            
            if poll["winner"] and poll["winner"] != "no_quorum":
                master["current_poll_id"] = None
                master["poll_history"].append({
                    "poll_id": poll["poll_id"],
                    "question": poll["question"],
                    "winner": poll["winner"],
                    "closed_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                })
                
                # Update master-todo.md with the winning item
                update_todo(poll)
            
            MASTER.write_text(json.dumps(master, indent=2))
            log(f"Poll {poll['poll_id']} archived")

def update_todo(poll):
    """Add winning poll item as P0 to master-todo.md if not already there."""
    label_map = {
        "striker_signals": "Pipeline | Wire Striker signals to Telegram | Assigned | P0 | Poll winner",
        "new_pipeline": "Pipeline | Build execution pipeline | Assigned | P0 | Poll winner",
        "boot_persistence": "Infra | Test and fix boot persistence | Assigned | P0 | Poll winner",
        "protocol_polish": "Protocol | Polish v4.0 protocol | Assigned | P0 | Poll winner",
    }
    entry = label_map.get(poll.get("winner"))
    if entry and TODO.exists():
        content = TODO.read_text()
        if entry not in content:
            # Find the P0 section and add
            new_entry = f"| {entry} |" + "\n"
            content = content + new_entry
            TODO.write_text(content)
            log(f"Todo updated: {entry}")
            poll["todo_updated"] = True

if __name__ == "__main__":
    process_polls()