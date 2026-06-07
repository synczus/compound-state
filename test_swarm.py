"""Integration test: AutoHOP v2.2 Swarm with MCP Tool execution."""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
from swarm.hub import AutoHOPHub


async def test_swarm_mcp_execution():
    hub = AutoHOPHub()
    result = await hub.orchestrate({'id': 'test_mcp', 'input': 'Build a bot'})
    
    print('\n--- SWARM EXECUTION TRACE ---')
    for i, hop in enumerate(result['history'], 1):
        print(f'Hop {i}: {hop.model} -> {hop.next_hop} | Score: {hop.leverage_score} | {hop.reasoning}')
    
    print(f'\nFinal Status: {result["status"]}')
    
    # Verify the MCP output file was written to disk
    output_file = '/tmp/autohop_test_mcp_summary.txt'
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            content = f.read()
        print(f'\n--- MCP Output File ({output_file}) ---')
        print(f'{content[:500]}...' if len(content) > 500 else content)
        print('\nTEST PASSED: Swarm ran and MCP wrote output to disk.')
        return True
    else:
        print(f'\nTEST FAILED: MCP output file not found at {output_file}')
        return False


if __name__ == '__main__':
    success = asyncio.run(test_swarm_mcp_execution())
    sys.exit(0 if success else 1)