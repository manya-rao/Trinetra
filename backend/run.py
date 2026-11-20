"""
Trinetra Backend Server Runner
Usage: python run.py
"""

import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    print(f"Starting Trinetra Backend on http://{HOST}:{PORT}")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
