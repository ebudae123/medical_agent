"""
Quick start script for Nightingale AI
Starts both backend and frontend servers
"""
import subprocess
import sys
import os
import time

def main():
    print("[START] Starting Nightingale AI Medical Assistant\n")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("Warning: No .env file found. Creating from .env.example...")
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("Success: Created .env file. Please edit it with your GOOGLE_API_KEY")
            print("   Get your API key from: https://aistudio.google.com/app/apikey\n")
            input("Press Enter after you've added your API key...")
        else:
            print("Error: .env.example not found!")
            return
    
    print("Starting servers...\n")
    
    # Start backend
    print("Backend: Starting backend server on http://localhost:8000")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    time.sleep(2)
    
    # Start frontend
    print("Frontend: Starting frontend server on http://localhost:3000")
    frontend_process = subprocess.Popen(
        [sys.executable, "serve_frontend.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print("\n" + "="*60)
    print("Success: Nightingale AI is running!")
    print("="*60)
    print("\nOpen your browser to: http://localhost:3000")
    print("API Documentation: http://localhost:8000/docs")
    print("\nTest Users:")
    print("   - Patient: Click 'Patient' button")
    print("   - Clinician: Click 'Clinician' button")
    print("\nPress Ctrl+C to stop all servers\n")
    
    try:
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n\nStopping servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("Goodbye!")

if __name__ == "__main__":
    main()
