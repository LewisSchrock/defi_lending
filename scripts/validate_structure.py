#!/usr/bin/env python3
"""
Code Structure Validation Script

Validates that all adapter files are present and properly structured.
This runs without network access to check code integrity.

Usage:
    python scripts/validate_structure.py
"""

import os
import sys
from pathlib import Path

# Expected file structure
EXPECTED_STRUCTURE = {
    'adapters/tvl': [
        'aave_v3.py',
        'compound_v2_style.py',
        'compound_v3.py',
        'fluid.py',
        'lista.py',
        'gearbox.py',
        'cap.py',
        '__init__.py',
    ],
    'adapters/liquidations': [
        'aave_v3.py',
        'compound_v2_style.py',
        'compound_v3.py',
        'fluid.py',
        'lista.py',
        'gearbox.py',
        'cap.py',
        '__init__.py',
    ],
    'config': [
        'rpc_config.py',
        'units.csv',
        '__init__.py',
    ],
    'scripts': [
        'test_single_csu.py',
        'test_all_csus.py',
        'validate_structure.py',
        '__init__.py',
    ],
    'docs': [
        'TESTING_GUIDE.md',
        'COMPLETE.md',
        'CODE_REUSE_ACHIEVEMENT.md',
        'QUICKSTART.md',
        'TROUBLESHOOTING.md',
    ],
}

# Expected function signatures
ADAPTER_FUNCTIONS = {
    'tvl': {
        'aave_v3.py': 'get_aave_v3_tvl',
        'compound_v2_style.py': 'get_compound_style_tvl',
        'compound_v3.py': 'get_compound_v3_tvl',
        'fluid.py': 'get_fluid_tvl',
        'lista.py': 'get_lista_tvl',
        'gearbox.py': 'get_gearbox_tvl',
        'cap.py': 'get_cap_tvl',
    },
    'liquidations': {
        'aave_v3.py': 'scan_aave_liquidations',
        'compound_v2_style.py': 'scan_compound_style_liquidations',
        'compound_v3.py': 'scan_compound_v3_liquidations',
        'fluid.py': 'scan_fluid_liquidations',
        'lista.py': 'scan_lista_liquidations',
        'gearbox.py': 'scan_gearbox_liquidations',
        'cap.py': 'scan_cap_liquidations',
    },
}


def validate_files():
    """Check that all expected files exist."""
    print("Validating file structure...")
    missing = []
    present = []
    
    for directory, files in EXPECTED_STRUCTURE.items():
        for filename in files:
            filepath = Path(directory) / filename
            if filepath.exists():
                present.append(str(filepath))
            else:
                missing.append(str(filepath))
    
    print(f"✅ Present: {len(present)} files")
    if missing:
        print(f"❌ Missing: {len(missing)} files")
        for f in missing:
            print(f"   - {f}")
        return False
    return True


def validate_functions():
    """Check that adapter files have expected functions."""
    print("\nValidating adapter functions...")
    issues = []
    
    for adapter_type, functions in ADAPTER_FUNCTIONS.items():
        for filename, func_name in functions.items():
            filepath = Path('adapters') / adapter_type / filename
            if not filepath.exists():
                continue
            
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                if f'def {func_name}' not in content:
                    issues.append(f"{filepath}: Missing function '{func_name}'")
            except Exception as e:
                issues.append(f"{filepath}: Error reading file: {e}")
    
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print(f"✅ All adapter functions present")
    return True


def validate_imports():
    """Check that adapter files have required imports."""
    print("\nValidating imports...")
    required_imports = {
        'tvl': ['from web3 import Web3', 'from typing import'],
        'liquidations': ['from web3 import Web3', 'from typing import', 'import time'],
    }
    
    issues = []
    
    for adapter_type, imports in required_imports.items():
        for filename in ADAPTER_FUNCTIONS[adapter_type].keys():
            filepath = Path('adapters') / adapter_type / filename
            if not filepath.exists():
                continue
            
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                for required_import in imports:
                    if required_import not in content:
                        issues.append(f"{filepath}: Missing '{required_import}'")
            except Exception as e:
                issues.append(f"{filepath}: Error reading file: {e}")
    
    if issues:
        print(f"❌ Found {len(issues)} import issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"   - {issue}")
        if len(issues) > 5:
            print(f"   ... and {len(issues) - 5} more")
        return False
    
    print(f"✅ All required imports present")
    return True


def count_lines():
    """Count total lines of code."""
    print("\nCounting lines of code...")
    total = 0
    
    for adapter_type in ['tvl', 'liquidations']:
        for filename in ADAPTER_FUNCTIONS[adapter_type].keys():
            filepath = Path('adapters') / adapter_type / filename
            if not filepath.exists():
                continue
            
            try:
                with open(filepath, 'r') as f:
                    lines = len(f.readlines())
                    total += lines
            except Exception:
                pass
    
    print(f"📊 Total adapter code: ~{total:,} lines")
    return total


def main():
    """Run all validations."""
    print("="*60)
    print("CODE STRUCTURE VALIDATION")
    print("="*60)
    
    checks = [
        ('File Structure', validate_files),
        ('Adapter Functions', validate_functions),
        ('Required Imports', validate_imports),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}: Exception: {e}")
            results.append((name, False))
    
    # Count lines
    count_lines()
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n📊 Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 Code structure is valid!")
        print("Ready to test on local machine with network access.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} checks failed.")
        print("Review issues above before testing.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
