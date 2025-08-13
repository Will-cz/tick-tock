#!/usr/bin/env python3
"""
System Tray Integration for Tick-Tock Widget
Provides Windows system tray functionality with icon and context menu
"""

import threading
import sys
from pathlib import Path
from typing import Optional, Callable, Any

try:
    import pystray
    from PIL import Image
    SYSTEM_TRAY_AVAILABLE = True
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False
    pystray = None
    Image = None


class SystemTrayManager:
    """Manages system tray icon and menu for the Tick-Tock Widget"""
    
    def __init__(self, main_window_callback: Callable, quit_callback: Callable):
        """
        Initialize the system tray manager
        
        Args:
            main_window_callback: Function to show/hide the main window
            quit_callback: Function to quit the application
        """
        self.main_window_callback = main_window_callback
        self.quit_callback = quit_callback
        self.icon: Optional[Any] = None
        self.tray_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Try to find the icon file
        self.icon_path = self._find_icon_path()
        
    def _find_icon_path(self) -> Optional[Path]:
        """Find the tick_tock_icon.ico file"""
        # Get the directory containing this module
        current_dir = Path(__file__).parent
        
        # Look for the icon in the assets folder relative to the project root
        possible_paths = [
            current_dir.parent.parent / "assets" / "tick_tock_icon.ico",  # From src/tick_tock_widget
            current_dir.parent / "assets" / "tick_tock_icon.ico",         # From src
            current_dir / "assets" / "tick_tock_icon.ico",                # Same directory
            Path("assets") / "tick_tock_icon.ico",                       # Relative to cwd
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        return None
    
    def _load_icon_image(self) -> Optional[Any]:
        """Load the icon image for the system tray"""
        if not SYSTEM_TRAY_AVAILABLE:
            return None
            
        if self.icon_path and self.icon_path.exists():
            try:
                # Load the ICO file
                image = Image.open(self.icon_path)
                
                # Convert to RGBA if needed and resize to appropriate size for system tray
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                    
                # Resize to 16x16 for system tray (Windows standard)
                image = image.resize((16, 16), Image.Resampling.LANCZOS)
                return image
            except Exception as e:
                print(f"Warning: Could not load icon from {self.icon_path}: {e}")
        
        # Create a simple fallback icon if the file is not found
        try:
            # Create a simple 16x16 green square as fallback
            image = Image.new('RGBA', (16, 16), (0, 255, 0, 255))
            return image
        except Exception:
            return None
    
    def _create_menu(self) -> Optional[Any]:
        """Create the context menu for the system tray icon"""
        if not SYSTEM_TRAY_AVAILABLE:
            return None
            
        return pystray.Menu(
            pystray.MenuItem("Show/Hide Tick-Tock", self._toggle_window),
            pystray.MenuItem("Show Tick-Tock", self._show_window),
            pystray.MenuItem("Hide Tick-Tock", self._hide_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_application)
        )
    
    def _toggle_window(self, icon=None, item=None):
        """Toggle the main window visibility"""
        if self.main_window_callback:
            self.main_window_callback()
    
    def _show_window(self, icon=None, item=None):
        """Show the main window"""
        if self.main_window_callback:
            self.main_window_callback(force_show=True)
    
    def _hide_window(self, icon=None, item=None):
        """Hide the main window"""
        if self.main_window_callback:
            self.main_window_callback(force_hide=True)
    
    def _quit_application(self, icon=None, item=None):
        """Quit the entire application"""
        print("🔻 System tray quit requested...")
        try:
            # Stop this system tray first
            self.stop()
            
            # Call the main application quit callback
            if self.quit_callback:
                self.quit_callback()
        except Exception as e:
            print(f"Error in system tray quit: {e}")
            # Force exit if callback fails
            import sys
            sys.exit(1)
    
    def start(self) -> bool:
        """
        Start the system tray icon
        
        Returns:
            True if successfully started, False otherwise
        """
        if not SYSTEM_TRAY_AVAILABLE:
            print("Warning: System tray not available (pystray/Pillow not installed)")
            return False
        
        if self._running:
            return True
            
        try:
            # Load the icon image
            image = self._load_icon_image()
            if not image:
                print("Warning: Could not load icon image for system tray")
                return False
            
            # Create the menu
            menu = self._create_menu()
            
            # Create the system tray icon
            self.icon = pystray.Icon(
                "tick_tock_widget",
                image,
                "Tick-Tock Widget",
                menu
            )
            
            # Start the icon in a separate thread
            self._running = True
            self.tray_thread = threading.Thread(target=self._run_tray, daemon=True)
            self.tray_thread.start()
            
            print("✅ System tray icon started")
            return True
            
        except Exception as e:
            print(f"Error starting system tray: {e}")
            return False
    
    def _run_tray(self):
        """Run the system tray icon (called in separate thread)"""
        try:
            if self.icon:
                self.icon.run()
        except Exception as e:
            print(f"Error running system tray: {e}")
        finally:
            self._running = False
    
    def stop(self):
        """Stop the system tray icon"""
        if not self._running:
            return
            
        self._running = False
        
        if self.icon:
            try:
                self.icon.stop()
            except Exception as e:
                print(f"Error stopping system tray: {e}")
        
        if self.tray_thread and self.tray_thread.is_alive():
            try:
                # Give the thread a moment to clean up
                self.tray_thread.join(timeout=2.0)
            except Exception:
                pass
        
        self.icon = None
        self.tray_thread = None
        print("🔻 System tray icon stopped")
    
    def is_running(self) -> bool:
        """Check if the system tray is running"""
        return self._running and self.icon is not None
    
    def update_tooltip(self, tooltip: str):
        """Update the system tray icon tooltip"""
        if self.icon and self._running:
            try:
                self.icon.title = tooltip
            except Exception as e:
                print(f"Error updating tooltip: {e}")


def is_system_tray_available() -> bool:
    """Check if system tray functionality is available"""
    return SYSTEM_TRAY_AVAILABLE
