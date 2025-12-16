"""
Test script for update_format.py

Tests various format conversion scenarios and validates the tool's functionality.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from update_format import FormatUpdater


def test_single_conversion():
    """Test converting a single file."""
    print("\n" + "="*60)
    print("TEST 1: Single File Conversion")
    print("="*60)
    
    updater = FormatUpdater()
    
    # Test converting example.ncd to .ncdn
    if os.path.exists('example.ncd'):
        success, message = updater.convert_file('example.ncd', 'ncdn', 'test_output.ncdn')
        print(f"Convert .ncd -> .ncdn: {'✅ PASS' if success else '❌ FAIL'}")
        print(f"  {message}")
        
        # Clean up
        if os.path.exists('test_output.ncdn'):
            os.remove('test_output.ncdn')
    else:
        print("❌ example.ncd not found, skipping test")
    
    return success


def test_validation():
    """Test file validation."""
    print("\n" + "="*60)
    print("TEST 2: File Validation")
    print("="*60)
    
    updater = FormatUpdater()
    
    if os.path.exists('example.ncd'):
        ncn_path = 'example.ncn' if os.path.exists('example.ncn') else None
        is_valid, issues = updater.validate_files('example.ncd', ncn_path)
        
        print(f"Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        if issues:
            print(f"  Issues found: {len(issues)}")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"    - {issue}")
        else:
            print(f"  No issues found")
        
        return True
    else:
        print("❌ example.ncd not found, skipping test")
        return False


def test_round_trip():
    """Test round-trip conversion (format A -> B -> A)."""
    print("\n" + "="*60)
    print("TEST 3: Round-Trip Conversion")
    print("="*60)
    
    updater = FormatUpdater()
    
    if not os.path.exists('example.ncd'):
        print("❌ example.ncd not found, skipping test")
        return False
    
    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        # Copy original
        temp_original = os.path.join(temp_dir, 'original.ncd')
        shutil.copy('example.ncd', temp_original)
        if os.path.exists('example.ncn'):
            shutil.copy('example.ncn', os.path.join(temp_dir, 'original.ncn'))
        
        # Convert: .ncd -> .ncdn
        temp_ncdn = os.path.join(temp_dir, 'converted.ncdn')
        success1, msg1 = updater.convert_file(temp_original, 'ncdn', temp_ncdn)
        print(f"Step 1 (.ncd -> .ncdn): {'✅' if success1 else '❌'}")
        
        # Convert: .ncdn -> .ncd
        temp_reconverted = os.path.join(temp_dir, 'reconverted.ncd')
        success2, msg2 = updater.convert_file(temp_ncdn, 'ncd', temp_reconverted)
        print(f"Step 2 (.ncdn -> .ncd): {'✅' if success2 else '❌'}")
        
        # Validate the reconverted file
        is_valid, issues = updater.validate_files(temp_reconverted)
        print(f"Step 3 (Validation): {'✅' if is_valid else '❌'}")
        
        if issues:
            print(f"  Issues: {len(issues)}")
            for issue in issues[:3]:
                print(f"    - {issue}")
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return success1 and success2 and is_valid
        
    except Exception as e:
        print(f"❌ Round-trip test failed: {e}")
        return False


def test_all_format_conversions():
    """Test conversion between all supported formats."""
    print("\n" + "="*60)
    print("TEST 4: All Format Conversions")
    print("="*60)
    
    updater = FormatUpdater()
    
    if not os.path.exists('example.ncd'):
        print("❌ example.ncd not found, skipping test")
        return False
    
    formats = ['ncd', 'ncn', 'ncdn', 'nc.json', 'nci.json']
    
    try:
        temp_dir = tempfile.mkdtemp()
        results = {}
        
        for target_format in formats:
            output_path = os.path.join(temp_dir, f'test.{target_format}')
            success, message = updater.convert_file('example.ncd', target_format, output_path)
            results[target_format] = success
            
            status = '✅' if success else '❌'
            print(f"  {status} .ncd -> .{target_format}")
            
            if success and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"      Size: {file_size} bytes")
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return all(results.values())
        
    except Exception as e:
        print(f"❌ Format conversion test failed: {e}")
        return False


def test_companion_generation():
    """Test generating companion files."""
    print("\n" + "="*60)
    print("TEST 5: Companion File Generation")
    print("="*60)
    
    updater = FormatUpdater()
    
    if not os.path.exists('example.ncd'):
        print("❌ example.ncd not found, skipping test")
        return False
    
    try:
        temp_dir = tempfile.mkdtemp()
        
        # Copy original to temp
        temp_ncd = os.path.join(temp_dir, 'test.ncd')
        shutil.copy('example.ncd', temp_ncd)
        
        # Generate all companions
        generated = updater.generate_companions(
            temp_ncd, 
            generate_ncn=True, 
            generate_json=True,
            generate_ncdn=True,
            generate_nci=True
        )
        
        print(f"Generated {len(generated)} companion files:")
        for path in generated:
            exists = os.path.exists(path)
            status = '✅' if exists else '❌'
            print(f"  {status} {os.path.basename(path)}")
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return len(generated) == 4  # Should generate 4 companions
        
    except Exception as e:
        print(f"❌ Companion generation test failed: {e}")
        return False


def test_batch_conversion():
    """Test batch conversion."""
    print("\n" + "="*60)
    print("TEST 6: Batch Conversion")
    print("="*60)
    
    updater = FormatUpdater()
    
    try:
        # Create temp directory with multiple test files
        temp_dir = tempfile.mkdtemp()
        
        # Create some test .ncd files
        for i in range(3):
            test_file = os.path.join(temp_dir, f'test{i}.ncd')
            if os.path.exists('example.ncd'):
                shutil.copy('example.ncd', test_file)
            else:
                # Create minimal test file
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(f':<:({{test{i}}}) | 1. assigning\n')
        
        # Batch convert
        stats = updater.batch_convert(temp_dir, 'ncd', 'ncdn', recursive=False)
        
        print(f"Total files: {stats['total']}")
        print(f"Success: {stats['success']}")
        print(f"Failed: {stats['failed']}")
        
        success = stats['failed'] == 0 and stats['success'] == stats['total']
        print(f"Batch conversion: {'✅ PASS' if success else '❌ FAIL'}")
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        return success
        
    except Exception as e:
        print(f"❌ Batch conversion test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("NormCode Format Update Tool - Test Suite")
    print("="*60)
    
    tests = [
        ("Single Conversion", test_single_conversion),
        ("Validation", test_validation),
        ("Round-Trip", test_round_trip),
        ("All Formats", test_all_format_conversions),
        ("Companion Generation", test_companion_generation),
        ("Batch Conversion", test_batch_conversion),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = '✅ PASS' if result else '❌ FAIL'
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists('update_format.py'):
        print("❌ Error: Please run this script from the editor_subapp directory")
        print("   cd streamlit_app/editor_subapp")
        sys.exit(1)
    
    success = run_all_tests()
    sys.exit(0 if success else 1)




