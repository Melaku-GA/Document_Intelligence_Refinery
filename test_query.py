#!/usr/bin/env python3
"""Test script for query agent"""
import sys

try:
    from src.agents.query_agent import RefineryQueryAgent
    
    agent = RefineryQueryAgent()
    result = agent.run('What was the headline inflation in March 2025?')
    
    print("=== ANSWER ===")
    print(result.get('answer', 'No answer')[:500])
    
    print("\n=== PROVENANCE ===")
    for p in result.get('provenance', [])[:2]:
        print(f"Page {p.get('page')}, bbox=({p.get('x0',0):.0f},{p.get('y0',0):.0f})-({p.get('x1',100):.0f},{p.get('y1',100):.0f})")

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
