import logging
import importlib
import os
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Log when application starts
@app.on_event("startup")
async def startup_event():
    logger.debug("Application startup complete")

@app.get("/")
def home():
    logger.debug("Home endpoint reached!")
    return {"message": "FastAPI is running with dynamic modules!"}

# PostgreSQL connection settings
DB_HOST = "34.88.110.91"  # Replace with your actual PostgreSQL IP
DB_NAME = "postgres"
DB_USER = "QuantCopilot"
DB_PASS = "Nov@21is"

# Dynamically load all modules in the "modules" folder
MODULES_DIR = "modules"

def register_modules(app):
    logger.debug("Calling register_modules() to load dynamic modules")
    if not os.path.exists(MODULES_DIR):
        logger.error(f"Modules directory '{MODULES_DIR}' not found!")
        return

    for module_file in os.listdir(MODULES_DIR):
        if module_file.endswith(".py") and module_file != "__init__.py":
            module_name = f"{MODULES_DIR}.{module_file[:-3]}"
            logger.debug(f"Attempting to load module: {module_name}")
            try:
                imported_module = importlib.import_module(module_name)

                if hasattr(imported_module, "register_routes"):
                    logger.debug(f"Registering routes from {module_name}")
                    imported_module.register_routes(app)
                else:
                    logger.debug(f"No register_routes function found in {module_name}")
            except Exception as e:
                logger.error(f"Failed to load module {module_name}: {e}")

    logger.debug("Finished registering modules")

# Dynamically register all available modules
register_modules(app)

# Ensure FastAPI explicitly includes routes from dynamically loaded modules
import modules.backtest
import modules.stock_query
import modules.gpt_strategy

modules.backtest.register_routes(app)
modules.stock_query.register_routes(app)
modules.gpt_strategy.register_routes(app)

# ✅ Ensure Uvicorn starts with Cloud Run-compatible settings
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))  # Ensure correct port assignment
    uvicorn.run(app, host="0.0.0.0", port=port)
