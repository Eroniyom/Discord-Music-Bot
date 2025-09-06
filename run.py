#!/usr/bin/env python3
"""
Discord Music Bot Launcher
Run this file to start the music bot
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from music_bot import main
    main()
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please install the required dependencies:")
    print("pip install -r requirements.txt")
except KeyboardInterrupt:
    print("\n👋 Bot stopped by user")
except Exception as e:
    print(f"❌ Error starting bot: {e}")
    print("Please check your configuration and try again")
