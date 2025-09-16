#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unified Test Runner for Auralis System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Runs all tests for the Auralis audio mastering system
"""

import sys
import subprocess
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file.name}")
    print('='*60)

    try:
        result = subprocess.run([sys.executable, str(test_file)],
                              capture_output=False,
                              check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {test_file.name}")
        return False
    except Exception as e:
        print(f"❌ Error running {test_file.name}: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Auralis System Test Suite")
    print("=" * 60)

    # Test directories
    test_dirs = [
        Path("tests/auralis"),
        Path("tests/matchering")
    ]

    all_passed = True
    test_results = []

    for test_dir in test_dirs:
        if not test_dir.exists():
            print(f"⚠️  Test directory not found: {test_dir}")
            continue

        print(f"\n🔍 Running tests in {test_dir}/")

        # Find all test files
        test_files = list(test_dir.glob("test_*.py"))

        if not test_files:
            print(f"⚠️  No test files found in {test_dir}")
            continue

        for test_file in sorted(test_files):
            result = run_test_file(test_file)
            test_results.append((test_file.name, result))
            if not result:
                all_passed = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<40} {status}")

    print("=" * 60)

    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✨ Auralis system is ready for production!")
        return 0
    else:
        print("⚠️  Some tests failed - please check the output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())