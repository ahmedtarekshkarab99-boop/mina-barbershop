# Launcher shim to run the package entrypoint
# Keeps absolute imports intact and avoids ModuleNotFoundError when invoking "python main.py"
from mina_al_arabi.main import main

if __name__ == "__main__":
    main()