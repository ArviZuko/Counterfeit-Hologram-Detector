#!/usr/bin/env python3
"""
Launcher alias for raspberry.py
Enables direct execution via 'python rapberry.py' or 'python raspberry.py'.
"""
import sys
import os

# Delegate directly to raspberry.py main
from raspberry import main

if __name__ == '__main__':
    main()
