#!/usr/bin/env python3
"""
Test script to verify autonomous setup works without dependencies

This simulates a fresh system where Python packages aren't installed
"""

import sys
import subprocess
import os

def test_scenario_1_no_dependencies():
    """Test: Run autonomous setup when dependencies are missing"""
    print("\n" + "="*70)
    print("TEST SCENARIO 1: Autonomous Setup WITHOUT Pre-installed Dependencies")
    print("="*70 + "\n")
    
    print("Simulating fresh environment by temporarily uninstalling packages...")
    
    # Uninstall test packages
    packages = ['rich', 'pyyaml']
    for pkg in packages:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'uninstall', '-y', pkg],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ Uninstalled {pkg}")
        else:
            print(f"  {pkg} was not installed")
    
    print("\n📋 Current state:")
    # Verify they're uninstalled
    for pkg in ['rich', 'yaml']:
        try:
            __import__(pkg)
            print(f"  ✗ {pkg} still available (unexpected)")
        except ImportError:
            print(f"  ✓ {pkg} NOT available (expected)")
    
    print("\n🚀 Now running autonomous_setup.py...")
    print("   This should automatically detect and install missing packages\n")
    print("-" * 70)
    
    # Run autonomous setup
    result = subprocess.run(
        [sys.executable, 'autonomous_setup.py'],
        capture_output=True,
        text=True,
        timeout=60,
        input='n\n',  # Answer 'no' to skip actual setup
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print("-" * 70)
    
    # Verify packages were installed
    print("\n📋 Post-run state:")
    all_installed = True
    for pkg in ['rich', 'yaml']:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg} is NOW available")
        except ImportError:
            print(f"  ✗ {pkg} is STILL missing")
            all_installed = False
    
    if all_installed:
        print("\n✅ SUCCESS: Autonomous setup detected and installed all dependencies!")
    else:
        print("\n❌ FAILED: Some dependencies were not installed automatically")
    
    return all_installed


def test_scenario_2_partial_dependencies():
    """Test: Only one dependency missing"""
    print("\n" + "="*70)
    print("TEST SCENARIO 2: Autonomous Setup WITH Partial Dependencies")
    print("="*70 + "\n")
    
    print("Uninstalling only 'rich' package...")
    subprocess.run(
        [sys.executable, '-m', 'pip', 'uninstall', '-y', 'rich'],
        capture_output=True
    )
    
    print("\n📋 Current state:")
    for pkg in ['rich', 'yaml']:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg} available")
        except ImportError:
            print(f"  ✗ {pkg} NOT available")
    
    print("\n🚀 Running autonomous_setup.py with partial dependencies...")
    print("-" * 70)
    
    result = subprocess.run(
        [sys.executable, 'autonomous_setup.py'],
        capture_output=True,
        text=True,
        timeout=60,
        input='n\n',
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print(result.stdout[:500])  # First 500 chars
    print("-" * 70)
    
    # Verify
    try:
        __import__('rich')
        print("\n✅ SUCCESS: Missing 'rich' package was installed!")
        return True
    except ImportError:
        print("\n❌ FAILED: 'rich' package was not installed")
        return False


def test_scenario_3_all_installed():
    """Test: All dependencies already installed"""
    print("\n" + "="*70)
    print("TEST SCENARIO 3: Autonomous Setup WITH All Dependencies")
    print("="*70 + "\n")
    
    # Ensure all are installed
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', 'rich', 'pyyaml'],
        capture_output=True
    )
    
    print("📋 Current state: All packages installed")
    for pkg in ['rich', 'yaml']:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg} available")
        except ImportError:
            print(f"  ✗ {pkg} NOT available")
    
    print("\n🚀 Running autonomous_setup.py with all dependencies...")
    print("   Should skip installation and proceed directly\n")
    print("-" * 70)
    
    result = subprocess.run(
        [sys.executable, 'autonomous_setup.py'],
        capture_output=True,
        text=True,
        timeout=60,
        input='n\n',
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print(result.stdout[:500])
    print("-" * 70)
    
    if "already installed" in result.stdout or "All required Python packages are installed" in result.stdout:
        print("\n✅ SUCCESS: Correctly detected all packages are installed!")
        return True
    else:
        print("\n⚠️  WARNING: Expected detection message not found")
        return False


def main():
    """Run all test scenarios"""
    print("\n" + "="*70)
    print("🧪 AUTONOMOUS SETUP DEPENDENCY TESTING")
    print("="*70)
    print("\nThis test suite verifies that autonomous_setup.py can:")
    print("  1. Detect missing Python dependencies")
    print("  2. Automatically install them")
    print("  3. Handle partial installations")
    print("  4. Skip installation when not needed")
    print("\nStarting tests...\n")
    
    results = {}
    
    try:
        # Test 1: No dependencies
        results['no_deps'] = test_scenario_1_no_dependencies()
        
        # Test 2: Partial dependencies
        results['partial_deps'] = test_scenario_2_partial_dependencies()
        
        # Test 3: All installed
        results['all_deps'] = test_scenario_3_all_installed()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:20s} : {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The autonomous setup is truly autonomous and handles dependencies!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Review the output above for details")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
