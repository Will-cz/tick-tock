#!/usr/bin/env python3
"""
GUI Test Utilities for Tick-Tock Widget
Provides utilities to prevent GUI tests from hanging and ensure proper cleanup
"""

import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from typing import List, Any


class GUITestMixin:
    """Mixin class for GUI tests that provides proper setup and cleanup"""
    
    def setUp(self):
        """Set up GUI test environment with proper mocking"""
        super().setUp() if hasattr(super(), 'setUp') else None
        
        # Store created widgets for cleanup
        self.created_widgets: List[Any] = []
        self.created_roots: List[tk.Tk] = []
    
    def tearDown(self):
        """Clean up all GUI components"""
        # Clean up any created widgets
        for widget in getattr(self, 'created_widgets', []):
            try:
                if hasattr(widget, 'root') and widget.root:
                    widget.root.destroy()
            except (tk.TclError, AttributeError):
                pass
        
        # Clean up any created root windows
        for root in getattr(self, 'created_roots', []):
            try:
                if root and root.winfo_exists():
                    root.destroy()
            except (tk.TclError, AttributeError):
                pass
        
        super().tearDown() if hasattr(super(), 'tearDown') else None
    
    def create_mock_parent(self):
        """Create a properly mocked parent widget"""
        mock_parent = MagicMock()
        root = tk.Tk()
        root.withdraw()  # Hide immediately
        self.created_roots.append(root)
        
        mock_parent.root = root
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#FF0000',
            'button_bg': '#111111',
            'button_fg': '#EEEEEE',
            'button_active': '#222222'
        }
        return mock_parent
    
    def track_widget(self, widget):
        """Track a widget for cleanup"""
        if hasattr(self, 'created_widgets'):
            self.created_widgets.append(widget)
        return widget


@contextmanager
def no_gui_blocking():
    """Context manager that prevents GUI operations from blocking tests"""
    with patch('tkinter.messagebox.showinfo') as mock_showinfo, \
         patch('tkinter.messagebox.showwarning') as mock_showwarning, \
         patch('tkinter.messagebox.showerror') as mock_showerror, \
         patch('tkinter.messagebox.askquestion') as mock_askquestion, \
         patch('tkinter.messagebox.askyesno') as mock_askyesno, \
         patch('tkinter.messagebox.askokcancel') as mock_askokcancel, \
         patch('tkinter.filedialog.asksaveasfilename') as mock_saveas, \
         patch('tkinter.filedialog.askopenfilename') as mock_open, \
         patch('tkinter.filedialog.askdirectory') as mock_directory, \
         patch.object(tk.Toplevel, 'mainloop'), \
         patch.object(tk.Toplevel, 'wait_window'), \
         patch.object(tk.Toplevel, 'grab_set'), \
         patch.object(tk.Toplevel, 'grab_release'), \
         patch.object(tk.Toplevel, 'withdraw'), \
         patch.object(tk.Toplevel, 'wm_attributes'), \
         patch.object(tk.Toplevel, 'attributes'), \
         patch.object(tk.Toplevel, 'after') as mock_after, \
         patch.object(tk.Tk, 'mainloop'), \
         patch.object(tk.Tk, 'wait_window'), \
         patch.object(tk.Tk, 'after') as mock_tk_after:
        
        # Configure default return values to simulate user interactions
        mock_askquestion.return_value = 'yes'
        mock_askyesno.return_value = True
        mock_askokcancel.return_value = True
        mock_saveas.return_value = ''
        mock_open.return_value = ''
        mock_directory.return_value = ''
        
        # Mock after() methods to prevent scheduled callbacks
        mock_after.return_value = None
        mock_tk_after.return_value = None
        
        yield {
            'showinfo': mock_showinfo,
            'showwarning': mock_showwarning,
            'showerror': mock_showerror,
            'askquestion': mock_askquestion,
            'askyesno': mock_askyesno,
            'askokcancel': mock_askokcancel,
            'asksaveasfilename': mock_saveas,
            'askopenfilename': mock_open,
            'askdirectory': mock_directory,
            'after': mock_after,
            'tk_after': mock_tk_after
        }


class SafeGUITestCase(GUITestMixin, unittest.TestCase):
    """Base test case class for GUI tests with automatic cleanup and blocking prevention"""
    
    def run_gui_test(self, test_func, *args, **kwargs):
        """Run a GUI test function with proper mocking"""
        with no_gui_blocking():
            return test_func(*args, **kwargs)


def patch_gui_operations():
    """Decorator to automatically patch GUI operations for a test method"""
    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            with no_gui_blocking():
                return test_func(self, *args, **kwargs)
        return wrapper
    return decorator
