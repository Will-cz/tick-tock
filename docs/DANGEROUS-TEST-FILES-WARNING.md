# ⚠️ DANGEROUS TEST FILES - DO NOT RUN WITHOUT FIXING

## **HIGH RAM CONSUMPTION RISK FILES:**

### **CRITICAL - These files create real GUI widgets:**
- `test_tick_tock_widget_extended.py` - 17 instances of `TickTockWidget()` creation
- `test_minimized_widget_extended.py` - 19 instances of `MinimizedTickTockWidget()` creation  
- `test_gui_geometry_validation.py` - Multiple GUI widget creations
- `test_dynamic_gui_geometry_validation.py` - GUI validation tests
- `test_integration.py` - Integration tests with real widgets
- `test_performance_optimization.py` - Performance tests
- `test_tick_tock_widget.py` - Original widget tests

### **RAM CONSUMPTION CAUSES:**
1. **Real tkinter widgets** created in each test method
2. **Timer loops** not properly mocked, running infinitely
3. **Window creation** without proper cleanup
4. **Multiple widget instances** created simultaneously

### **IMMEDIATE SAFETY ACTIONS:**

#### 1. **NEVER run these commands:**
```bash
# ❌ DANGEROUS - Will consume all RAM
python -m pytest tests/
python -m pytest tests/test_tick_tock_widget_extended.py
python -m pytest tests/test_minimized_widget_extended.py
python -m pytest tests/test_gui_geometry_validation.py
```

#### 2. **SAFE alternatives:**
```bash
# ✅ SAFE - Run only non-GUI tests
python -m pytest tests/test_config.py
python -m pytest tests/test_project_data.py
python -m pytest tests/test_theme_colors.py
```

#### 3. **If you accidentally run dangerous tests:**
- **Immediately press Ctrl+C**
- **Open Task Manager** and end all python.exe processes
- **Restart VS Code** if necessary

### **FILES TO FIX BEFORE USING:**
Each of these needs comprehensive GUI mocking added:

1. **test_tick_tock_widget_extended.py** - Add `@patch('tick_tock_widget.tick_tock_widget.tk')`
2. **test_minimized_widget_extended.py** - Add `@patch('tick_tock_widget.minimized_widget.tk')`
3. **test_gui_geometry_validation.py** - Add comprehensive GUI mocking
4. **test_integration.py** - Add complete widget mocking
5. **test_performance_optimization.py** - Add performance-safe mocking

### **WORKING SAFE FILES:**
- `test_tick_tock_widget_core.py` - ✅ Has proper mocking
- `test_monthly_report.py` - ✅ Has proper GUI mocking  
- `test_config.py` - ✅ No GUI components
- `test_project_data.py` - ✅ Data-only tests

### **EMERGENCY CONTACT:**
If your system becomes unresponsive due to RAM consumption:
1. Ctrl+Alt+Del → Task Manager
2. End all python.exe processes
3. Reboot if necessary
4. Check this warning file before running any tests
