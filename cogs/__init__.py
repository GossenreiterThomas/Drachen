import importlib
from pathlib import Path

async def setup(bot):
    base_dir = Path(__file__).parent

    # Load all Python files in this folder except __init__.py
    for file in base_dir.glob("*.py"):
        if file.stem == "__init__":
            continue
        module_name = f"{__package__}.{file.stem}"
        module = importlib.import_module(module_name)
        if hasattr(module, "setup"):
            await module.setup(bot)

    # Load all subfolders that have __init__.py
    for folder in base_dir.iterdir():
        if folder.is_dir() and (folder / "__init__.py").exists():
            module_name = f"{__package__}.{folder.name}"
            module = importlib.import_module(module_name)
            if hasattr(module, "setup"):
                await module.setup(bot)
