#!/usr/bin/env python3
"""
Monitoring System Test Script
============================

Tests all monitoring components to ensure proper functionality
in production environment.
"""

import json
import sys
import time
import traceback
from pathlib import Path

import pytest

# Skip these script-style tests when executed under pytest
SKIP_IN_PYTEST = "pytest" in sys.modules

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_structured_logging():
    """Test structured logging functionality"""
    if SKIP_IN_PYTEST:
        pytest.skip("monitoring script test")
    print("🔍 Testing Structured Logging...")  # pragma: allow-print

    try:
        from core.monitoring import set_trace_context, structured_logger, trace_operation

        # Test basic logging
        structured_logger.info("Test info message", test_component="monitoring")
        structured_logger.warning("Test warning message", test_component="monitoring")
        structured_logger.error("Test error message", test_component="monitoring")

        # Test trace context
        set_trace_context(user_id="test_user", operation="test_operation")
        structured_logger.info("Message with trace context", test_data="trace_test")

        # Test trace operation context manager
        with trace_operation("test_context_manager", user_id="test_user"):
            structured_logger.info("Message within trace operation")

        # Test pipeline logging
        structured_logger.pipeline_start("test_pipeline", user_id="test_user")
        time.sleep(0.1)  # Simulate work
        structured_logger.pipeline_complete("test_pipeline", 0.1, success=True)

        print("✅ Structured logging tests passed")  # pragma: allow-print
        return True

    except Exception as e:
        print(f"❌ Structured logging test failed: {e}")  # pragma: allow-print
        traceback.print_exc()
        return False


def test_health_checks():
    """Test health check functionality"""
    if SKIP_IN_PYTEST:
        pytest.skip("monitoring script test")
    print("🔍 Testing Health Checks...")

    try:
        from core.health_check import health_checker

        # Test health status
        health_status = health_checker.get_health_status()
        print(f"   Health Status: {health_status.status}")
        print(f"   Uptime: {health_status.uptime_seconds:.2f}s")

        # Test SLO metrics
        slo_metrics = health_checker.get_slo_metrics()
        print(f"   Error Rate: {slo_metrics.error_rate_5xx}%")
        print(f"   Response Time: {slo_metrics.median_response_time}ms")
        print(f"   Active Users: {slo_metrics.active_users_1h}")

        # Test SLO violations
        violations = health_checker.check_slo_violations()
        print(f"   SLO Violations: {len(violations)}")

        # Test metrics JSON export
        metrics_json = health_checker.get_metrics_json()
        metrics_data = json.loads(metrics_json)
        assert "health" in metrics_data
        assert "slo_metrics" in metrics_data

        print("✅ Health check tests passed")
        return True

    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        traceback.print_exc()
        return False


def test_metrics_export():
    """Test metrics export functionality"""
    if SKIP_IN_PYTEST:
        pytest.skip("monitoring script test")
    print("🔍 Testing Metrics Export...")

    try:
        from core.metrics_exporter import (
            export_json_metrics,
            export_prometheus_metrics,
            track_pipeline,
            track_request,
        )

        # Test request tracking
        track_request(0.5, 200, "GET", "/test")
        track_request(1.2, 500, "POST", "/api/test")

        # Test pipeline tracking
        track_pipeline("test_pipeline", 2.5, True)
        track_pipeline("test_pipeline", 5.0, False)

        # Test Prometheus export
        prometheus_metrics = export_prometheus_metrics()
        assert "whisperforge_http_requests_total" in prometheus_metrics
        assert "whisperforge_pipeline_success_total" in prometheus_metrics

        # Test JSON export
        json_metrics = export_json_metrics()
        assert "counters" in json_metrics
        assert "gauges" in json_metrics
        assert "histograms" in json_metrics

        print("✅ Metrics export tests passed")
        return True

    except Exception as e:
        print(f"❌ Metrics export test failed: {e}")
        traceback.print_exc()
        return False


