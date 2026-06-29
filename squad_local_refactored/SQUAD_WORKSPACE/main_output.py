import uvicorn
import app
import os

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get('PORT', 8001)), reload=True)