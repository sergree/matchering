"""
Test runner script for Matchering test suite
Provides convenient commands for running different test categories
"""

import sys
import subprocess
from pathlib import Path

def run_pytest(args=None, markers=None):
    """Run pytest with specified arguments and markers"""
    cmd = ["python", "-m", "pytest"]

    if args:
        cmd.extend(args)

    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])

    # Add common options
    cmd.extend([
        "--tb=short",
        "-v"
    ])

    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=Path(__file__).parent.parent)

def main():
    """Main test runner with different options"""
    if len(sys.argv) < 2:
        print("Matchering Test Runner")
        print("=" * 40)
        print("Usage: python test_runner.py <command>")
        print("")
        print("Commands:")
        print("  all          - Run all tests")
        print("  unit         - Run unit tests only")
        print("  integration  - Run integration tests only")
        print("  player       - Run player-related tests")
        print("  core         - Run core library tests")
        print("  dsp          - Run DSP functionality tests")
        print("  audio        - Run audio processing tests")
        print("  files        - Run file I/O tests")
        print("  error        - Run error handling tests")
        print("  performance  - Run performance tests")
        print("  fast         - Run fast tests (exclude slow)")
        print("  slow         - Run slow tests only")
        print("")
        print("Examples:")
        print("  python test_runner.py unit")
        print("  python test_runner.py player --verbose")
        print("  python test_runner.py fast -x")
        return 1

    command = sys.argv[1]
    extra_args = sys.argv[2:] if len(sys.argv) > 2 else []

    if command == "all":
        result = run_pytest(extra_args)
    elif command == "unit":
        result = run_pytest(extra_args, ["unit"])
    elif command == "integration":
        result = run_pytest(extra_args, ["integration"])
    elif command == "player":
        result = run_pytest(extra_args, ["player"])
    elif command == "core":
        result = run_pytest(extra_args, ["core"])
    elif command == "dsp":
        result = run_pytest(extra_args, ["dsp"])
    elif command == "audio":
        result = run_pytest(extra_args, ["audio"])
    elif command == "files":
        result = run_pytest(extra_args, ["files"])
    elif command == "error":
        result = run_pytest(extra_args, ["error"])
    elif command == "performance":
        result = run_pytest(extra_args, ["performance"])
    elif command == "fast":
        result = run_pytest(extra_args + ["-m", "not slow"])
    elif command == "slow":
        result = run_pytest(extra_args, ["slow"])
    else:
        print(f"Unknown command: {command}")
        return 1

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())