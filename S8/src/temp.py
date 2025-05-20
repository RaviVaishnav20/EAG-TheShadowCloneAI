from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent.parent.resolve()  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

server_file = ROOT / "src" / "server" / "example.py"