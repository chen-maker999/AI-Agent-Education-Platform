#!/usr/bin/env python
"""Check route paths from main.py to see the actual route patterns."""
import sys
import os

sys.path.insert(0, r"D:\AI-Agent-Education-Platform-cursor\backend")
os.environ.setdefault("PYTHONPATH", r"D:\AI-Agent-Education-Platform-cursor\backend")

from main import app

# Get routes and their actual paths
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        path = route.path
        methods = list(route.methods) if route.methods else ['GET']
        for method in methods:
            # Only print routes that contain 'knowledge' or 'intelligence' or 'visual'
            if 'knowledge' in path or 'intelligence' in path or 'visual' in path or 'chat' in path:
                print(f"{method} {path}")
