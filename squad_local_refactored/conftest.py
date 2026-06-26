import sys
from pathlib import Path

# Add squad_local_refactored root directory to sys.path so pytest can resolve 'src'
sys.path.insert(0, str(Path(__file__).resolve().parent))
