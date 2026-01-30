import subprocess
import time
import sys
import os

def run():
    # 1. Start backend
    print("🚀 Starting Backend API...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=os.getcwd()
    )
    
    # Wait for backend to be ready
    time.sleep(5)
    
    # 2. Start frontend
    print("🎨 Starting Frontend Dashboard...")
    # Check if dashboard/node_modules exists, if not install (safety)
    if not os.path.exists("dashboard/node_modules"):
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd="dashboard")
        
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="dashboard",
        shell=True
    )
    
    print("\n✅ SYSTEM IS RUNNING")
    print("   Backend: http://localhost:8000")
    print("   Frontend: http://localhost:5173")
    print("\nPress Ctrl+C to stop both.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    run()