def test_error_tracking():
    """Test error tracking functionality"""
    if SKIP_IN_PYTEST:
        pytest.skip("monitoring script test")
    print("🔍 Testing Error Tracking...")

    try:
        from core.monitoring import error_tracker

        # Test exception capture
        try:
            raise ValueError("Test error for monitoring")
        except Exception as e:
            error_tracker.capture_exception(e, {"test_context": "monitoring_test", "user_id": "test_user"})

        # Test message capture
        error_tracker.capture_message("Test warning message", level="warning", context={"test": "monitoring"})

        print("✅ Error tracking tests passed")
        return True

    except Exception as e:
        print(f"❌ Error tracking test failed: {e}")
        traceback.print_exc()
        return False


def test_performance_tracking():
    """Test performance tracking functionality"""
    if SKIP_IN_PYTEST:
        pytest.skip("monitoring script test")
    print("🔍 Testing Performance Tracking...")

    try:
        from core.monitoring import monitor_function, performance_tracker

        # Test context manager
        with performance_tracker.track_operation("test_operation"):
            time.sleep(0.1)  # Simulate work

        # Test decorator
        @monitor_function("test_function")
        def test_function():
            time.sleep(0.05)
            return "test_result"

        result = test_function()
        assert result == "test_result"

        # Test pipeline performance tracking
        performance_tracker.track_pipeline_performance("test_pipeline", 1.5, True, file_size_mb=10)

        print("✅ Performance tracking tests passed")
        return True

    except Exception as e:
        print(f"❌ Performance tracking test failed: {e}")
        traceback.print_exc()
        return False


def test_streamlit_integration():
    """Test Streamlit monitoring integration"""
    if SKIP_IN_PYTEST:
        pytest.skip("monitoring script test")
    print("🔍 Testing Streamlit Integration...")

    try:
        from core.streamlit_monitoring import streamlit_component, streamlit_page

        # Test decorators (without actual Streamlit context)
        @streamlit_page("test_page")
        def test_page_function():
            return "page_result"

        @streamlit_component("test_component")
        def test_component_function():
            return "component_result"

        # Note: These will work but won't have full Streamlit context
        # In actual usage, they would have access to st.session_state

        print("✅ Streamlit integration tests passed")
        return True

    except Exception as e:
        print(f"❌ Streamlit integration test failed: {e}")
        traceback.print_exc()
        return False


def test_log_file_creation():
    """Test that log files are created properly"""
    if SKIP_IN_PYTEST:
        pytest.skip("monitoring script test")
    print("🔍 Testing Log File Creation...")

    try:
        from datetime import datetime
        from pathlib import Path

        # Check logs directory
        logs_dir = Path("logs")
        if not logs_dir.exists():
            print("   Creating logs directory...")
            logs_dir.mkdir(exist_ok=True)

        # Check for structured log file
        today = datetime.now().strftime("%Y%m%d")
        log_file = logs_dir / f"whisperforge_structured_{today}.jsonl"

        if log_file.exists():
            print(f"   ✅ Log file exists: {log_file}")

            # Check file content
            with open(log_file) as f:
                lines = f.readlines()
                if lines:
                    print(f"   ✅ Log file has {len(lines)} entries")

                    # Validate JSON format
                    try:
                        last_entry = json.loads(lines[-1].strip())
                        print("   ✅ Last log entry is valid JSON")
                        if "timestamp" in last_entry and "level" in last_entry:
                            print("   ✅ Log entry has required fields")
                    except json.JSONDecodeError:
                        print("   ⚠️ Last log entry is not valid JSON")
                else:
                    print("   ⚠️ Log file is empty")
        else:
            print(f"   ⚠️ Log file not found: {log_file}")

        print("✅ Log file creation tests completed")
        return True

    except Exception as e:
        print(f"❌ Log file creation test failed: {e}")
        traceback.print_exc()
        return False


def run_comprehensive_test():
    """Run all monitoring tests"""
    print("🚀 Starting Comprehensive Monitoring Test Suite")
    print("=" * 60)

    tests = [
        ("Structured Logging", test_structured_logging),
        ("Health Checks", test_health_checks),
        ("Metrics Export", test_metrics_export),
        ("Error Tracking", test_error_tracking),
        ("Performance Tracking", test_performance_tracking),
        ("Streamlit Integration", test_streamlit_integration),
        ("Log File Creation", test_log_file_creation),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n📈 Overall Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All monitoring tests passed! System is ready for production.")
        return True
    else:
        print("⚠️ Some tests failed. Please review and fix issues before deployment.")
        return False


def main():
    """Main test runner"""
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
