import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

if __name__ == "__main__":
    # Set development environment
    os.environ["ENV"] = "development"
    
    # Run the server with hot reload
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8080,
        reload=True,
        reload_dirs=[os.path.join(project_root, "app")]
    ) 