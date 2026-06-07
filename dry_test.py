from poller import BackgroundPoller
print("poller import ok")

from scanners.state_manager import StateManager
print("state manager import ok")

from scanners.github_hunter import DEFAULT_TARGETS
print(f"{len(DEFAULT_TARGETS)} targets loaded")

print("\n--- All dry imports passed ---")
