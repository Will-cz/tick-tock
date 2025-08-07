#!/usr/bin/env python3
"""
Simple test to verify the GUI geometry validation imports work correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing import of test_gui_geometry_validation...")

try:
    from tests.test_gui_geometry_validation import GeometryInfo, ValidationResult, KeyboardAccessibilityRule
    print("✅ Import successful! All classes are available:")
    print(f"  - GeometryInfo: {GeometryInfo}")
    print(f"  - ValidationResult: {ValidationResult}")
    print(f"  - KeyboardAccessibilityRule: {KeyboardAccessibilityRule}")
    
    # Test creating instances
    print("\nTesting class instantiation...")
    
    # Mock widget for testing GeometryInfo
    class MockWidget:
        def winfo_x(self): return 10
        def winfo_y(self): return 20
        def winfo_width(self): return 100
        def winfo_height(self): return 50
        def winfo_reqwidth(self): return 100
        def winfo_reqheight(self): return 50
        def winfo_class(self): return "Button"
        def winfo_viewable(self): return True
        
        class __class__:
            __module__ = "tkinter"
            __name__ = "Button"
    
    mock_widget = MockWidget()
    geo_info = GeometryInfo(mock_widget, "test_button")
    print(f"  - GeometryInfo created: {geo_info.name}, type: {geo_info.widget_type}")
    
    validation_result = ValidationResult(
        rule_name="test",
        passed=True,
        severity="PASS",
        issues=[],
        confidence=1.0,
        metadata={}
    )
    print(f"  - ValidationResult created: {validation_result.rule_name}")
    
    keyboard_rule = KeyboardAccessibilityRule()
    print(f"  - KeyboardAccessibilityRule created: {keyboard_rule.name}")
    
    print("\n🎉 All tests passed! The NameError issues have been resolved.")
    
except Exception as e:
    print(f"❌ Import failed with error: {e}")
    import traceback
    traceback.print_exc()
