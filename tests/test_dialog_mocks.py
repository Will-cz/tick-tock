#!/usr/bin/env python3
"""
Global Test Dialog Mocking
Provides common mocking patterns for all test files to prevent popup dialogs
"""

from unittest.mock import patch, MagicMock
import contextlib

@contextlib.contextmanager
def mock_all_dialogs():
    """Context manager that mocks all popup dialogs to prevent test blocking"""
    with patch('tkinter.messagebox.showinfo') as mock_showinfo, \
         patch('tkinter.messagebox.showwarning') as mock_showwarning, \
         patch('tkinter.messagebox.showerror') as mock_showerror, \
         patch('tkinter.messagebox.askquestion') as mock_askquestion, \
         patch('tkinter.messagebox.askyesno') as mock_askyesno, \
         patch('tkinter.messagebox.askokcancel') as mock_askokcancel, \
         patch('tkinter.filedialog.asksaveasfilename') as mock_saveas, \
         patch('tkinter.filedialog.askopenfilename') as mock_open, \
         patch('tkinter.filedialog.askdirectory') as mock_directory:
        
        # Configure default return values
        mock_askquestion.return_value = 'yes'
        mock_askyesno.return_value = True
        mock_askokcancel.return_value = True
        mock_saveas.return_value = ''  # User cancels save dialog
        mock_open.return_value = ''    # User cancels open dialog  
        mock_directory.return_value = ''  # User cancels directory dialog
        
        yield {
            'showinfo': mock_showinfo,
            'showwarning': mock_showwarning, 
            'showerror': mock_showerror,
            'askquestion': mock_askquestion,
            'askyesno': mock_askyesno,
            'askokcancel': mock_askokcancel,
            'asksaveasfilename': mock_saveas,
            'askopenfilename': mock_open,
            'askdirectory': mock_directory
        }

@contextlib.contextmanager 
def mock_window_operations():
    """Context manager that mocks window operations to prevent GUI blocking"""
    with patch.object(tk.Toplevel, 'mainloop'), \
         patch.object(tk.Toplevel, 'wait_window'), \
         patch.object(tk.Toplevel, 'grab_set'), \
         patch.object(tk.Toplevel, 'grab_release'):
        yield

@contextlib.contextmanager
def mock_all_gui_operations():
    """Context manager that mocks all GUI operations and dialogs"""
    with mock_all_dialogs() as dialog_mocks, \
         mock_window_operations():
        yield dialog_mocks
