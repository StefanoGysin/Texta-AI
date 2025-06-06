from pathlib import Path
import sys

# Adicionar o diretório raiz do projeto ao PYTHONPATH
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))
