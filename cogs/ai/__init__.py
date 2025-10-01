# cogs/folder_name/__init__.py
import importlib
from pathlib import Path

async def setup(bot):
    """
    Automatically loads all cog files in this package/folder.
    Skips __init__.py and any files you list in SKIP_FILES.
    """
    SKIP_FILES = ["__init__", "utils", "database"]  # helper files to skip
    package_dir = Path(__file__).parent

    for file in package_dir.glob("*.py"):
        if file.stem in SKIP_FILES:
            continue

        module_name = f"{__package__}.{file.stem}"  # e.g. cogs.economy.balance_cog
        module = importlib.import_module(module_name)

        # if the module has a setup function, call it
        if hasattr(module, "setup"):
            await module.setup(bot)
