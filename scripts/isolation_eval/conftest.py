import sys
from pathlib import Path

# Allow `from protocol import ...` whether pytest is started from repo root or this dir.
sys.path.insert(0, str(Path(__file__).resolve().parent))
