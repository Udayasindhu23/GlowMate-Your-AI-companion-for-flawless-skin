#!/usr/bin/env python
"""
Quick start script for SmartSkin application
"""
import os
import sys
import warnings
import logging

# Suppress Flask development server warnings
logging.getLogger('werkzeug').setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module='werkzeug')
os.environ['FLASK_ENV'] = 'development'
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

# Check Python version
if sys.version_info < (3, 8):
    print("Error: Python 3.8 or higher is required")
    sys.exit(1)

# Check if dependencies are installed
try:
    import flask
    import cv2
    import numpy
    import sklearn
except ImportError as e:
    print(f"Error: Missing dependency - {e}")
    print("Please install dependencies using: pip install -r requirements.txt")
    sys.exit(1)

# Run the application
if __name__ == '__main__':
    from app import app, init_db
    
    print("=" * 50)
    print("SmartSkin - AI Skincare Assistant")
    print("=" * 50)
    print("\nInitializing database...")
    init_db()
    print("Database initialized!")
    print("\nStarting server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    # Suppress werkzeug warnings by redirecting stderr
    old_stderr = sys.stderr
    from io import StringIO
    sys.stderr = StringIO()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    finally:
        sys.stderr = old_stderr

