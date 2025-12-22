"""
Quick validation tests for the refactored execute tab.
Run this to verify the refactoring works correctly.
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all new modules import correctly."""
    print("Testing imports...")
    
    try:
        # Import from execute package
        from streamlit_app.tabs.execute import constants
        print("[PASS] constants imported successfully")
        
        from streamlit_app.tabs.execute import state
        print("[PASS] state imported successfully")
        
        from streamlit_app.tabs.execute import logging as execute_logging
        print("[PASS] logging imported successfully")
        
        # Skip UI components and engine that require streamlit
        print("[SKIP] ui_components (requires streamlit)")
        print("[SKIP] engine (requires streamlit)")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_state():
    """Test ExecutionState class."""
    print("\nTesting ExecutionState...")
    
    try:
        from streamlit_app.tabs.execute.state import ExecutionState, ExecutionStatus
        
        state = ExecutionState()
        
        # Test lifecycle
        state.start("test_run_001")
        assert state.status == ExecutionStatus.RUNNING
        assert state.run_id == "test_run_001"
        print("[PASS] State start works")
        
        # Test phase transitions
        state.set_phase("setup")
        assert state.current_phase == "setup"
        print("[PASS] Phase transitions work")
        
        # Test metrics updates
        state.update_metrics(total_items=10, completed_items=5)
        assert state.metrics.total_items == 10
        assert state.metrics.completed_items == 5
        assert state.metrics.progress_percentage == 50.0
        print("[PASS] Metrics update works")
        
        # Test warnings
        state.add_warning("Test warning")
        assert len(state.warnings) == 1
        print("[PASS] Warning tracking works")
        
        # Test debug info
        state.add_debug_info("test_key", "test_value")
        assert state.debug_info["test_key"] == "test_value"
        print("[PASS] Debug info works")
        
        # Test completion
        state.complete()
        assert state.status == ExecutionStatus.COMPLETED
        print("[PASS] State completion works")
        
        # Test summary
        summary = state.get_status_summary()
        assert summary['run_id'] == "test_run_001"
        assert summary['progress'] == "50.0%"
        print("[PASS] Status summary works")
        
        return True
    except Exception as e:
        print(f"[FAIL] ExecutionState test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_metrics():
    """Test ExecutionMetrics calculations."""
    print("\nTesting ExecutionMetrics...")
    
    try:
        from streamlit_app.tabs.execute.state import ExecutionMetrics
        from datetime import datetime, timedelta
        
        metrics = ExecutionMetrics()
        
        # Test success rate
        metrics.total_executions = 10
        metrics.successful_executions = 8
        assert metrics.success_rate == 80.0
        print("[PASS] Success rate calculation works")
        
        # Test progress
        metrics.total_items = 20
        metrics.completed_items = 15
        assert metrics.progress_percentage == 75.0
        print("[PASS] Progress calculation works")
        
        # Test elapsed time
        metrics.start_time = datetime.now() - timedelta(seconds=10)
        assert 9.5 < metrics.elapsed_time < 10.5
        print("[PASS] Elapsed time calculation works")
        
        return True
    except Exception as e:
        print(f"[FAIL] ExecutionMetrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_logger():
    """Test ExecutionLogger class."""
    print("\nTesting ExecutionLogger...")
    
    try:
        from streamlit_app.tabs.execute.logging import ExecutionLogger
        
        logger = ExecutionLogger("test_run_002")
        
        # Test phase logging
        logger.log_phase("setup", "Setup started")
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0]['type'] == 'phase'
        print("[PASS] Phase logging works")
        
        # Test metric logging
        logger.log_metric("items_count", 42)
        logs = logger.get_logs()
        assert len(logs) == 2
        metrics = logger.get_logs_by_type('metric')
        assert len(metrics) == 1
        assert metrics[0]['value'] == 42
        print("[PASS] Metric logging works")
        
        # Test event logging
        logger.log_event("test_event", {"key": "value"})
        events = logger.get_logs_by_type('event')
        assert len(events) == 1
        print("[PASS] Event logging works")
        
        # Test export
        exported = logger.export_to_dict()
        assert exported['run_id'] == "test_run_002"
        assert exported['total_entries'] == 3
        print("[PASS] Export works")
        
        return True
    except Exception as e:
        print(f"[FAIL] ExecutionLogger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constants():
    """Test constants are properly defined."""
    print("\nTesting constants...")
    
    try:
        from streamlit_app.tabs.execute.constants import (
            OPERATION_ICONS, STATUS_ICONS, ExecutionPhase
        )
        
        # Test operation icons
        assert 'READ' in OPERATION_ICONS
        assert 'SAVE' in OPERATION_ICONS
        print("[PASS] Operation icons defined")
        
        # Test status icons
        assert 'SUCCESS' in STATUS_ICONS
        assert 'ERROR' in STATUS_ICONS
        print("[PASS] Status icons defined")
        
        # Test execution phases
        assert hasattr(ExecutionPhase, 'SETUP')
        assert hasattr(ExecutionPhase, 'EXECUTION')
        print("[PASS] Execution phases defined")
        
        return True
    except Exception as e:
        print(f"[FAIL] Constants test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all validation tests."""
    print("=" * 60)
    print("REFACTORED EXECUTE TAB VALIDATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("ExecutionState", test_execution_state),
        ("ExecutionMetrics", test_execution_metrics),
        ("ExecutionLogger", test_execution_logger),
        ("Constants", test_constants),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Refactoring is working correctly.")
        return True
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

