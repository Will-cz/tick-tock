# RAM-Safe Testing Guidelines

## **CRITICAL: Prevent RAM Overconsumption in Tests**

### Root Cause of RAM Issues:
1. **Real GUI Widget Creation**: Tests creating actual tkinter windows
2. **Infinite Timer Loops**: GUI timers not properly mocked, running indefinitely
3. **Memory Leaks**: Widgets not properly destroyed after tests
4. **Background Processes**: Test processes not terminating correctly

### **MANDATORY Safety Rules:**

#### 1. **NEVER Run Tests Without Complete GUI Mocking**
```python
# ❌ DANGEROUS - Can create real widgets
def test_without_mocking():
    widget = TickTockWidget()  # Creates real GUI!

# ✅ SAFE - Complete mocking
@patch('tick_tock_widget.tick_tock_widget.tk.Tk')
@patch('tick_tock_widget.tick_tock_widget.ttk.Frame')
def test_with_mocking(self, mock_frame, mock_tk):
    widget = TickTockWidget()  # Creates mock objects only
```

#### 2. **Always Mock Timer Functions**
```python
@patch('tick_tock_widget.tick_tock_widget.after')  # Prevent timer loops
@patch('tick_tock_widget.tick_tock_widget.after_cancel')
```

#### 3. **Use Memory-Safe Test Pattern**
```python
class SafeTestPattern(unittest.TestCase):
    
    def setUp(self):
        # Create temp files, not persistent data
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
    
    def tearDown(self):
        # ALWAYS clean up
        try:
            os.unlink(self.temp_file.name)
        except FileNotFoundError:
            pass
    
    @patch('module.tk')  # Mock ALL GUI
    @patch('module.ttk')
    @patch('module.after')  # Mock timers
    def test_safe_method(self, mock_after, mock_ttk, mock_tk):
        # Test implementation
        pass
```

#### 4. **Identify Dangerous Test Files**
These files may cause RAM issues if run without proper mocking:
- Any test importing `tick_tock_widget.tick_tock_widget`
- Any test importing `tick_tock_widget.minimized_widget`
- Any test importing `tick_tock_widget.project_management`
- Any test creating real data files without cleanup

#### 5. **Safe Testing Commands**
```bash
# ❌ AVOID - Can trigger GUI creation
python -m pytest tests/

# ✅ SAFE - Run specific working tests only
python -m pytest tests/test_config.py -v

# ✅ SAFE - Run with timeout to prevent hanging
timeout 30s python -m pytest tests/test_specific.py
```

### **Emergency Stop Procedures:**
If tests start consuming RAM:
1. **Ctrl+C** to interrupt
2. **Task Manager** → End Python processes
3. **Restart VS Code** if needed
4. **Check this guide** before running more tests

### **Approved Safe Test Files:**
- `test_config.py` - No GUI components
- `test_project_data.py` - Data-only tests
- Any test with complete GUI mocking verified

### **Dangerous Test Files to Avoid:**
- Any test without `@patch('module.tk')` 
- Any test creating real widgets
- Any test with timer functions unmocked
