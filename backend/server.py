"""Server entrypoint for FastAPI application.
Starts uvicorn server without SSL for now.
"""

from backend.oldmodern import app
import uvicorn

if __name__ == "__main__":
    #SSL configuration commented out for now
    import os
    ssl_keyfile = os.path.join(os.path.dirname(__file__), 'ssl', 'key.pem')
    ssl_certfile = os.path.join(os.path.dirname(__file__), 'ssl', 'cert.pem')
    
    uvicorn.run(
        "modern:app",  # Use import string to enable reload
        host="0.0.0.0",
        port=8001,
        reload=True,workers=1
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )
