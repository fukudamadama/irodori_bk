#!/usr/bin/env python3
"""
Azure App Service startup script for FastAPI application
"""
import os
import uvicorn

if __name__ == "__main__":
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