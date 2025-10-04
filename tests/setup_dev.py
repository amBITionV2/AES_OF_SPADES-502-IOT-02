#!/usr/bin/env python3
"""
UR Safe Stick - Development Setup Script
========================================

This script helps team members set up their development environment quickly.
Run this after cloning the repository.

Usage:
    python setup_dev.py [--test]
    
Options:
    --test    Run all module tests after setup
"""

import os
import sys
import subprocess
import platform

def run_command(cmd, description):
    """Run a command and handle errors gracefully"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Verify Python version is 3.9+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not supported")
        print("   UR Safe Stick requires Python 3.9 or higher")
        return False

def create_venv():
    """Create virtual environment if it doesn't exist"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command(
        f"{sys.executable} -m venv venv",
        "Creating virtual environment"
    )

def get_python_executable():
    """Get the path to Python executable in venv"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python")

def install_requirements():
    """Install project requirements"""
    python_exe = get_python_executable()
    return run_command(
        f'"{python_exe}" -m pip install -r requirements.txt',
        "Installing project dependencies"
    )

def run_tests():
    """Run all module tests"""
    python_exe = get_python_executable()
    tests = [
        ("ursafe_sdk/crypto_manager.py", "Cryptography tests"),
        ("ursafe_sdk/chunk_manager.py", "Secret sharing tests"),
    ]
    
    print("\n🧪 Running Tests")
    print("=" * 50)
    
    all_passed = True
    for test_file, description in tests:
        if os.path.exists(test_file):
            print(f"\n🔍 {description}:")
            success = run_command(
                f'"{python_exe}" {test_file}',
                f"Running {test_file}"
            )
            if not success:
                all_passed = False
        else:
            print(f"⚠️  {test_file} not found, skipping")
    
    return all_passed

def main():
    print("🚀 UR Safe Stick - Development Setup")
    print("=" * 40)
    
    # Check if we should run tests
    run_tests_flag = "--test" in sys.argv
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Create virtual environment
    if not create_venv():
        sys.exit(1)
    
    # Step 3: Install requirements
    if not install_requirements():
        sys.exit(1)
    
    print("\n✅ Development environment setup complete!")
    
    # Step 4: Run tests if requested
    if run_tests_flag:
        if run_tests():
            print("\n🎉 All tests passed! You're ready to develop.")
        else:
            print("\n⚠️  Some tests failed. Check the output above.")
            sys.exit(1)
    else:
        print("\n💡 To run tests, use: python setup_dev.py --test")
    
    # Step 5: Show next steps
    print("\n📝 Next Steps:")
    print("   1. Activate virtual environment:")
    if platform.system() == "Windows":
        print("      venv\\Scripts\\activate")
    else:
        print("      source venv/bin/activate")
    
    print("   2. Run individual tests:")
    print("      python ursafe_sdk/crypto_manager.py")
    print("      python ursafe_sdk/chunk_manager.py")
    
    print("   3. Start developing your assigned modules!")
    print("\n📚 See README.md for detailed development guide")

if __name__ == "__main__":
    main()