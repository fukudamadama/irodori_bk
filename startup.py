"""
Azure App Service startup script for FastAPI application
Works with both Windows and Linux App Services
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    import uvicorn
    
    # Azure App Service sets PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    # Run with production settings
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # No reload in production
        workers=1      # Azure handles scaling
    )