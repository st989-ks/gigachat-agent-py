#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
from mcp_server import main_start

if __name__ == "__main__":
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", requirements_file],
        capture_output=True,
        text=True,
        timeout=300
    )
    main_start()
