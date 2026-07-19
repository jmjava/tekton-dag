"""Ensure backend and tekton-dag-common are importable when pytest cwd is backend/."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
COMMON_ROOT = BACKEND_ROOT.parent.parent / "libs" / "tekton-dag-common"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if COMMON_ROOT.is_dir() and str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))
