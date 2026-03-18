#!/usr/bin/env python
"""Test script to check if backend loads correctly."""
import sys
sys.path.insert(0, r"D:\AI-Agent-Education-Platform-cursor\backend")

try:
    from main import app
    print("Backend loaded successfully!")
    print(f"App title: {app.title}")
    print(f"Number of routes: {len(app.routes)}")
except Exception as e:
    print(f"Error loading backend: {e}")
    import traceback
    traceback.print_exc()
