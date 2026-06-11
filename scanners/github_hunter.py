import asyncio
import logging
import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional

# Governance Strict
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("kestrel.github_hunter")

from swarm.noise_gate import NoiseGate, RawInput
from swarm.hub import HubController
from scanners.state_manager import StateManager

@dataclass(slots=True)
class RepoTarget:
    owner: str
    repo: str
    description: str

class GitHubHunter:
    """
    Active Hunter: Monitors GitHub commits for structural shifts.
    Taps into the delta between 'code reality' and 'market consensus'.
    """
    def __init__(self, targets: List[RepoTarget]):
        self.targets = targets
        self.base_url = "https://api.github.com/repos"
        self.state = StateManager()

    async def fetch_commits(self, target: RepoTarget) -> List[RawInput]:
        logger.info(f"Hunting commits for {target.owner}/{target.repo}...")
        
        # Check state to avoid redundant processing
        last_sha = self.state.get_last_sha(target.repo)
        
        import subprocess, tempfile, os
        # Capture rate limit headers for telemetry (SPRINT requirement)
        rate_info = {}
        headers_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.headers') as hf:
                headers_file = hf.name
            cmd = [
                "curl", "-sL", "-D", headers_file,
                f"{self.base_url}/{target.owner}/{target.repo}/commits?per_page=10"
            ]
            process = subprocess.run(cmd, capture_output=True, text=True, check=True)
            body = process.stdout

            # Parse rate limit headers
            if os.path.exists(headers_file):
                with open(headers_file) as f:
                    for line in f:
                        line = line.strip().lower()
                        if line.startswith('x-ratelimit-'):
                            try:
                                k, v = line.split(':', 1)
                                rate_info[k.strip()] = v.strip()
                            except:
                                pass
                os.unlink(headers_file)
            if rate_info:
                logger.info(f"GitHub rate for {target.repo}: remaining={rate_info.get('x-ratelimit-remaining', '?')} limit={rate_info.get('x-ratelimit-limit', '?')}")

            commits = json.loads(body)
            
            if not isinstance(commits, list):
                logger.error(f"GitHub API error for {target.repo}: {commits}")
                return []

            signals = []
            for commit in commits:
                sha = commit['sha']
                if sha == last_sha:
                    logger.info(f"Reached last seen commit for {target.repo}. Stopping.")
                    break
                
                msg = commit['commit']['message']
                author = commit['commit']['author']['name']
                date_str = commit['commit']['author']['date']
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                
                signals.append(RawInput(
                    content=f"Commit {sha[:7]} by {author}: {msg}",
                    source=f"GitHub_{target.repo}",
                    timestamp=datetime.now(timezone.utc),  # discovery time, not author time
                    metadata={"sha": sha, "authored_at": dt.isoformat(), "rate_remaining": rate_info.get('x-ratelimit-remaining')}
                ))
            
            # Update state with the most recent SHA seen
            if commits:
                self.state.update_sha(target.repo, commits[0]['sha'])
                
            return signals
        except Exception as e:
            if headers_file and os.path.exists(headers_file):
                try: os.unlink(headers_file)
                except: pass
            logger.error(f"GitHub hunt failed for {target.repo}: {e}")
            return []

# High-signal multi-repo targets
# Note: "autogpt/AutoGPT" removed (404s); use the canonical Significant-Gravitas one.
DEFAULT_TARGETS = [
    RepoTarget("ggerganov", "llama.cpp", "Local LLM inference shifts"),
    RepoTarget("nomic-ai", "gpt4all", "Local LLM ecosystem"),
    RepoTarget("ollama", "ollama", "Local LLM orchestration"),
    RepoTarget("Significant-Gravitas", "AutoGPT", "Autonomous agent shifts (canonical)"),
    RepoTarget("comfyanonymous", "ComfyUI", "Local image gen infrastructure"),
    RepoTarget("langchain-ai", "langchain", "LLM orchestration framework"),
    RepoTarget("microsoft", "vscode", "Dev tool ecosystem shifts"),
    RepoTarget("openai", "openai-python", "API ecosystem changes"),
    RepoTarget("unslothai", "unsloth", "Fine-tuning optimization"),
]

async def run_real_pipeline(targets: Optional[List[RepoTarget]] = None):
    if targets is None:
        targets = DEFAULT_TARGETS
    
    hunter = GitHubHunter(targets)
    hub = HubController()
    total_signals = 0
    
    for target in targets:
        real_signals = await hunter.fetch_commits(target)
        total_signals += len(real_signals)
        
        for signal in real_signals:
            logger.info(f"Processing real signal: {signal.content[:60]}...")
            result = await hub.process_signal(signal)
            if result:
                logger.info(f"SUCCESS: Real alpha extracted from {target.repo}!")
            else:
                logger.info(f"PURGED: Commit noise rejected.")
    
    logger.info(f"Hunt complete: {total_signals} new signals from {len(targets)} repos.")
    return total_signals

async def run_single_hunt(repo_owner: str, repo_name: str, description: str = ""):
    """Single-shot hunt for a specific repo, used by poller."""
    target = RepoTarget(repo_owner, repo_name, description)
    hunter = GitHubHunter([target])
    hub = HubController()
    
    signals = await hunter.fetch_commits(target)
    for signal in signals:
        logger.info(f"Signal from {repo_owner}/{repo_name}: {signal.content[:60]}...")
        result = await hub.process_signal(signal)
    
    return signals

if __name__ == "__main__":
    asyncio.run(run_real_pipeline())
