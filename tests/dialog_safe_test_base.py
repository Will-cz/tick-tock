#!/usr/bin/env python3
"""
Dialog-Safe Test Base Class
Provides a base test class that automatically mocks all popup dialogs
"""

import unittest
import tkinter as tk
from unittest.mock import patch
from contextlib import contextmanager


class DialogSafeTestCase(unittest.TestCase):
    """Base test class that automatically mocks all popup dialogs"""
    
    @contextmanager
    def no_dialogs(self):
        """Context manager that mocks all popup dialogs and window operations"""
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
             patch.object(tk.Toplevel, 'grab_release'):
            
            # Configure default return values to simulate user interactions
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
    
    @contextmanager
    def no_dialogs_export_file(self, export_filename):
        """Context manager that mocks dialogs and sets a specific export filename"""
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
             patch.object(tk.Toplevel, 'grab_release'):
            
            # Configure return values for export testing
            mock_askquestion.return_value = 'yes'
            mock_askyesno.return_value = True
            mock_askokcancel.return_value = True
            mock_saveas.return_value = export_filename  # Use provided filename
            mock_open.return_value = ''
            mock_directory.return_value = ''
            
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
