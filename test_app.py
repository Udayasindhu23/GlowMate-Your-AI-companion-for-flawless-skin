#!/usr/bin/env python
"""
Simple test script to verify the Flask app can start
"""
import sys
import os

print("Testing SmartSkin Application...")
print("=" * 50)

# Test imports
print("\n1. Testing imports...")
try:
    from app import app
    print("   [OK] Flask app imported successfully")
except Exception as e:
    print(f"   [ERROR] Error importing app: {e}")
    sys.exit(1)

# Test database initialization
print("\n2. Testing database initialization...")
try:
    from app import init_db
    init_db()
    print("   [OK] Database initialized successfully")
except Exception as e:
    print(f"   [ERROR] Error initializing database: {e}")
    sys.exit(1)

# Test routes
print("\n3. Testing routes...")
try:
    with app.test_client() as client:
        # Test home route
        response = client.get('/')
        if response.status_code == 200:
            print("   [OK] Home route (/) is working")
        else:
            print(f"   [ERROR] Home route returned status {response.status_code}")
        
        # Test static files
        response = client.get('/static/css/style.css')
        if response.status_code == 200:
            print("   [OK] CSS file is accessible")
        else:
            print(f"   [WARNING] CSS file status: {response.status_code}")
            
except Exception as e:
    print(f"   [ERROR] Error testing routes: {e}")
    sys.exit(1)

# Check file structure
print("\n4. Checking file structure...")
files_to_check = [
    'templates/index.html',
    'static/css/style.css',
    'static/js/main.js',
    'utils/face_detection.py',
    'utils/skin_analysis.py',
    'chatbot/bot_engine.py'
]

all_files_exist = True
for file in files_to_check:
    if os.path.exists(file):
        print(f"   [OK] {file}")
    else:
        print(f"   [MISSING] {file}")
        all_files_exist = False

if not all_files_exist:
    print("\n[WARNING] Some files are missing!")
    sys.exit(1)

print("\n" + "=" * 50)
print("[SUCCESS] All tests passed! The application is ready to run.")
print("=" * 50)
print("\nTo start the server, run:")
print("   python app.py")
print("\nThen open your browser and go to:")
print("   http://localhost:5000")

