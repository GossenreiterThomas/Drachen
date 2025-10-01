import importlib
from pathlib import Path

async def setup(bot):
    # Get the directory this file is in (cogs/economy)
    package_dir = Path(__file__).parent

    # Loop through all python files in this folder (except __init__.py and utils/db files)
    for file in package_dir.glob("*.py"):
        if file.stem in ["__init__", "database", "utils"]:
            continue

        module_name = f"{__package__}.{file.stem}"  # e.g. cogs.economy.balance_cog
        module = importlib.import_module(module_name)

        if hasattr(module, "setup"):
            await module.setup(bot)
