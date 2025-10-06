# Launcher shim to run the package entrypoint
# Ensures project root is on sys.path so absolute imports work (mina_al_arabi.*)
import sys, os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mina_al_arabi.main import main

if __name__ == "__main__":
    main()