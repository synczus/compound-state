import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional

# Initialize logger per Kestrel standards
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ToolResponse:
    """Standard return for any tool execution."""
    success: bool
    output: str
    error: Optional[str] = None


class SafeShell:
    """
    Sovereign Shell Wrapper.
    Ensures audit trails and prevents destructive system calls.
    """
    BLOCKED_PATTERNS = [
        "format ", "mkfs", "dd if=", "reboot", "shutdown",
        "poweroff", "init 0", "init 6", "halt"
    ]

    @staticmethod
    async def execute(cmd: str) -> ToolResponse:
        """Executes a shell command asynchronously with safety checks."""
        # General safety check: block common high-risk keywords
        for pattern in SafeShell.BLOCKED_PATTERNS:
            if pattern in cmd.lower():
                logger.error("DANGER: High-risk command detected: %s", cmd)
                return ToolResponse(False, "", "Command blocked for security reasons.")

        logger.info("Executing MCP command: %s", cmd)

        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return ToolResponse(True, stdout.decode().strip())
            else:
                return ToolResponse(False, stdout.decode().strip(), stderr.decode().strip())
        except Exception as e:
            logger.exception("Shell execution error: %s", e)
            return ToolResponse(False, "", str(e))


class MCPTools:
    """
    MCP (Model Context Protocol) Toolset.
    The 'Hands' for the gemma-4-31b-heavy agent.
    """

    @staticmethod
    async def write_file(path: str, content: str) -> ToolResponse:
        """Sovereign file write."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("MCP: Wrote file to %s", path)
            return ToolResponse(True, f"Successfully wrote to {path}")
        except Exception as e:
            logger.exception("MCP write_file error: %s", e)
            return ToolResponse(False, "", str(e))

    @staticmethod
    async def read_file(path: str) -> ToolResponse:
        """Sovereign file read."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info("MCP: Read file %s", path)
            return ToolResponse(True, content)
        except Exception as e:
            logger.exception("MCP read_file error: %s", e)
            return ToolResponse(False, "", str(e))

    @staticmethod
    async def execute_command(cmd: str) -> ToolResponse:
        """Execute a shell command via the SafeShell wrapper."""
        return await SafeShell.execute(cmd)

    @staticmethod
    async def git_commit_push(message: str, branch: str = "main") -> ToolResponse:
        """Automated git flow for the swarm's progress."""
        commands = [
            "git add .",
            f"git commit -m '{message}'",
            f"git push origin {branch}"
        ]
        for cmd in commands:
            res = await SafeShell.execute(cmd)
            if not res.success:
                logger.error("Git failure at %s: %s", cmd, res.error)
                return ToolResponse(False, "", f"Git failure: {res.error}")
        return ToolResponse(True, "Committed and pushed successfully.")