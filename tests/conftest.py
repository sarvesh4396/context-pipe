"""Pytest configuration for context-pipe tests."""

import sys
from pathlib import Path

# Add workspace package source directories to path for easier imports
workspace_root = Path(__file__).parent.parent
for package_dir in (workspace_root / "packages").glob("*/src"):
    sys.path.insert(0, str(package_dir))
