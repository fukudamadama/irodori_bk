"""
Azure App Service startup script for FastAPI application
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

logger.info(f"Current directory: {current_dir}")
logger.info(f"Python path: {sys.path}")

try:
    # Import FastAPI app
    from main import app
    logger.info("Successfully imported FastAPI app")
    
    # Azure App Service sets PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting uvicorn on {host}:{port}")
    
    import uvicorn
    uvicorn.run(
        app,  # Use app object directly instead of string
        host=host,
        port=port,
        log_level="info"
    )
    
except Exception as e:
    logger.error(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)