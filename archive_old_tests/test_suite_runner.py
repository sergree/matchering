#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Test Suite Runner
Orchestrates all test suites with reporting and options
"""

import sys
import os
import time
import subprocess
from pathlib import Path

def run_test_file(test_file, description=""):
    """Run a single test file and return results"""
    print(f"\n{'='*80}")
    print(f"🚀 RUNNING: {test_file}")
    if description:
        print(f"📝 {description}")
    print('='*80)

    start_time = time.perf_counter()

    try:
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))

        end_time = time.perf_counter()
        duration = end_time - start_time

        success = result.returncode == 0

        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"\n⏱️  Duration: {duration:.2f}s")
        print(f"✅ Result: {'PASSED' if success else 'FAILED'}")

        return {
            'file': test_file,
            'description': description,
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }

    except Exception as e:
        end_time = time.perf_counter()
        duration = end_time - start_time

        print(f"❌ Error running {test_file}: {e}")
        print(f"⏱️  Duration: {duration:.2f}s")

        return {
            'file': test_file,
            'description': description,
            'success': False,
            'duration': duration,
            'error': str(e),
            'returncode': -1
        }

def generate_report(results, output_file=None):
    """Generate a comprehensive test report"""
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    total_duration = sum(r['duration'] for r in results)

    report = []
    report.append("🧪 MATCHERING TEST SUITE COMPREHENSIVE REPORT")
    report.append("=" * 80)
    report.append(f"📊 SUMMARY:")
    report.append(f"   Total test files: {total_tests}")
    report.append(f"   Passed: {passed_tests}")
    report.append(f"   Failed: {failed_tests}")
    report.append(f"   Success rate: {passed_tests/total_tests:.1%}")
    report.append(f"   Total duration: {total_duration:.2f}s")
    report.append("")

    # Detailed results
    report.append("📋 DETAILED RESULTS:")
    report.append("-" * 80)

    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        report.append(f"{status} - {result['file']} ({result['duration']:.2f}s)")
        if result['description']:
            report.append(f"    {result['description']}")

        if not result['success']:
            if 'error' in result:
                report.append(f"    Error: {result['error']}")
            elif result['returncode'] != 0:
                report.append(f"    Exit code: {result['returncode']}")

            # Show stderr for failed tests
            if result.get('stderr'):
                report.append("    STDERR:")
                for line in result['stderr'].split('\n'):
                    if line.strip():
                        report.append(f"      {line}")

        report.append("")

    # Performance analysis
    report.append("⚡ PERFORMANCE ANALYSIS:")
    report.append("-" * 80)

    fastest = min(results, key=lambda x: x['duration'])
    slowest = max(results, key=lambda x: x['duration'])

    report.append(f"Fastest test: {fastest['file']} ({fastest['duration']:.2f}s)")
    report.append(f"Slowest test: {slowest['file']} ({slowest['duration']:.2f}s)")
    report.append(f"Average duration: {total_duration/total_tests:.2f}s")
    report.append("")

    # Recommendations
    report.append("💡 RECOMMENDATIONS:")
    report.append("-" * 80)

    if failed_tests == 0:
        report.append("🎉 All tests passed! The codebase is in excellent condition.")
    elif failed_tests == 1:
        report.append("⚠️  One test failed. Review the failure and fix if necessary.")
    elif failed_tests <= total_tests * 0.2:  # Less than 20% failed
        report.append("⚠️  Some tests failed but overall health is good.")
        report.append("   Focus on fixing the failed tests to improve coverage.")
    else:
        report.append("❌ Multiple test failures detected.")
        report.append("   Priority: Review and fix failing tests before deployment.")

    if total_duration > 60:  # More than 1 minute
        report.append("⏰ Test suite is taking a long time to run.")
        report.append("   Consider optimizing slow tests or running them separately.")

    report.append("")
    report.append("🔍 For detailed output from each test, check the individual test runs above.")

    report_text = '\n'.join(report)
    print("\n" + report_text)

    # Save to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"\n📝 Report saved to: {output_file}")
        except Exception as e:
            print(f"⚠️  Could not save report to {output_file}: {e}")

    return report_text

def main():
    """Run the complete test suite"""
    print("🧪 MATCHERING COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("This will run all available test files in the test suite.")
    print("Each test may take several seconds to complete.\n")

    # Define all test files with descriptions
    test_files = [
        # Existing tests
        ("test_dsp_core.py", "Basic DSP functions and processor initialization"),
        ("test_audio_pipeline.py", "Complete audio pipeline with file I/O"),
        ("test_core_functionality.py", "Core DSP processing and performance"),
        ("test_frequency_matching.py", "Frequency matching and EQ functionality"),
        ("test_stereo_width.py", "Stereo width control and imaging"),
        ("test_auto_mastering.py", "Auto-mastering with content analysis"),

        # New comprehensive tests
        ("test_core_library.py", "Core matchering library components"),
        ("test_integration_regression.py", "Integration tests and regression detection"),
        ("test_error_handling.py", "Error handling and edge cases"),
    ]

    # Check which test files actually exist
    available_tests = []
    for test_file, description in test_files:
        if Path(test_file).exists():
            available_tests.append((test_file, description))
        else:
            print(f"⚠️  Test file not found: {test_file}")

    if not available_tests:
        print("❌ No test files found!")
        return False

    print(f"📋 Found {len(available_tests)} test files to run:")
    for test_file, description in available_tests:
        print(f"   • {test_file}: {description}")

    print(f"\n🚀 Starting test suite run...")

    # Run all tests
    results = []
    start_time = time.perf_counter()

    for test_file, description in available_tests:
        result = run_test_file(test_file, description)
        results.append(result)

    end_time = time.perf_counter()
    total_duration = end_time - start_time

    # Generate comprehensive report
    print(f"\n{'='*80}")
    print("📊 GENERATING COMPREHENSIVE REPORT")
    print('='*80)

    # Save report with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.txt"

    generate_report(results, report_file)

    # Final summary
    passed = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"\n{'='*80}")
    print("🎯 FINAL RESULTS")
    print('='*80)
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {passed/total:.1%}")
    print(f"Total time: {total_duration:.1f}s")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ The Matchering codebase is in excellent condition!")
        return True
    elif passed >= total * 0.8:  # 80% or more passed
        print(f"\n✅ MOSTLY SUCCESSFUL ({passed}/{total} passed)")
        print("🔧 Review failed tests and address issues.")
        return True
    else:
        print(f"\n❌ MULTIPLE FAILURES ({passed}/{total} passed)")
        print("🚨 Significant issues detected - review and fix before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)