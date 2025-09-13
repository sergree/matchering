#!/usr/bin/env python3
"""
Matchering Test Management Script
Provides make-like commands for running tests and generating reports
"""

import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return success status"""
    if description:
        print(f"\n🚀 {description}")
        print("=" * (len(description) + 4))

    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()

    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent)
        duration = time.time() - start_time
        print(f"✅ Completed in {duration:.1f}s")
        return True
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"❌ Failed after {duration:.1f}s (exit code: {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")

    deps = {
        "pytest": ["python", "-m", "pytest", "--version"],
        "soundfile": ["python", "-c", "import soundfile; print('soundfile available')"],
        "numpy": ["python", "-c", "import numpy; print(f'numpy {numpy.__version__}')"],
    }

    missing = []
    for name, cmd in deps.items():
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"  ✅ {name}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  ❌ {name}")
            missing.append(name)

    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install pytest soundfile numpy")
        return False

    return True

def main():
    """Main command dispatcher"""
    if len(sys.argv) < 2:
        print("Matchering Test Management")
        print("=" * 40)
        print("Usage: python run_tests.py <command>")
        print("")
        print("Test Commands:")
        print("  test         - Run all tests")
        print("  test-unit    - Run unit tests only")
        print("  test-int     - Run integration tests only")
        print("  test-fast    - Run fast tests only")
        print("  test-slow    - Run slow tests only")
        print("  test-player  - Run player tests")
        print("  test-core    - Run core library tests")
        print("  test-dsp     - Run DSP tests")
        print("  test-perf    - Run performance tests")
        print("")
        print("Coverage Commands:")
        print("  coverage     - Run tests with coverage report")
        print("  coverage-html - Generate HTML coverage report")
        print("")
        print("Utility Commands:")
        print("  check        - Check dependencies")
        print("  clean        - Clean test artifacts")
        print("  help         - Show this help")
        print("")
        print("Examples:")
        print("  python run_tests.py test")
        print("  python run_tests.py test-unit")
        print("  python run_tests.py coverage-html")
        return 0

    command = sys.argv[1]

    # Check dependencies for test commands
    if command.startswith('test') or command.startswith('coverage'):
        if not check_dependencies():
            return 1

    if command == "help":
        main()
        return 0

    elif command == "check":
        success = check_dependencies()
        return 0 if success else 1

    elif command == "clean":
        print("🧹 Cleaning test artifacts...")
        artifacts = [
            ".pytest_cache",
            "htmlcov",
            ".coverage",
            "test_report_*.txt",
            "__pycache__"
        ]

        for artifact in artifacts:
            try:
                if Path(artifact).is_file():
                    Path(artifact).unlink()
                    print(f"  Removed {artifact}")
                elif Path(artifact).is_dir():
                    import shutil
                    shutil.rmtree(artifact)
                    print(f"  Removed {artifact}/")
            except Exception as e:
                print(f"  Could not remove {artifact}: {e}")

        print("✅ Cleanup complete")
        return 0

    elif command == "test":
        success = run_command(
            ["python", "-m", "pytest", "-v"],
            "Running all tests"
        )

    elif command == "test-unit":
        success = run_command(
            ["python", "-m", "pytest", "-m", "unit", "-v"],
            "Running unit tests"
        )

    elif command == "test-int":
        success = run_command(
            ["python", "-m", "pytest", "-m", "integration", "-v"],
            "Running integration tests"
        )

    elif command == "test-fast":
        success = run_command(
            ["python", "-m", "pytest", "-m", "not slow", "-v"],
            "Running fast tests"
        )

    elif command == "test-slow":
        success = run_command(
            ["python", "-m", "pytest", "-m", "slow", "-v"],
            "Running slow tests"
        )

    elif command == "test-player":
        success = run_command(
            ["python", "-m", "pytest", "-m", "player", "-v"],
            "Running player tests"
        )

    elif command == "test-core":
        success = run_command(
            ["python", "-m", "pytest", "-m", "core", "-v"],
            "Running core library tests"
        )

    elif command == "test-dsp":
        success = run_command(
            ["python", "-m", "pytest", "-m", "dsp", "-v"],
            "Running DSP tests"
        )

    elif command == "test-perf":
        success = run_command(
            ["python", "-m", "pytest", "-m", "performance", "-v"],
            "Running performance tests"
        )

    elif command == "coverage":
        success = run_command(
            ["python", "-m", "pytest", "--cov=matchering", "--cov=matchering_player",
             "--cov-report=term-missing", "-v"],
            "Running tests with coverage"
        )

    elif command == "coverage-html":
        success = run_command(
            ["python", "-m", "pytest", "--cov=matchering", "--cov=matchering_player",
             "--cov-report=html", "--cov-report=term-missing", "-v"],
            "Generating HTML coverage report"
        )
        if success:
            print(f"\n📊 Coverage report generated at: {Path('htmlcov/index.html').absolute()}")

    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python run_tests.py help' for available commands")
        return 1

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())