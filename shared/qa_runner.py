#!/usr/bin/env python3
"""
Campus Emergency Assistance System — Automated QA Test Suite Runner
Owner: P3 — Alert Queue & QA (Day 10 Milestone)

One-click automated runner that executes all QA test suites,
monitors execution timing, tallies pass/fail results, and
renders a formatted Quality Certification Dashboard in the terminal.
"""

import os
import sys
import time
import pytest

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

TEST_SUITES = [
    {
        "tier": "Tier 1",
        "name": "Alert Data & Schema Validation",
        "file": "tests/qa/test_alert_data_validation.py",
        "desc": "Validates boundary coordinates, enum constraints, and XSS sanitization"
    },
    {
        "tier": "Tier 2",
        "name": "Multi-Service Integration Workflows",
        "file": "tests/qa/test_integration_workflows.py",
        "desc": "Integrates campus datasets, alert queue state machine, and SSE streaming"
    },
    {
        "tier": "Tier 3",
        "name": "End-to-End User Journey Scenarios",
        "file": "tests/qa/test_e2e_scenarios.py",
        "desc": "Executes real-world student panic, admin triage, and escalation cycles"
    },
    {
        "tier": "Tier 4",
        "name": "Automated Security & Regression Suite",
        "file": "tests/qa/test_regression_suite.py",
        "desc": "Validates RBAC boundaries, JWT refresh, status immutability, and headers"
    },
    {
        "tier": "Tier 5",
        "name": "Full-System Stress & Concurrency Suite",
        "file": "tests/qa/test_full_system_stress_qa.py",
        "desc": "Simulates 5-student concurrent burst, rapid triage, and debounce defense"
    }
]

class TerminalColors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_banner():
    print(f"\n{TerminalColors.BOLD}{TerminalColors.CYAN}{'=' * 78}{TerminalColors.RESET}")
    print(f"{TerminalColors.BOLD}{TerminalColors.CYAN}    CAMPUS EMERGENCY ASSISTANCE — AUTOMATED QA CERTIFICATION RUNNER{TerminalColors.RESET}")
    print(f"{TerminalColors.BOLD}{TerminalColors.CYAN}    P3: Alert Queue & QA Lead Verification Harness (Day 10){TerminalColors.RESET}")
    print(f"{TerminalColors.BOLD}{TerminalColors.CYAN}{'=' * 78}{TerminalColors.RESET}\n")


class TestResultCollector:
    """Pytest plugin to capture passed, failed, and skipped counts."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            if report.passed:
                self.passed += 1
            elif report.failed:
                self.failed += 1
            elif report.skipped:
                self.skipped += 1


def run_single_suite(suite_info):
    test_file_path = os.path.join(WORKSPACE_ROOT, suite_info["file"])
    collector = TestResultCollector()
    
    start_time = time.time()
    # Run pytest quietly for this file
    exit_code = pytest.main(
        [test_file_path, "-q", "--disable-warnings"],
        plugins=[collector]
    )
    duration = time.time() - start_time
    
    return {
        "suite": suite_info,
        "exit_code": exit_code,
        "passed": collector.passed,
        "failed": collector.failed,
        "skipped": collector.skipped,
        "duration": duration
    }


def main():
    print_banner()
    overall_start = time.time()
    results = []
    
    print(f"Executing {len(TEST_SUITES)} Quality Assurance Test Suites...\n")

    for idx, s in enumerate(TEST_SUITES, 1):
        print(f"[{idx}/{len(TEST_SUITES)}] Running {s['tier']}: {s['name']}...", end=" ", flush=True)
        res = run_single_suite(s)
        results.append(res)
        if res["exit_code"] == 0 and res["failed"] == 0:
            print(f"{TerminalColors.GREEN}PASSED{TerminalColors.RESET} ({res['passed']} tests, {res['duration']:.2f}s)")
        else:
            print(f"{TerminalColors.RED}FAILED{TerminalColors.RESET} ({res['failed']} failed, {res['duration']:.2f}s)")

    total_duration = time.time() - overall_start
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_skipped = sum(r["skipped"] for r in results)
    total_tests = total_passed + total_failed + total_skipped
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"\n{TerminalColors.BOLD}{'=' * 78}{TerminalColors.RESET}")
    print(f"{TerminalColors.BOLD}QA EXECUTION SUMMARY MATRIX{TerminalColors.RESET}")
    print(f"{'=' * 78}")
    print(f"{'Tier':<8} | {'Test Suite':<38} | {'Passed':<6} | {'Failed':<6} | {'Time':<7}")
    print(f"{'-' * 8}-+-{'-' * 38}-+-{'-' * 6}-+-{'-' * 6}-+-{'-' * 7}")

    for r in results:
        s = r["suite"]
        status_color = TerminalColors.GREEN if r["failed"] == 0 else TerminalColors.RED
        print(
            f"{s['tier']:<8} | "
            f"{s['name'][:38]:<38} | "
            f"{status_color}{r['passed']:<6}{TerminalColors.RESET} | "
            f"{status_color}{r['failed']:<6}{TerminalColors.RESET} | "
            f"{r['duration']:.2f}s"
        )

    print(f"{'=' * 78}")
    print(f"Total Tests Executed : {total_tests}")
    print(f"Total Tests Passed   : {TerminalColors.GREEN}{total_passed}{TerminalColors.RESET}")
    print(f"Total Tests Failed   : {TerminalColors.RED if total_failed > 0 else TerminalColors.GREEN}{total_failed}{TerminalColors.RESET}")
    print(f"Pass Rate            : {TerminalColors.BOLD}{TerminalColors.GREEN if pass_rate == 100 else TerminalColors.YELLOW}{pass_rate:.1f}%{TerminalColors.RESET}")
    print(f"Total Execution Time : {total_duration:.2f} seconds")
    print(f"{'=' * 78}")

    if total_failed == 0:
        print(f"\n{TerminalColors.BOLD}{TerminalColors.GREEN}[SUCCESS] All QA Milestones Certified! Ready for Team Integration.{TerminalColors.RESET}\n")
        return 0
    else:
        print(f"\n{TerminalColors.BOLD}{TerminalColors.RED}[FAILURE] {total_failed} QA test cases failed! Review logs.{TerminalColors.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
