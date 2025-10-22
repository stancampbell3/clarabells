# Ensure repo root is on sys.path so `app` package can be imported from tests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

