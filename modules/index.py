import os
import importlib
from fastapi import FastAPI

def register_modules(app: FastAPI):
    MODULES_DIR = "modules"

    for module_file in os.listdir(MODULES_DIR):
        if module_file.endswith(".py") and module_file != "__init__.py" and module_file != "index.py":
            module_name = f"{MODULES_DIR}.{module_file[:-3]}"
            imported_module = importlib.import_module(module_name)

            if hasattr(imported_module, "router"):
                app.include_router(imported_module.router)
