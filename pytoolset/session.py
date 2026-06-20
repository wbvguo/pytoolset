from __future__ import annotations

import platform
import sys


def sessionInfo() -> None:
    """Print Python/platform details and versions of loaded top-level packages."""
    print("Python version:", sys.version)
    print("Platform:", platform.platform())
    print("Implementation:", platform.python_implementation())
    print("Architecture:", platform.architecture()[0])
    print("\nLoaded packages:")

    # Filter for top-level modules with a __version__ attribute
    loaded_packages = {
        name: module
        for name, module in sys.modules.items()
        if module and hasattr(module, "__version__") and "." not in name
    }

    for name, module in sorted(loaded_packages.items()):
        print(f"{name}=={module.__version__}")


if __name__ == "__main__":
    sessionInfo()
