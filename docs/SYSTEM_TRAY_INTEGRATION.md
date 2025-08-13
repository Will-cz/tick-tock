# System Tray Integration

This document describes the system tray functionality added to the Tick-Tock Widget application.

## Overview

The Tick-Tock Widget now supports Windows system tray integration, allowing the application to:
- Minimize to the system tray instead of closing
- Show/hide the main window from the system tray
- Display context menu with quick actions
- Show current project status in the tooltip

## Features

### System Tray Icon
- **Icon**: Uses the official `tick_tock_icon.ico` from the assets folder
- **Tooltip**: Shows current project and timing status (e.g., "Tick-Tock Widget - Project Name (🟢 Timing)")
- **Fallback**: If the icon file is not found, a simple green square is used as fallback

### Context Menu
The system tray icon provides a right-click context menu with the following options:
- **Show/Hide Tick-Tock**: Toggles window visibility
- **Show Tick-Tock**: Explicitly shows the main window
- **Hide Tick-Tock**: Explicitly hides the main window to system tray
- **Quit**: Completely exits the application

### Window Behavior
- **Close Button (X)**: Now minimizes to system tray instead of closing (if system tray is available)
- **Minimize to Tray**: Window is hidden but application continues running in the background
- **Restore from Tray**: Double-click or use context menu to restore the window

## Keyboard Shortcuts

The following keyboard shortcuts are available when the main window has focus:

| Shortcut | Action |
|----------|--------|
| `Ctrl+H` | Hide window to system tray |
| `Ctrl+Shift+H` | Show window from system tray |
| `Alt+F4` | Hide to system tray (or quit if tray unavailable) |
| `Escape` | Hide to system tray (or quit if tray unavailable) |

## Dependencies

The system tray functionality requires the following packages:
- `pystray>=0.19.4` - System tray icon management
- `Pillow>=10.0.0` - Image processing for the icon

These are automatically included in `requirements.txt`.

## Graceful Degradation

If the required dependencies are not installed:
- The application will still work normally
- System tray functionality will be disabled
- A warning message will be displayed
- Window close button will quit the application normally

## Technical Implementation

### Files Modified
- `requirements.txt` - Added pystray and Pillow dependencies
- `src/tick_tock_widget/tick_tock_widget.py` - Integrated system tray functionality
- `src/tick_tock_widget/system_tray.py` - New system tray management module

### Key Components

#### SystemTrayManager Class
```python
class SystemTrayManager:
    def __init__(self, main_window_callback, quit_callback)
    def start() -> bool
    def stop()
    def is_running() -> bool
    def update_tooltip(tooltip: str)
```

#### Integration Points
- Window close protocol: `self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)`
- Keyboard shortcuts: Bound in `setup_keyboard_shortcuts()`
- Automatic startup: Called in `run()` method

## Error Handling

The implementation includes comprehensive error handling:
- Missing dependencies are detected gracefully
- Icon loading failures fall back to a simple icon
- System tray errors don't crash the main application
- Thread cleanup is handled properly on application exit

## Testing

To test the system tray functionality:

1. **Installation Test**:
   ```bash
   python test_system_tray.py
   ```

2. **Integration Test**:
   ```bash
   python -m src.tick_tock_widget.main
   ```

3. **Manual Testing**:
   - Click the window close button (X) - should minimize to tray
   - Right-click the system tray icon - should show context menu
   - Try keyboard shortcuts - should hide/show window
   - Check tooltip updates when project changes

## Future Enhancements

Potential improvements for future versions:
- Balloon notifications for important events
- Tray icon animation during timing
- Quick timer controls in tray menu
- Multiple project tray icons
- Custom tray icon themes

## Troubleshooting

### Common Issues

**System tray icon not appearing**:
- Check if `pystray` and `Pillow` are installed
- Verify the icon file exists in `assets/tick_tock_icon.ico`
- Check Windows system tray settings

**Window not hiding properly**:
- Ensure system tray started successfully (check console output)
- Try using keyboard shortcuts instead
- Check for error messages in the console

**Application won't quit**:
- Use the "Quit" option from the system tray context menu
- Check if background processes are still running
- Force quit using Task Manager if necessary

### Debug Information

The application provides debug output during startup:
- `🔧 System tray manager initialized` - Manager created successfully
- `✅ System tray icon started` - Icon is running in system tray
- `Warning: System tray not available` - Dependencies missing
- `Error: ...` - Specific error messages

## Platform Support

Currently tested and supported on:
- **Windows 10/11**: Full support with native system tray
- **Other platforms**: May work but not officially tested

Note: Linux and macOS support depends on the underlying `pystray` library and desktop environment capabilities.
