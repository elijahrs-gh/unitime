import sys
import os
import subprocess
from pathlib import Path

ui_dir = Path(__file__).parent
sys.path.insert(0, str(ui_dir))

try:
    from main_window import main
    
    if __name__ == "__main__":
        print("Starting UniTime UI...")
        print("Make sure the tracking API is running on localhost:5000")
        print("You can start it by running: python track_api.py")
        print("-" * 50)
        
        main()

except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("\nMake sure you have installed the required dependencies:")
    print("pip install -r requirements.txt")
    print("\nRequired packages:")
    print("- PyQt6")
    print("- requests")
    sys.exit(1)

except Exception as e:
    print(f"Error starting UniTime UI: {e}")
    sys.exit(1)
