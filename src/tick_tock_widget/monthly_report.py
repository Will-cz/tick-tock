#!/usr/bin/env python3
"""
Monthly Report Window for Tick-Tock Widget
Displays monthly time tracking report in a table format
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, date
import calendar
from typing import List, Optional, Any
import colorsys
import csv
from .project_data import ProjectDataManager
from .theme_colors import ThemeColors

class MonthlyReportWindow:
    """Monthly report window with table view of project hours"""

    def __init__(self, parent_widget: Any, data_manager: ProjectDataManager, theme: Optional[ThemeColors] = None):
        self.parent_widget = parent_widget
        self.data_manager = data_manager

        # Use provided theme or default to matrix theme
        if theme is None:
            self.theme: ThemeColors = {
                'name': 'Matrix',
                'bg': '#001100',
                'fg': '#00FF00',
                'accent': '#00AA00',
                'button_bg': '#003300',
                'button_fg': '#00FF00',
                'button_active': '#004400'
            }
        else:
            self.theme = theme

        # Current view settings
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        # Window state
        self.window_closed = False

        self.window = tk.Toplevel(parent_widget.root)
        self.setup_window()
        self.create_widgets()
        self.update_report()

        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Initialize drag variables for borderless window
        self.start_x = 0
        self.start_y = 0

    def setup_window(self):
        """Setup the report window with borderless design matching main widget"""
        self.window.title(f"📊 Monthly Report - {calendar.month_name[self.current_month]} {self.current_year}")
        self.window.geometry("1500x500")  # Increased width from 1400 to 1500 for better total column fit
        self.window.configure(bg='black')  # Black background like main widget

        # Remove window decorations for consistent borderless look
        self.window.overrideredirect(True)

        # Stay on top like main widget
        self.window.attributes('-topmost', True)  # type: ignore[misc]

        # Add transparency to match main widget style
        try:
            self.window.attributes('-alpha', 0.9)  # type: ignore[misc]  # Slightly more opaque than main widget
        except tk.TclError:
            pass

        # Center on screen or near parent
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()

        # Try to position relative to parent if possible
        try:
            parent_x = self.parent_widget.root.winfo_x()
            parent_y = self.parent_widget.root.winfo_y()
            # Position to the right of parent with some offset
            x = parent_x + 500
            y = parent_y
            # Ensure window stays on screen
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            if x + 1500 > screen_width:  # Updated for new width
                x = screen_width - 1500 - 50
            if y + 500 > screen_height:  # Updated for new height
                y = screen_height - 500 - 50
            self.window.geometry(f"+{x}+{y}")
        except (tk.TclError, AttributeError):
            # If positioning relative to parent fails, center on screen
            x = (self.window.winfo_screenwidth() // 2) - 750  # Half of window width (1500/2)
            y = (self.window.winfo_screenheight() // 2) - 250  # Half of window height (500/2)
            self.window.geometry(f"+{x}+{y}")

    def create_widgets(self):
        """Create the report interface"""
        # Main frame with border effect matching main widget style
        self.main_frame = tk.Frame(
            self.window,
            bg=self.theme['bg'],
            relief='raised',
            bd=2,
            highlightbackground=self.theme['accent'],
            highlightthickness=1
        )
        self.main_frame.pack(fill='both', expand=True, padx=3, pady=3)

        # Header frame with consistent styling (more compact)
        header_frame = tk.Frame(self.main_frame, bg=self.theme['bg'])
        header_frame.pack(fill='x', pady=(0, 8))  # Reduced padding from 15 to 8

        # Title bar frame for proper layout
        title_bar_frame = tk.Frame(header_frame, bg=self.theme['bg'])
        title_bar_frame.pack(fill='x', pady=(0, 8))

        # Title label on the left
        self.title_label = tk.Label(
            title_bar_frame,
            text="📊 MONTHLY REPORT",  # Shorter title for compactness
            bg=self.theme['bg'],
            fg=self.theme['accent'],
            font=('Arial', 12, 'bold')  # Smaller font
        )
        self.title_label.pack(side='left', padx=5, pady=2)

        # Close button on the right (matching main widget style)
        close_btn = tk.Button(
            title_bar_frame,
            text="✕",
            bg='#660000',
            fg='#FF6666',
            font=('Arial', 10, 'bold'),
            bd=0,
            width=2,
            height=1,
            command=self.on_window_close,
            relief='flat'
        )
        close_btn.pack(side='right', padx=5, pady=2)

        # Top control panel with consistent spacing
        control_frame = tk.Frame(header_frame, bg=self.theme['bg'])
        control_frame.pack(fill='x')

        # Date selection group with consistent styling
        date_group_frame = tk.Frame(control_frame, bg=self.theme['bg'])
        date_group_frame.pack(side='left', padx=(0, 20))

        # Year selector with consistent styling
        year_frame = tk.Frame(date_group_frame, bg=self.theme['bg'])
        year_frame.pack(side='left', padx=(0, 10))

        tk.Label(
            year_frame,
            text="Year:",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=(0, 5))

        self.year_var = tk.StringVar(value=str(self.current_year))
        year_spinbox = tk.Spinbox(
            year_frame,
            from_=2000,
            to=2100,
            width=6,
            textvariable=self.year_var,
            command=self.on_date_changed,
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            buttonbackground=self.theme['button_bg'],
            insertbackground=self.theme['fg'],
            relief='solid',
            bd=1,
            font=('Arial', 10)
        )
        year_spinbox.pack(side='left')

        # Month selector with consistent styling
        month_frame = tk.Frame(date_group_frame, bg=self.theme['bg'])
        month_frame.pack(side='left')

        tk.Label(
            month_frame,
            text="Month:",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=(0, 5))

        # Create list of month names
        month_names = [calendar.month_name[i] for i in range(1, 13)]
        self.month_var = tk.StringVar(value=calendar.month_name[self.current_month])

        # Configure combobox style to match main widget
        style = ttk.Style()
        style.theme_use('clam')

        # Custom combobox style matching main widget
        style.configure(  # type: ignore[misc]
            'ReportMonth.TCombobox',
            background=self.theme['bg'],
            fieldbackground=self.theme['bg'],
            foreground=self.theme['fg'],
            arrowcolor=self.theme['fg'],
            selectbackground=self.theme['accent'],
            selectforeground=self.theme['fg'],
            borderwidth=1,
            relief='solid'
        )
        style.map(  # type: ignore[misc]
            'ReportMonth.TCombobox',
            fieldbackground=[('readonly', self.theme['bg']), ('active', self.theme['bg'])],
            selectbackground=[('readonly', self.theme['accent'])],
            foreground=[('readonly', self.theme['fg'])]
        )

        month_menu = ttk.Combobox(
            month_frame,
            textvariable=self.month_var,
            values=month_names,
            state='readonly',
            width=12,
            style='ReportMonth.TCombobox',
            font=('Arial', 10)
        )
        month_menu.pack(side='left')
        month_menu.bind('<<ComboboxSelected>>', lambda e: self.on_date_changed())

        # Navigation buttons matching main widget style
        nav_frame = tk.Frame(control_frame, bg=self.theme['bg'])
        nav_frame.pack(side='left', padx=(20, 0))

        prev_btn = tk.Button(
            nav_frame,
            text="◀",
            command=self.previous_month,
            bg=self.theme['button_bg'],
            fg=self.theme['button_fg'],
            activebackground=self.theme['button_active'],
            activeforeground=self.theme['button_fg'],
            relief='raised',
            bd=1,
            font=('Arial', 10, 'bold'),
            width=3,
            height=1
        )
        prev_btn.pack(side='left', padx=(0, 2))

        next_btn = tk.Button(
            nav_frame,
            text="▶",
            command=self.next_month,
            bg=self.theme['button_bg'],
            fg=self.theme['button_fg'],
            activebackground=self.theme['button_active'],
            activeforeground=self.theme['button_fg'],
            relief='raised',
            bd=1,
            font=('Arial', 10, 'bold'),
            width=3,
            height=1
        )
        next_btn.pack(side='left')

        # Export button in upper navigation area
        export_frame = tk.Frame(control_frame, bg=self.theme['bg'])
        export_frame.pack(side='left', padx=(30, 0))

        export_btn = tk.Button(
            export_frame,
            text="📄 Export",
            command=self.export_to_txt,  # Changed to txt export
            bg=self.theme['button_bg'],
            fg=self.theme['button_fg'],
            activebackground=self.theme['button_active'],
            activeforeground=self.theme['button_fg'],
            relief='raised',
            bd=1,
            font=('Arial', 10, 'bold'),
            width=8,
            height=1
        )
        export_btn.pack(side='left')

        # Separator line
        separator = tk.Frame(self.main_frame, bg=self.theme['accent'], height=2)
        separator.pack(fill='x', pady=(10, 15))

        # Table frame with consistent styling (more compact)
        table_frame = tk.Frame(self.main_frame, bg=self.theme['bg'])
        table_frame.pack(fill='both', expand=True, pady=(0, 5))  # Add small bottom padding

        # Create and configure treeview with main widget styling
        style = ttk.Style()

        # Configure main treeview style to match SubTree.Treeview
        style.configure(  # type: ignore[misc]
            "MonthlyReport.Treeview",
            background=self.theme['bg'],
            foreground=self.theme['fg'],
            fieldbackground=self.theme['bg'],
            bordercolor=self.theme['accent'],
            lightcolor=self.theme['accent'],
            darkcolor=self.theme['accent'],
            selectbackground=self.theme['accent'],
            selectforeground=self.theme['fg'],
            rowheight=22,  # Reduced from 28 to 22 for more compact rows
            font=('Arial', 8)  # Reduced from 9 to 8 for smaller text
        )

        # Configure header style to match main widget
        style.configure(  # type: ignore[misc]
            "MonthlyReport.Treeview.Heading",
            background=self.theme['button_bg'],
            foreground=self.theme['button_fg'],
            borderwidth=1,
            relief='raised',
            font=('Arial', 8, 'bold'),  # Reduced from 9 to 8 for smaller headers
            padding=(3, 5)  # Reduced padding from (5, 8) to (3, 5)
        )

        # Configure selection colors to match main widget
        style.map("MonthlyReport.Treeview",  # type: ignore[misc]
            background=[('selected', self.theme['accent'])],
            foreground=[('selected', self.theme['fg'])]
        )

        # Configure weekend column header styling
        style.configure(  # type: ignore[misc]
            "Weekend.Treeview.Heading",
            background='#D0D0D0',  # Darker grey for weekend headers
            foreground=self.theme['button_fg'],
            borderwidth=1,
            relief='raised',
            font=('Arial', 9, 'bold'),
            padding=(5, 8)
        )

        # Create scrollable frame for the table
        table_container = tk.Frame(table_frame, bg=self.theme['bg'], relief='sunken', bd=2)
        table_container.pack(fill='both', expand=True)

        # Create treeview for the report with consistent styling (compact height)
        self.tree = ttk.Treeview(
            table_container,
            style="MonthlyReport.Treeview",
            show='tree headings',  # Show both tree structure and headings
            height=20  # Reduced from 25 to 20 for more compact display
        )

        # Add scrollbars with consistent styling
        y_scrollbar = ttk.Scrollbar(table_container, orient='vertical', command=self.tree.yview)  # type: ignore[misc]
        x_scrollbar = ttk.Scrollbar(table_container, orient='horizontal', command=self.tree.xview)  # type: ignore[misc]
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Pack scrollbars and tree properly
        y_scrollbar.pack(side='right', fill='y')
        x_scrollbar.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

        # Add keyboard navigation support
        self.tree.bind('<Key>', self.on_key_press)  # type: ignore[misc]
        self.tree.bind('<Double-1>', self.on_double_click)  # type: ignore[misc]
        self.tree.focus_set()  # Allow keyboard focus

        # Make window draggable by binding to title elements
        self.title_label.bind('<Button-1>', self.start_drag)  # type: ignore[misc]
        self.title_label.bind('<B1-Motion>', self.do_drag)  # type: ignore[misc]
        header_frame.bind('<Button-1>', self.start_drag)  # type: ignore[misc]
        header_frame.bind('<B1-Motion>', self.do_drag)  # type: ignore[misc]
        title_bar_frame.bind('<Button-1>', self.start_drag)  # type: ignore[misc]
        title_bar_frame.bind('<B1-Motion>', self.do_drag)  # type: ignore[misc]

        # Bottom button frame with consistent styling
        button_frame = tk.Frame(self.main_frame, bg=self.theme['bg'])
        button_frame.pack(fill='x', pady=(15, 0))

        # Action buttons matching main widget style
        action_frame = tk.Frame(button_frame, bg=self.theme['bg'])
        action_frame.pack(side='left')

        refresh_btn = tk.Button(
            action_frame,
            text="🔄",
            command=self.update_report,
            bg=self.theme['button_bg'],
            fg=self.theme['button_fg'],
            activebackground=self.theme['button_active'],
            activeforeground=self.theme['button_fg'],
            relief='raised',
            bd=1,
            font=('Arial', 10, 'bold'),
            width=3,
            height=1
        )
        refresh_btn.pack(side='left', padx=(0, 5))

        export_btn = tk.Button(
            action_frame,
            text="�",  # Changed from 📊 to 📄 to indicate document export
            command=self.export_to_txt,  # Updated to use txt export
            bg=self.theme['button_bg'],
            fg=self.theme['button_fg'],
            activebackground=self.theme['button_active'],
            activeforeground=self.theme['button_fg'],
            relief='raised',
            bd=1,
            font=('Arial', 10, 'bold'),
            width=3,
            height=1
        )
        export_btn.pack(side='left')

        # Close button on the right
        close_btn = tk.Button(
            button_frame,
            text="❌ Close",
            command=self.on_window_close,
            bg=self.theme['button_bg'],
            fg=self.theme['button_fg'],
            activebackground=self.theme['button_active'],
            activeforeground=self.theme['button_fg'],
            relief='raised',
            bd=1,
            font=('Arial', 10, 'bold'),
            padx=15,
            height=1
        )
        close_btn.pack(side='right')

    def format_time(self, seconds: int) -> str:
        """Format seconds to HH:MM"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    def get_weekend_days(self, year: int, month: int) -> List[int]:
        """Get list of weekend days (Saturday and Sunday) for given month"""
        weekend_days: List[int] = []
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            if date(year, month, day).weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                weekend_days.append(day)
        return weekend_days

    def update_report(self):
        """Update the report view with current year/month data"""
        try:
            year = int(self.year_var.get())
            month = list(calendar.month_name).index(self.month_var.get())
        except (ValueError, TypeError):
            return

        # Update window title
        self.window.title(f"📊 Monthly Report - {calendar.month_name[month]} {year}")

        # Get days in month
        num_days = calendar.monthrange(year, month)[1]
        weekend_days = self.get_weekend_days(year, month)

        # Configure columns - like a tree view structure (optimized for better time display)
        columns = ['#0']  # Tree column for project hierarchy
        column_widths: dict[str, int] = {}

        # Add day columns with very compact width for maximum space efficiency
        for day in range(1, num_days + 1):
            col_id = f'day_{day}'
            columns.append(col_id)
            column_widths[col_id] = 40  # Reduced from 48 to 40 for maximum compactness

        # Add total column with compact width
        columns.append('total')
        column_widths['total'] = 60  # Reduced from 70 to 60 for more compact layout

        # Configure tree structure
        self.tree['columns'] = columns[1:]  # Exclude #0 as it's automatic

        # Configure tree column (#0) for project names - very compact
        self.tree.column('#0', width=130, minwidth=100, anchor='w')  # Reduced from 160 to 130
        self.tree.heading('#0', text='Project / Activity', anchor='w')

        # Configure day columns with very compact spacing
        for col in columns[1:]:
            if col == 'total':
                self.tree.column(col, width=column_widths[col], minwidth=50, anchor='center')  # Reduced minwidth
                self.tree.heading(col, text='Total', anchor='center')  # Shorter text
            else:
                day_num = int(col.split('_')[1])

                # Enhanced weekend styling with different header appearance
                if day_num in weekend_days:
                    heading_text = f"[{day_num}]"  # Brackets to indicate weekend
                    self.tree.column(col, width=column_widths[col], minwidth=35, anchor='center')  # Reduced minwidth
                    self.tree.heading(col, text=heading_text, anchor='center')
                else:
                    heading_text = f"{day_num}"  # Just day number for compactness
                    self.tree.column(col, width=column_widths[col], minwidth=35, anchor='center')  # Reduced minwidth
                    self.tree.heading(col, text=heading_text, anchor='center')

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Populate data with tree structure
        daily_totals = {f'day_{day}': 0 for day in range(1, num_days + 1)}
        grand_total_seconds = 0

        for project in self.data_manager.projects:
            project_total_seconds = 0
            project_daily_data = {f'day_{day}': 0 for day in range(1, num_days + 1)}

            # Get project time records (direct project time)
            for record_date, record in project.time_records.items():
                try:
                    record_datetime = datetime.fromisoformat(record_date)
                    if record_datetime.year == year and record_datetime.month == month:
                        day = record_datetime.day
                        day_key = f'day_{day}'
                        project_daily_data[day_key] += record.total_seconds
                        project_total_seconds += record.total_seconds
                        daily_totals[day_key] += record.total_seconds
                        grand_total_seconds += record.total_seconds
                except ValueError:
                    continue

            # ALSO include sub-activity time in project daily totals
            for sub in project.sub_activities:
                for record_date, record in sub.time_records.items():
                    try:
                        record_datetime = datetime.fromisoformat(record_date)
                        if record_datetime.year == year and record_datetime.month == month:
                            day = record_datetime.day
                            day_key = f'day_{day}'
                            project_daily_data[day_key] += record.total_seconds
                            project_total_seconds += record.total_seconds
                            # Add to global daily totals and grand total (only once here)
                            daily_totals[day_key] += record.total_seconds
                            grand_total_seconds += record.total_seconds
                    except ValueError:
                        continue

            # Prepare project values for tree structure (these now include sub-activity time)
            project_values: List[str] = []
            for day in range(1, num_days + 1):
                day_key = f'day_{day}'
                day_seconds = project_daily_data[day_key]
                if day_seconds > 0:
                    project_values.append(self.format_time(day_seconds))
                else:
                    project_values.append('')

            # Add total time
            project_values.append(self.format_time(project_total_seconds))

            # Insert project as parent item with enhanced styling showing daily sums
            project_text = f"📁 {project.alias}"
            project_item = self.tree.insert(
                '', 'end',
                text=project_text,
                values=project_values,
                open=False  # Start collapsed
            )

            # Add "General" activity as first child showing direct project time (excluding sub-activities)
            general_total_seconds = 0
            general_daily_data = {f'day_{day}': 0 for day in range(1, num_days + 1)}

            # Calculate direct project time (only project-level time records)
            for record_date, record in project.time_records.items():
                try:
                    record_datetime = datetime.fromisoformat(record_date)
                    if record_datetime.year == year and record_datetime.month == month:
                        day = record_datetime.day
                        day_key = f'day_{day}'
                        general_daily_data[day_key] += record.total_seconds
                        general_total_seconds += record.total_seconds
                except ValueError:
                    continue

            # Prepare general activity values
            general_values: List[str] = []
            for day in range(1, num_days + 1):
                day_key = f'day_{day}'
                day_seconds = general_daily_data[day_key]
                if day_seconds > 0:
                    general_values.append(self.format_time(day_seconds))
                else:
                    general_values.append('')

            # Add total time for general activity
            general_values.append(self.format_time(general_total_seconds))

            # Insert "General" activity as first child
            general_text = "  ⚡ General"
            self.tree.insert(
                project_item, 'end',
                text=general_text,
                values=general_values
            )

            # Add sub-activities as children
            for sub in project.sub_activities:
                sub_total_seconds = 0
                sub_daily_data = {f'day_{day}': 0 for day in range(1, num_days + 1)}

                # Get sub-activity time records
                for record_date, record in sub.time_records.items():
                    try:
                        record_datetime = datetime.fromisoformat(record_date)
                        if record_datetime.year == year and record_datetime.month == month:
                            day = record_datetime.day
                            day_key = f'day_{day}'
                            sub_daily_data[day_key] += record.total_seconds
                            sub_total_seconds += record.total_seconds
                            # Don't double-count: daily_totals and grand_total were already updated above
                    except ValueError:
                        continue

                # Prepare sub-activity values
                sub_values: List[str] = []
                for day in range(1, num_days + 1):
                    day_key = f'day_{day}'
                    day_seconds = sub_daily_data[day_key]
                    if day_seconds > 0:
                        sub_values.append(self.format_time(day_seconds))
                    else:
                        sub_values.append('')

                # Add total time
                sub_values.append(self.format_time(sub_total_seconds))

                # Insert sub-activity as child with distinct styling
                sub_text = f"  ⚡ {sub.alias}"
                self.tree.insert(
                    project_item, 'end',
                    text=sub_text,
                    values=sub_values
                )

        # Add daily totals row as a special summary item
        total_values: List[str] = []
        for day in range(1, num_days + 1):
            day_key = f'day_{day}'
            day_total = daily_totals[day_key]
            if day_total > 0:
                total_values.append(self.format_time(day_total))
            else:
                total_values.append('')
        total_values.append(self.format_time(grand_total_seconds))

        # Insert totals row with special styling
        totals_item = self.tree.insert(
            '', 'end',
            text="📊 DAILY TOTALS",
            values=total_values
        )

        # Apply special styling for totals row
        try:
            self.tree.set(totals_item, 'total', f"🕐 {self.format_time(grand_total_seconds)}")
        except (tk.TclError, AttributeError):
            pass

        # Style weekend columns with better visual distinction
        self.style_weekend_columns(weekend_days, year, month)

    def on_date_changed(self):
        """Handle date selection change"""
        if not self.window_closed:
            # Update window title with new date
            try:
                year = int(self.year_var.get())
                month = list(calendar.month_name).index(self.month_var.get())
                self.window.title(f"Monthly Report - {calendar.month_name[month]} {year}")
                self.current_year = year
                self.current_month = month
            except (ValueError, TypeError):
                pass
            self.update_report()

    def previous_month(self):
        """Navigate to previous month"""
        try:
            current_month = list(calendar.month_name).index(self.month_var.get())
            current_year = int(self.year_var.get())

            if current_month == 1:
                new_month = 12
                new_year = current_year - 1
            else:
                new_month = current_month - 1
                new_year = current_year

            self.month_var.set(calendar.month_name[new_month])
            self.year_var.set(str(new_year))
            self.on_date_changed()
        except (ValueError, TypeError):
            pass

    def next_month(self):
        """Navigate to next month"""
        try:
            current_month = list(calendar.month_name).index(self.month_var.get())
            current_year = int(self.year_var.get())

            if current_month == 12:
                new_month = 1
                new_year = current_year + 1
            else:
                new_month = current_month + 1
                new_year = current_year

            self.month_var.set(calendar.month_name[new_month])
            self.year_var.set(str(new_year))
            self.on_date_changed()
        except (ValueError, TypeError):
            pass

    def on_key_press(self, event: Any) -> None:
        """Handle keyboard navigation"""
        if event.keysym == 'Left':
            self.previous_month()
        elif event.keysym == 'Right':
            self.next_month()
        elif event.keysym == 'Escape':
            self.on_window_close()
        elif event.keysym == 'F5':
            self.update_report()

    def on_double_click(self, _event: Any) -> None:
        """Handle double-click on tree items"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            # Toggle item expansion
            if self.tree.get_children(item):
                if self.tree.item(item)['open']:
                    self.tree.item(item, open=False)
                else:
                    self.tree.item(item, open=True)

    def style_weekend_columns(self, weekend_days: List[int], year: int, month: int):
        """Apply weekend styling to columns - weekends are indicated by brackets in headers"""
        # Weekend styling is now handled through the column header text formatting
        # Weekend columns show day numbers in brackets: [1], [2] vs regular: 1, 2

    def update_theme(self, new_theme: ThemeColors):
        """Update the window theme to match main widget"""
        self.theme = new_theme

        try:
            # Update window background
            self.window.configure(bg=self.theme['bg'])

            # Update all frames and labels
            def update_widget_theme(widget: Any) -> None:
                try:
                    widget_type: str = widget.winfo_class()  # type: ignore[misc]

                    if widget_type == 'Frame':
                        widget.configure(bg=self.theme['bg'])  # type: ignore[misc]
                    elif widget_type == 'Label':
                        widget.configure(bg=self.theme['bg'], fg=self.theme['fg'])  # type: ignore[misc]
                    elif widget_type == 'Button':
                        widget.configure(  # type: ignore[misc]
                            bg=self.theme['button_bg'],
                            fg=self.theme['button_fg'],
                            activebackground=self.theme['button_active'],
                            activeforeground=self.theme['button_fg']
                        )
                    elif widget_type == 'Spinbox':
                        widget.configure(  # type: ignore[misc]
                            bg=self.theme['bg'],
                            fg=self.theme['fg'],
                            buttonbackground=self.theme['button_bg'],
                            insertbackground=self.theme['fg']
                        )

                    # Recursively update children
                    for child in widget.winfo_children():  # type: ignore[misc]
                        update_widget_theme(child)

                except (tk.TclError, AttributeError):
                    pass

            # Update all widgets
            update_widget_theme(self.window)

            # Update TTK styles
            style = ttk.Style()

            # Update month combobox style
            style.configure(  # type: ignore[misc]
                'ReportMonth.TCombobox',
                background=self.theme['bg'],
                fieldbackground=self.theme['bg'],
                foreground=self.theme['fg'],
                arrowcolor=self.theme['fg'],
                selectbackground=self.theme['accent'],
                selectforeground=self.theme['fg']
            )
            style.map(  # type: ignore[misc]
                'ReportMonth.TCombobox',
                fieldbackground=[('readonly', self.theme['bg'])],
                selectbackground=[('readonly', self.theme['accent'])],
                foreground=[('readonly', self.theme['fg'])]
            )

            # Update treeview style
            style.configure(  # type: ignore[misc]
                "MonthlyReport.Treeview",
                background=self.theme['bg'],
                foreground=self.theme['fg'],
                fieldbackground=self.theme['bg'],
                bordercolor=self.theme['accent'],
                lightcolor=self.theme['accent'],
                darkcolor=self.theme['accent'],
                selectbackground=self.theme['accent'],
                selectforeground=self.theme['fg']
            )

            style.configure(  # type: ignore[misc]
                "MonthlyReport.Treeview.Heading",
                background=self.theme['button_bg'],
                foreground=self.theme['button_fg']
            )

            style.map("MonthlyReport.Treeview",  # type: ignore[misc]
                background=[('selected', self.theme['accent'])],
                foreground=[('selected', self.theme['fg'])]
            )

        except (tk.TclError, AttributeError):
            # If theme update fails, continue silently
            pass

    def export_to_txt(self):
        """Export current monthly report to text file with tab indentation structure"""
        try:
            # Get current year and month
            year = int(self.year_var.get())
            month = list(calendar.month_name).index(self.month_var.get())

            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Monthly Report",
                initialfile=f"monthly_report_{calendar.month_name[month]}_{year}.txt"
            )

            if not filename:
                return

            self._export_txt(filename, year, month)

        except (OSError, ValueError, tk.TclError) as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")

    def _export_txt(self, filename: str, year: int, month: int) -> None:
        """Export to text format with improved column alignment and clarity"""
        # Get days in month and weekend days
        num_days = calendar.monthrange(year, month)[1]
        weekend_days = self.get_weekend_days(year, month)

        with open(filename, 'w', encoding='utf-8') as txtfile:
            # Write header
            txtfile.write("MONTHLY TIME TRACKING REPORT\n")
            txtfile.write(f"{calendar.month_name[month]} {year}\n")
            txtfile.write("=" * 100 + "\n\n")

            # Create header with fixed-width columns for better alignment
            header_line = "Project / Activity".ljust(25)

            # Add day columns with fixed width and clear separators
            for day in range(1, num_days + 1):
                if day in weekend_days:
                    day_header = f"[{day}]".center(8)  # Weekend days with brackets, centered in 8 chars
                else:
                    day_header = f"{day}".center(8)    # Regular days, centered in 8 chars
                header_line += "| " + day_header + " "

            # Add total column
            header_line += "| " + "Total".center(8) + " |\n"
            txtfile.write(header_line)

            # Write separator line with column dividers
            separator_line = "-" * 25  # Project name column
            for day in range(1, num_days + 1):
                separator_line += "+-" + "-" * 8 + "-"  # Day columns with separators
            separator_line += "+-" + "-" * 8 + "-+\n"  # Total column
            txtfile.write(separator_line)

            # Export data from the tree view
            for item in self.tree.get_children():
                self._write_txt_item_and_children(txtfile, item, 0, num_days)

            # Write footer separator
            txtfile.write(separator_line)
            txtfile.write("\n" + "=" * 100 + "\n")
            txtfile.write(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            txtfile.write("Legend: [day] = Weekend, regular numbers = Workdays\n")

        messagebox.showinfo("Export Successful", f"Monthly report exported to text file:\n{filename}")

    def _write_txt_item_and_children(self, txtfile: Any, item: Any, indent_level: int, num_days: int) -> None:
        """Write tree item and its children to text file with improved column alignment"""
        # Get item data
        item_text = self.tree.item(item)['text']

        # Create indentation using spaces for better control
        indent = "  " * indent_level
        project_name = (indent + item_text)[:24]  # Truncate if too long, reserve space for indentation

        # Start line with fixed-width project name column
        line = project_name.ljust(25)

        # Write time data for each day with fixed-width columns and separators
        for col in self.tree['columns']:
            if col != 'total':
                value = self.tree.set(item, col)
                # Format time value to fit in 8 characters, centered
                time_str = str(value if value else "-").center(8)
                line += "| " + time_str + " "

        # Write total with separator
        total_value = self.tree.set(item, 'total')
        total_str = str(total_value if total_value else "-").center(8)
        line += "| " + total_str + " |\n"

        txtfile.write(line)

        # Write children recursively with increased indentation
        for child in self.tree.get_children(item):
            self._write_txt_item_and_children(txtfile, child, indent_level + 1, num_days)

    def _export_csv(self, filename: str, year: int, month: int) -> None:
        """Export to CSV format as fallback"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header with month/year info
            writer.writerow([f"Monthly Time Tracking Report - {calendar.month_name[month]} {year}"])
            writer.writerow([])  # Empty row

            # Write column headers
            headers = ['Project/Activity']

            for col in self.tree['columns']:
                if col == 'total':
                    headers.append('Total Hours')
                else:
                    day_num = int(col.split('_')[1])
                    weekday = date(year, month, day_num).strftime('%a')
                    headers.append(f"{day_num} ({weekday})")

            writer.writerow(headers)

            # Write data
            def write_item_and_children(item: Any, indent_level: int = 0) -> None:
                # Get item text and values
                item_text = self.tree.item(item)['text']  # type: ignore[misc]
                indent = "  " * indent_level
                row = [indent + item_text]

                for col in self.tree['columns']:
                    row.append(self.tree.set(item, col))  # type: ignore[misc]

                writer.writerow(row)

                # Write children recursively
                for child in self.tree.get_children(item):
                    write_item_and_children(child, indent_level + 1)

            # Write all top-level items and their children
            for item in self.tree.get_children():
                write_item_and_children(item)

        messagebox.showinfo("Export Successful", f"Report exported to CSV:\n{filename}")

    def on_window_close(self):
        """Handle window close event"""
        self.window_closed = True
        try:
            # Notify parent widget that this window is closing
            if hasattr(self.parent_widget, 'close_monthly_report'):
                self.parent_widget.close_monthly_report()
            else:
                self.window.destroy()
        except (tk.TclError, AttributeError):
            # Fallback - just destroy the window
            try:
                self.window.destroy()
            except tk.TclError:
                pass

    def _adjust_color(self, hex_color: str, lightness_factor: float = 1.0) -> str:
        """Adjust color lightness"""
        try:
            # Convert hex to RGB
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

            # Convert to HSL
            rgb_normalized = [x/255.0 for x in rgb]
            h, l, s = colorsys.rgb_to_hls(*rgb_normalized)

            # Adjust lightness
            l = max(0, min(1, l * lightness_factor))

            # Convert back to RGB
            rgb_adjusted = colorsys.hls_to_rgb(h, l, s)
            rgb_denormalized = tuple(int(x * 255) for x in rgb_adjusted)

            # Convert to hex
            return f'#{rgb_denormalized[0]:02x}{rgb_denormalized[1]:02x}{rgb_denormalized[2]:02x}'
        except (ValueError, TypeError, ZeroDivisionError):
            # Return original color if conversion fails
            return hex_color

    def show(self):
        """Show the report window"""
        if not self.window_closed:
            try:
                self.window.deiconify()
                self.window.lift()  # type: ignore[misc]
                self.window.focus_set()
            except tk.TclError:
                pass

    def start_drag(self, event: Any) -> None:
        """Start dragging the borderless window"""
        self.start_x = event.x_root
        self.start_y = event.y_root

    def do_drag(self, event: Any) -> None:
        """Drag the borderless window"""
        x = self.window.winfo_x() + (event.x_root - self.start_x)
        y = self.window.winfo_y() + (event.y_root - self.start_y)
        self.window.geometry(f"+{x}+{y}")
        self.start_x = event.x_root
        self.start_y = event.y_root

    def destroy(self):
        """Destroy the report window"""
        self.window_closed = True
        try:
            self.window.destroy()
        except tk.TclError:
            pass
