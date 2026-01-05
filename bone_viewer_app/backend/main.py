import uvicorn
import logging

if __name__ == "__main__":
    # Redirect to the new Clean Architecture structure
    print("Starting Bone Viewer Backend (Clean Architecture)...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8001, reload=True)
