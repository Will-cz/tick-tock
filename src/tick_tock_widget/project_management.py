#!/usr/bin/env python3
# pylint: disable=too-many-lines
"""
Project Management Window for Tick-Tock Widget
Handles project and sub-activity management with tree view interface
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any


class ProjectManagementWindow:
    """Project management sub-window with tree view and editing capabilities"""

    def __init__(self, parent_widget: Any, data_manager: Any,
                 on_update_callback: Optional[Callable[[], None]] = None,
                 theme: Optional[dict[str, Any]] = None):
        try:
            self.parent_widget = parent_widget
            self.data_manager = data_manager
            self.on_update_callback = on_update_callback
            # Use provided theme or default to matrix theme
            self.theme = theme if theme else {
                'name': 'Matrix', 'bg': '#001100', 'fg': '#00FF00', 'accent': '#00AA00'
            }

            # Track open dialogs for theme updates
            self.open_dialogs: list[Any] = []

            # Initialize dragging attributes
            self.start_x = 0
            self.start_y = 0

            self.window = tk.Toplevel(parent_widget.root)
            self.setup_window()
            self.create_widgets()
            self.populate_projects()
        except (tk.TclError, AttributeError, ValueError) as e:
            print(f"Error initializing project management window: {e}")
            # Ensure we have basic attributes even if initialization fails
            if not hasattr(self, 'parent_widget'):
                self.parent_widget = parent_widget
            if not hasattr(self, 'data_manager'):
                self.data_manager = data_manager
            if not hasattr(self, 'on_update_callback'):
                self.on_update_callback = on_update_callback
            if not hasattr(self, 'theme'):
                self.theme = theme if theme else {
                    'name': 'Matrix', 'bg': '#001100', 'fg': '#00FF00', 'accent': '#00AA00'
                }
            if not hasattr(self, 'open_dialogs'):
                self.open_dialogs: list[Any] = []
            # Don't create window on error to avoid further issues

    def update_theme(self, new_theme: dict[str, str]) -> None:
        """Update the theme of the project management window"""
        self.theme = new_theme

        # Update window background
        self.window.configure(bg=self.theme['bg'])

        # Apply theme to all widgets recursively
        self._apply_theme_to_children(self.window)

        # Update any open dialogs
        for dialog in self.open_dialogs[:]:  # Use slice copy to avoid modification during iteration
            try:
                if hasattr(dialog, 'dialog') and dialog.dialog.winfo_exists():
                    dialog.update_theme(new_theme)
                else:
                    # Remove dead dialogs from tracking
                    self.open_dialogs.remove(dialog)
            except tk.TclError:
                # Remove dead dialogs from tracking
                if dialog in self.open_dialogs:
                    self.open_dialogs.remove(dialog)

    def _apply_theme_to_children(self, parent: Any) -> None:
        """Apply current theme to all child widgets"""
        for child in parent.winfo_children():
            widget_class = child.winfo_class()

            if widget_class == 'Frame':
                child.configure(bg=self.theme['bg'])
                self._apply_theme_to_children(child)
            elif widget_class == 'Labelframe':
                try:
                    child.configure(bg=self.theme['bg'], fg=self.theme['fg'])
                    self._apply_theme_to_children(child)
                except tk.TclError:
                    pass
            elif widget_class in ['Label']:
                try:
                    if str(child['text']) in ['✕']:
                        child.configure(bg='#660000', fg='#FF6666')
                    else:
                        child.configure(bg=self.theme['bg'], fg=self.theme['fg'])
                except tk.TclError:
                    pass
            elif widget_class in ['Button']:
                try:
                    if str(child['text']) in ['✕']:
                        child.configure(bg='#660000', fg='#FF6666')
                    else:
                        child.configure(
                            bg=self.theme.get('button_bg', self.theme['accent']),
                            fg=self.theme.get('button_fg', self.theme['bg']),
                            activebackground=self.theme.get('button_active', self.theme['fg']),
                            activeforeground=self.theme.get('button_fg', self.theme['bg'])
                        )
                except tk.TclError:
                    pass
            elif widget_class == 'Entry':
                try:
                    child.configure(
                        bg=self.theme['bg'],
                        fg=self.theme['fg'],
                        insertbackground=self.theme['fg']
                    )
                except tk.TclError:
                    pass
            elif widget_class == 'Treeview':
                try:
                    style = ttk.Style()
                    style.configure(  # type: ignore[misc]
                        "Themed.Treeview",
                        background=self.theme['bg'],
                        foreground=self.theme['fg'],
                        fieldbackground=self.theme['bg'],
                        borderwidth=1,
                        relief='solid'
                    )
                    style.configure(  # type: ignore[misc]
                        "Themed.Treeview.Heading",
                        background=self.theme['accent'],
                        foreground=self.theme['bg'],
                        relief='flat'
                    )
                    child.configure(style="Themed.Treeview")
                except (tk.TclError, AttributeError):
                    pass
            elif widget_class == 'Scrollbar':
                try:
                    child.configure(
                        bg=self.theme['bg'],
                        troughcolor=self.theme['bg'],
                        activebackground=self.theme['accent'],
                        highlightbackground=self.theme['bg']
                    )
                except tk.TclError:
                    pass
            # Apply theme to child widgets recursively
            self._apply_theme_to_children(child)

    def setup_window(self):
        """Setup the project management window"""
        self.window.title("Project Management")
        self.window.geometry("600x560")  # Increased height to accommodate all elements
        self.window.configure(bg=self.theme['bg'])
        self.window.attributes('-topmost', True)  # type: ignore[misc]

        # Remove window decorations for consistency with main window
        self.window.overrideredirect(True)

        # Center on parent
        parent_x = self.parent_widget.root.winfo_x()
        parent_y = self.parent_widget.root.winfo_y()
        self.window.geometry(f"+{parent_x + 50}+{parent_y + 50}")

        # Setup dragging for title bar
        self.setup_dragging()

    def setup_dragging(self) -> None:
        """Setup window dragging functionality"""
        def start_drag(event: Any) -> None:
            self.start_x = event.x
            self.start_y = event.y

        def on_drag(event: Any) -> None:
            x = self.window.winfo_x() + event.x - self.start_x
            y = self.window.winfo_y() + event.y - self.start_y
            self.window.geometry(f"+{x}+{y}")

        # Bind to title frame for dragging
        def bind_dragging_to_frame():
            for child in self.window.winfo_children():
                if isinstance(child, tk.Frame) and hasattr(child, 'pack_info'):
                    info = child.pack_info()
                    if info and 'fill' in info and info['fill'] == 'x':  # Title frame
                        child.bind("<Button-1>", start_drag)
                        child.bind("<B1-Motion>", on_drag)
                        # Also bind to title label
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Label):
                                grandchild.bind("<Button-1>", start_drag)
                                grandchild.bind("<B1-Motion>", on_drag)
                        break

        # Schedule the binding after widgets are created
        self.window.after(100, bind_dragging_to_frame)

    def create_widgets(self):
        """Create the project management interface"""
        # Custom title bar with close button
        title_frame = tk.Frame(self.window, bg=self.theme['bg'], height=40, relief='raised', bd=2)
        title_frame.pack(fill='x', padx=2, pady=2)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="📊 Project Management",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 14, 'bold')
        ).pack(side='left', padx=10, pady=5)

        # Close button
        tk.Button(
            title_frame,
            text="✕",
            bg='#660000',
            fg='#FF6666',
            font=('Arial', 10, 'bold'),
            command=self.window.destroy,
            relief='flat',
            bd=0,
            width=2,
            height=1
        ).pack(side='right', padx=5, pady=5)

        # Main content frame
        main_frame = tk.Frame(self.window, bg=self.theme['bg'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Projects tree view
        tree_frame = tk.Frame(main_frame, bg=self.theme['bg'])
        tree_frame.pack(fill='both', expand=True, pady=5)

        tk.Label(
            tree_frame,
            text="Projects & Sub-Activities:",
            bg=self.theme['bg'],
            fg=self.theme['accent'],
            font=('Arial', 10, 'bold')
        ).pack(anchor='w')

        # Create treeview with scrollbar
        tree_container = tk.Frame(tree_frame, bg=self.theme['bg'])
        tree_container.pack(fill='both', expand=True, pady=5)

        # Configure treeview style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(  # type: ignore[misc]
            "Custom.Treeview",
            background=self.theme['bg'],
            foreground=self.theme['fg'],
            fieldbackground=self.theme['bg'],
            bordercolor=self.theme['accent'],
            lightcolor=self.theme['accent'],
            darkcolor=self.theme['accent']
        )
        style.configure(  # type: ignore[misc]
            "Custom.Treeview.Heading",
            background=self.theme['bg'],
            foreground=self.theme['fg'],
            bordercolor=self.theme['accent']
        )

        self.tree = ttk.Treeview(
            tree_container,
            style="Custom.Treeview",
            columns=('dz_number', 'name', 'total_time'),
            show='tree headings',
            height=15
        )

        # Configure columns
        self.tree.column('#0', width=150, minwidth=100)
        self.tree.column('dz_number', width=80, minwidth=60)
        self.tree.column('name', width=200, minwidth=150)
        self.tree.column('total_time', width=80, minwidth=70)

        # Configure headings
        self.tree.heading('#0', text='Alias', anchor='w')
        self.tree.heading('dz_number', text='DZ #', anchor='center')
        self.tree.heading('name', text='Full Name', anchor='w')
        self.tree.heading('total_time', text='Total', anchor='center')

        # Add scrollbar
        scrollbar = tk.Scrollbar(
            tree_container,
            orient='vertical',
            command=self.tree.yview,  # type: ignore[misc]
            bg='#002200',  # Darker background
            troughcolor='#001100',  # Very dark trough
            activebackground='#00FF00',  # Bright green when active
            highlightbackground='#001100',
            highlightcolor='#00AA00',
            elementborderwidth=1,
            borderwidth=2,
            relief='raised',
            width=16  # Slightly wider for better visibility
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind events
        self.tree.bind('<Double-1>', self.on_item_double_click)

        # Control buttons - framed sections with full width layout
        button_frame = tk.Frame(main_frame, bg=self.theme['bg'])
        button_frame.pack(fill='x', pady=10)

        # Left side - Project actions with prominent frame
        left_frame = tk.LabelFrame(
            button_frame,
            text="Project",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 9, 'bold'),
            relief='raised',
            bd=2,
            highlightbackground=self.theme['accent'],
            highlightthickness=1
        )
        left_frame.pack(side='left', fill='x', expand=True, padx=(5, 10), pady=5)

        tk.Button(
            left_frame,
            text="➕ Add",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            command=self.add_project,
            width=12,
            pady=4
        ).pack(side='left', fill='x', expand=True, padx=3, pady=8)

        tk.Button(
            left_frame,
            text="✏️ Edit",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            command=self.edit_project,
            width=12,
            pady=4
        ).pack(side='left', fill='x', expand=True, padx=3, pady=8)

        tk.Button(
            left_frame,
            text="🗑️ Delete",
            bg='#330000',
            fg='#FF6666',
            font=('Arial', 8),
            command=self.delete_project,
            width=12,
            pady=4
        ).pack(side='left', fill='x', expand=True, padx=3, pady=8)

        # Right side - Activity actions with prominent frame
        right_frame = tk.LabelFrame(
            button_frame,
            text="Activity",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 9, 'bold'),
            relief='raised',
            bd=2,
            highlightbackground=self.theme['accent'],
            highlightthickness=1
        )
        right_frame.pack(side='right', fill='x', expand=True, padx=(10, 5), pady=5)

        tk.Button(
            right_frame,
            text="➕ Add",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            command=self.add_sub_activity,
            width=12,
            pady=4
        ).pack(side='left', fill='x', expand=True, padx=3, pady=8)

        tk.Button(
            right_frame,
            text="✏️ Edit",
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            command=self.edit_sub_activity,
            width=12,
            pady=4
        ).pack(side='left', fill='x', expand=True, padx=3, pady=8)

        tk.Button(
            right_frame,
            text="🗑️ Delete",
            bg='#330000',
            fg='#FF6666',
            font=('Arial', 8),
            command=self.delete_sub_activity,
            width=12,
            pady=4
        ).pack(side='left', fill='x', expand=True, padx=3, pady=8)

        # Export button and status bar row - export moved to monthly report
        bottom_frame = tk.Frame(main_frame, bg=self.theme['bg'])
        bottom_frame.pack(fill='x', pady=(2, 5))

        # Status label on the left
        self.status_label = tk.Label(
            bottom_frame,
            text="Ready",
            bg=self.theme['bg'],
            fg=self.theme['accent'],
            font=('Arial', 9),
            anchor='w'
        )
        self.status_label.pack(side='left', padx=5)

    def populate_projects(self):
        """Populate the tree view with projects and sub-activities"""
        try:
            # Clear existing items
            if hasattr(self, 'tree'):
                for item in self.tree.get_children():
                    self.tree.delete(item)

            # Handle case where data_manager.projects might be None (mocks)
            if not hasattr(self.data_manager, 'projects') or self.data_manager.projects is None:
                return

            # Add projects
            for project in self.data_manager.projects:
                # Calculate total time (sum all days)
                total_seconds = sum(
                    record.total_seconds for record in project.time_records.values()
                )
                total_time = self.format_time(total_seconds)

                project_item = self.tree.insert(
                    '',
                    'end',
                    text=f"📁 {project.alias}",
                    values=(
                        project.dz_number,
                        project.name,
                        total_time
                    ),
                    tags=('project',)
                )

                # Add sub-activities
                for sub_activity in project.sub_activities:
                    # Calculate total time for sub-activity
                    sub_total_seconds = sum(
                        record.total_seconds for record in sub_activity.time_records.values()
                    )
                    sub_total_time = self.format_time(sub_total_seconds)

                    self.tree.insert(
                        project_item,
                        'end',
                        text=f"  📄 {sub_activity.name}",
                        values=(
                            "",  # No DZ number for sub-activities
                            "",  # No full name needed - it's shown in the tree column
                            sub_total_time
                        ),
                        tags=('sub_activity',)
                    )

                # Expand project by default
                self.tree.item(project_item, open=True)

            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Loaded {len(self.data_manager.projects)} projects")
        except (AttributeError, TypeError, ValueError) as e:
            print(f"Error populating projects: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Error loading projects")

    def format_time(self, total_seconds: int) -> str:
        """Format seconds to HH:MM:SS"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def on_item_double_click(self, event: Any) -> None:  # pylint: disable=unused-argument
        """Handle double-click on tree item"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        item_text = self.tree.item(item, 'text')

        if '📁' in item_text:  # Project
            project_alias = item_text.replace('📁 ', '')
            self.data_manager.set_current_project(project_alias)
            self.status_label.config(text=f"Selected project: {project_alias}")
            if self.on_update_callback:
                self.on_update_callback()
        elif '📄' in item_text:  # Sub-activity
            sub_alias = item_text.replace('  📄 ', '')
            # Get parent project
            parent = self.tree.parent(item)
            if parent:
                parent_text = self.tree.item(parent, 'text')
                project_alias = parent_text.replace('📁 ', '')
                self.data_manager.set_current_project(project_alias)
                # Find sub-activity by name
                project = self.data_manager.get_project(project_alias)
                if project:
                    for sub in project.sub_activities:
                        if sub.name == sub_alias:
                            self.data_manager.set_current_sub_activity(sub.alias)
                            break
                self.status_label.config(text=f"Selected: {project_alias} -> {sub_alias}")
                if self.on_update_callback:
                    self.on_update_callback()

    def add_project(self):
        """Add a new project using widget dialog"""
        dialog = ProjectEditDialog(self.window, "New Project", theme=self.theme)
        self.open_dialogs.append(dialog)
        result = dialog.show()

        if result:
            name, dz_number, alias = result
            if self.data_manager.add_project(name, dz_number, alias):
                self.populate_projects()
                self.status_label.config(text=f"Added project: {alias}")
                if self.on_update_callback:
                    self.on_update_callback()
            else:
                # Show error dialog
                error_dialog = MessageDialog(
                    self.window, "Error", f"Project '{alias}' already exists!"
                )
                error_dialog.show()

    def edit_project(self):
        """Edit selected project using widget dialog"""
        selection = self.tree.selection()
        if not selection:
            dialog = MessageDialog(self.window, "Warning", "Please select a project first!")
            dialog.show()
            return

        item = selection[0]
        item_text = self.tree.item(item, 'text')

        if '📁' not in item_text:
            dialog = MessageDialog(self.window, "Warning", "Please select a project!")
            dialog.show()
            return

        project_alias = item_text.replace('📁 ', '')
        project = self.data_manager.get_project(project_alias)
        if not project:
            dialog = MessageDialog(self.window, "Error", f"Project '{project_alias}' not found!")
            dialog.show()
            return

        # Open edit dialog with current values
        dialog = ProjectEditDialog(
            self.window,
            "Edit Project",
            initial_name=project.name,
            initial_dz=project.dz_number,
            initial_alias=project.alias,
            theme=self.theme
        )
        result = dialog.show()

        if result:
            name, dz_number, alias = result
            # Update project details
            project.name = name
            project.dz_number = dz_number
            if alias != project.alias:
                # Handle alias change if needed
                project.alias = alias

            self.populate_projects()
            self.status_label.config(text=f"Updated project: {alias}")
            if self.on_update_callback:
                self.on_update_callback()

    def delete_project(self):
        """Delete selected project"""
        selection = self.tree.selection()
        if not selection:
            dialog = MessageDialog(self.window, "Warning", "Please select a project to delete!")
            dialog.show()
            return

        item = selection[0]
        item_text = self.tree.item(item, 'text')

        if '📁' not in item_text:
            dialog = MessageDialog(self.window, "Warning", "Please select a project!")
            dialog.show()
            return

        project_alias = item_text.replace('📁 ', '')

        # Confirm deletion
        dialog = ConfirmDialog(
            self.window, "Confirm Delete", f"Delete project '{project_alias}' and all its data?"
        )
        result = dialog.show()

        if result:
            if self.data_manager.remove_project(project_alias):
                self.populate_projects()
            self.status_label.config(text=f"Deleted project: {project_alias}")
            if self.on_update_callback:
                self.on_update_callback()
        else:
            dialog = MessageDialog(
                self.window, "Error", f"Failed to delete project '{project_alias}'!"
            )
            dialog.show()

    def export_data(self):
        """Export data (placeholder method)"""
        dialog = MessageDialog(self.window, "Info", "Export functionality not yet implemented")
        dialog.show()

    def add_sub_activity(self):
        """Add a new sub-activity to selected project using widget dialog"""
        # Get selected project
        selection = self.tree.selection()
        if not selection:
            dialog = MessageDialog(self.window, "Warning", "Please select a project first!")
            dialog.show()
            return

        item = selection[0]
        item_text = self.tree.item(item, 'text')

        # Ensure we have a project selected
        if '📁' not in item_text:
            parent = self.tree.parent(item)
            if parent:
                item_text = self.tree.item(parent, 'text')
            else:
                dialog = MessageDialog(self.window, "Warning", "Please select a project!")
                dialog.show()
                return

        project_alias = item_text.replace('📁 ', '')
        project = self.data_manager.get_project(project_alias)
        if not project:
            dialog = MessageDialog(self.window, "Error", f"Project '{project_alias}' not found!")
            dialog.show()
            return

        # Show dialog
        dialog = SubActivityEditDialog(
            self.window, f"New Sub-Activity for '{project_alias}'", theme=self.theme
        )
        result = dialog.show()

        if result:
            name, alias = result
            project.add_sub_activity(name, alias)
            self.populate_projects()
            self.status_label.config(text=f"Added sub-activity: {alias} to {project_alias}")
            if self.on_update_callback:
                self.on_update_callback()

    def edit_sub_activity(self):
        """Edit selected sub-activity using widget dialog"""
        selection = self.tree.selection()
        if not selection:
            dialog = MessageDialog(self.window, "Warning", "Please select a sub-activity first!")
            dialog.show()
            return

        item = selection[0]
        item_text = self.tree.item(item, 'text')

        if '📄' not in item_text:
            dialog = MessageDialog(self.window, "Warning", "Please select a sub-activity!")
            dialog.show()
            return

        sub_name = item_text.replace('  📄 ', '')
        parent = self.tree.parent(item)
        if not parent:
            return

        parent_text = self.tree.item(parent, 'text')
        project_alias = parent_text.replace('📁 ', '')
        project = self.data_manager.get_project(project_alias)
        if not project:
            return

        # Find sub-activity
        sub_activity = None
        for sub in project.sub_activities:
            if sub.name == sub_name:
                sub_activity = sub
                break

        if not sub_activity:
            dialog = MessageDialog(self.window, "Error", f"Sub-activity '{sub_name}' not found!")
            dialog.show()
            return

        # Show edit dialog
        dialog = SubActivityEditDialog(
            self.window,
            f"Edit Sub-Activity in '{project_alias}'",
            initial_name=sub_activity.name,
            initial_alias=sub_activity.alias,
            theme=self.theme
        )
        result = dialog.show()

        if result:
            name, alias = result
            sub_activity.name = name
            sub_activity.alias = alias
            self.populate_projects()
            self.status_label.config(text=f"Updated sub-activity: {alias}")
            if self.on_update_callback:
                self.on_update_callback()

    def delete_sub_activity(self):
        """Delete selected sub-activity"""
        selection = self.tree.selection()
        if not selection:
            dialog = MessageDialog(
                self.window, "Warning", "Please select a sub-activity to delete!"
            )
            dialog.show()
            return

        item = selection[0]
        item_text = self.tree.item(item, 'text')

        if '📄' not in item_text:
            dialog = MessageDialog(self.window, "Warning", "Please select a sub-activity!")
            dialog.show()
            return

        sub_name = item_text.replace('  📄 ', '')
        parent = self.tree.parent(item)
        if not parent:
            return

        parent_text = self.tree.item(parent, 'text')
        project_alias = parent_text.replace('📁 ', '')
        project = self.data_manager.get_project(project_alias)
        if not project:
            return

        # Find sub-activity alias
        sub_alias = None
        for sub in project.sub_activities:
            if sub.name == sub_name:
                sub_alias = sub.alias
                break

        if not sub_alias:
            return

        # Confirm deletion
        dialog = ConfirmDialog(
            self.window, "Confirm Delete",
            f"Delete sub-activity '{sub_name}' from project '{project_alias}'?"
        )
        result = dialog.show()

        if result:
            if project.remove_sub_activity(sub_alias):
                self.populate_projects()
                self.status_label.config(text=f"Deleted sub-activity: {sub_name}")
                if self.on_update_callback:
                    self.on_update_callback()
            else:
                dialog = MessageDialog(
                    self.window, "Error", f"Failed to delete sub-activity '{sub_name}'!"
                )
                dialog.show()

    def close(self):
        """Close the project management window"""
        try:
            if hasattr(self, 'window') and self.window:
                self.window.destroy()
        except (tk.TclError, AttributeError) as e:
            print(f"Error closing project management window: {e}")


class ProjectEditDialog:
    """Compact dialog for editing project details"""

    def __init__(self, parent: Any, title: str, initial_name: str = "",
                 initial_dz: str = "", initial_alias: str = "",
                 theme: dict[str, str] | None = None) -> None:
        self.parent = parent
        self.result = None
        self.start_x = 0
        self.start_y = 0
        # Use provided theme or default to matrix theme with button colors
        self.theme = theme if theme else {
            'name': 'Matrix', 'bg': '#001100', 'fg': '#00FF00', 'accent': '#00AA00',
            'button_bg': '#003300', 'button_fg': '#00FF00', 'button_active': '#004400'
        }

        # Create borderless dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.overrideredirect(True)  # Remove title bar and borders
        self.dialog.geometry("320x200")  # Increased height for button visibility
        self.dialog.configure(bg=self.theme['bg'])
        self.dialog.resizable(False, False)  # Fixed size for compactness
        self.dialog.attributes('-topmost', True)  # type: ignore[misc]

        # Position relative to parent (without transient for borderless)
        try:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            x = parent_x + 50
            y = parent_y + 50
            self.dialog.geometry(f"320x200+{x}+{y}")
        except (tk.TclError, AttributeError):
            # Fallback to center of screen
            self.dialog.geometry("320x200+300+200")

        self.create_widgets(title, initial_name, initial_dz, initial_alias)

        # Add drag functionality for borderless window
        self.setup_drag_functionality()

        # Focus on dialog (without grab_set to avoid freezing)
        self.dialog.focus_set()

    def setup_drag_functionality(self) -> None:
        """Set up drag functionality for borderless window"""
        def start_drag(event: Any) -> None:
            self.start_x = event.x_root - self.dialog.winfo_x()
            self.start_y = event.y_root - self.dialog.winfo_y()

        def drag_window(event: Any) -> None:
            x = event.x_root - self.start_x
            y = event.y_root - self.start_y
            self.dialog.geometry(f"+{x}+{y}")

        # Bind drag events to the title area and main frame
        self.dialog.bind('<Button-1>', start_drag)
        self.dialog.bind('<B1-Motion>', drag_window)

    def create_widgets(self, title: str, initial_name: str, initial_dz: str,
                      initial_alias: str) -> None:
        """Create ultra-compact borderless dialog widgets"""
        # Add thin border frame for borderless window
        border_frame = tk.Frame(self.dialog, bg=self.theme['fg'], bd=0)
        border_frame.pack(fill='both', expand=True, padx=0, pady=0)

        # Main container with minimal spacing - creates thin border effect
        main_frame = tk.Frame(border_frame, bg=self.theme['bg'])
        main_frame.pack(fill='both', expand=True, padx=1, pady=1)

        # Content container with proper spacing
        content_frame = tk.Frame(main_frame, bg=self.theme['bg'])
        content_frame.pack(fill='both', expand=True, padx=7, pady=5)

        # Ultra-compact title with close button
        title_frame = tk.Frame(content_frame, bg=self.theme['bg'])
        title_frame.pack(fill='x', pady=(0, 6))

        title_label = tk.Label(
            title_frame,
            text=title,
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 9, 'bold')
        )
        title_label.pack(side='left')

        close_button = tk.Button(
            title_frame,
            text="✕",
            bg=self.theme['accent'],
            fg=self.theme['bg'],
            font=('Arial', 8, 'bold'),
            command=self.cancel_clicked,
            width=2,
            pady=0,
            relief='flat',
            bd=0
        )
        close_button.pack(side='right')

        # Compact form fields
        # Project Name field
        name_label = tk.Label(
            content_frame,
            text="Project Name:",
            bg=self.theme['bg'],
            fg=self.theme['accent'],
            font=('Arial', 8)
        )
        name_label.pack(anchor='w', pady=(0, 1))

        self.name_var = tk.StringVar(value=initial_name)
        name_entry = tk.Entry(
            content_frame,
            textvariable=self.name_var,
            bg=self.theme['accent'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            relief='solid',
            bd=1,
            insertbackground=self.theme['fg']
        )
        name_entry.pack(fill='x', pady=(0, 4), ipady=1)

        # DZ Number field
        dz_label = tk.Label(
            content_frame,
            text="DZ Number:",
            bg=self.theme['bg'],
            fg=self.theme['accent'],
            font=('Arial', 8)
        )
        dz_label.pack(anchor='w', pady=(0, 1))

        self.dz_var = tk.StringVar(value=initial_dz)
        dz_entry = tk.Entry(
            content_frame,
            textvariable=self.dz_var,
            bg=self.theme['accent'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            relief='solid',
            bd=1,
            insertbackground=self.theme['fg']
        )
        dz_entry.pack(fill='x', pady=(0, 4), ipady=1)

        # Alias field
        alias_label = tk.Label(
            content_frame,
            text="Alias:",
            bg=self.theme['bg'],
            fg=self.theme['accent'],
            font=('Arial', 8)
        )
        alias_label.pack(anchor='w', pady=(0, 1))

        self.alias_var = tk.StringVar(value=initial_alias)
        alias_entry = tk.Entry(
            content_frame,
            textvariable=self.alias_var,
            bg=self.theme['accent'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            relief='solid',
            bd=1,
            insertbackground=self.theme['fg']
        )
        alias_entry.pack(fill='x', pady=(0, 8), ipady=1)

        # Ultra-compact buttons
        button_frame = tk.Frame(content_frame, bg=self.theme['bg'])
        button_frame.pack(fill='x')

        ok_button = tk.Button(
            button_frame,
            text="OK",
            bg=self.theme['accent'],
            fg=self.theme['bg'],
            font=('Arial', 8, 'bold'),
            command=self.ok_clicked,
            width=8,
            pady=3,
            relief='solid',
            bd=1
        )
        ok_button.pack(side='left', padx=(15, 8))

        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            bg=self.theme['accent'],
            fg=self.theme['bg'],
            font=('Arial', 8, 'bold'),
            command=self.cancel_clicked,
            width=8,
            pady=3,
            relief='solid',
            bd=1
        )
        cancel_button.pack(side='left')

        # Set focus to first entry
        name_entry.focus_set()

    def show(self):
        """Show the dialog and wait for result"""
        # Set focus to first entry
        if hasattr(self, 'name_var'):
            for widget in self.dialog.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Entry):
                            child.focus_set()
                            break
                    break

        self.dialog.wait_window()
        return self.result

    def ok_clicked(self):
        """Handle OK button click"""
        name = self.name_var.get().strip()
        dz_number = self.dz_var.get().strip()
        alias = self.alias_var.get().strip()

        if not name or not alias:
            # Show simple error message
            error_dialog = tk.Toplevel(self.dialog)
            error_dialog.title("Error")
            error_dialog.geometry("300x100")
            error_dialog.configure(bg=self.theme['bg'])
            error_dialog.transient(self.dialog)
            error_dialog.grab_set()

            tk.Label(
                error_dialog,
                text="Name and Alias are required!",
                bg=self.theme['bg'],
                fg=self.theme['fg'],
                font=('Arial', 10)
            ).pack(expand=True)

            tk.Button(
                error_dialog,
                text="OK",
                bg=self.theme['accent'],
                fg=self.theme['bg'],
                command=error_dialog.destroy
            ).pack(pady=10)

            return

        self.result = (name, dz_number, alias)
        self.dialog.destroy()

    def cancel_clicked(self) -> None:
        """Handle Cancel button click"""
        self.result = None
        self.dialog.destroy()

    def update_theme(self, new_theme: dict[str, str]) -> None:
        """Update the theme of the dialog"""
        self.theme = new_theme

        # Update dialog background
        self.dialog.configure(bg=self.theme['bg'])

        # Apply theme to all widgets recursively
        self._apply_theme_to_children(self.dialog)

    def _apply_theme_to_children(self, parent: Any) -> None:
        """Apply current theme to all child widgets"""
        for child in parent.winfo_children():
            widget_class = child.winfo_class()

            if widget_class == 'Frame':
                child.configure(bg=self.theme['bg'])
                self._apply_theme_to_children(child)
            elif widget_class == 'Label':
                try:
                    if str(child['text']) in ['✕']:
                        child.configure(bg='#660000', fg='#FF6666')
                    else:
                        child.configure(bg=self.theme['bg'], fg=self.theme['fg'])
                except tk.TclError:
                    pass
            elif widget_class == 'Button':
                try:
                    if str(child['text']) in ['✕']:
                        child.configure(bg='#660000', fg='#FF6666')
                    else:
                        child.configure(
                            bg=self.theme.get('button_bg', self.theme['accent']),
                            fg=self.theme.get('button_fg', self.theme['bg']),
                            activebackground=self.theme.get('button_active', self.theme['fg']),
                            activeforeground=self.theme.get('button_fg', self.theme['bg'])
                        )
                except tk.TclError:
                    pass
            elif widget_class == 'Entry':
                try:
                    child.configure(
                        bg=self.theme['bg'],
                        fg=self.theme['fg'],
                        insertbackground=self.theme['fg']
                    )
                except tk.TclError:
                    pass
            # Apply theme to child widgets recursively
            self._apply_theme_to_children(child)


class SubActivityEditDialog:
    """Compact dialog for editing sub-activity details"""

    def __init__(self, parent: Any, title: str, initial_name: str = "",
                 initial_alias: str = "", theme: dict[str, str] | None = None) -> None:
        self.parent = parent
        self.result = None
        self.start_x = 0
        self.start_y = 0
        # Use provided theme or default to matrix theme
        self.theme = theme if theme else {
            'name': 'Matrix', 'bg': '#001100', 'fg': '#00FF00', 'accent': '#00AA00'
        }

        # Create borderless dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.overrideredirect(True)  # Remove title bar and borders
        # Slightly larger for visual consistency with project dialog
        self.dialog.geometry("310x160")
        self.dialog.configure(bg=self.theme['bg'])
        self.dialog.resizable(False, False)  # Fixed size for compactness
        self.dialog.attributes('-topmost', True)  # type: ignore[misc]

        # Position relative to parent (without transient for borderless)
        try:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            x = parent_x + 50
            y = parent_y + 50
            self.dialog.geometry(f"310x160+{x}+{y}")
        except (tk.TclError, AttributeError):
            # Fallback to center of screen
            self.dialog.geometry("310x160+300+200")

        self.create_widgets(title, initial_name, initial_alias)

        # Add drag functionality for borderless window
        self.setup_drag_functionality()

        # Focus on dialog (without grab_set to avoid freezing)
        self.dialog.focus_set()

    def setup_drag_functionality(self):
        """Set up drag functionality for borderless window"""
        self.start_x = 0
        self.start_y = 0

        def start_drag(event: Any) -> None:
            self.start_x = event.x_root - self.dialog.winfo_x()
            self.start_y = event.y_root - self.dialog.winfo_y()

        def drag_window(event: Any) -> None:
            x = event.x_root - self.start_x
            y = event.y_root - self.start_y
            self.dialog.geometry(f"+{x}+{y}")

        # Bind drag events to the title area and main frame
        self.dialog.bind('<Button-1>', start_drag)
        self.dialog.bind('<B1-Motion>', drag_window)

    def create_widgets(self, title: str, initial_name: str, initial_alias: str) -> None:
        """Create ultra-compact borderless dialog widgets"""
        # Add thin border frame for borderless window
        border_frame = tk.Frame(self.dialog, bg=self.theme['fg'], bd=0)
        border_frame.pack(fill='both', expand=True, padx=0, pady=0)

        # Main container with minimal spacing - creates thin border effect
        main_frame = tk.Frame(border_frame, bg=self.theme['bg'])
        main_frame.pack(fill='both', expand=True, padx=1, pady=1)

        # Content container with proper spacing
        content_frame = tk.Frame(main_frame, bg=self.theme['bg'])
        content_frame.pack(fill='both', expand=True, padx=6, pady=4)

        # Ultra-compact title with close button
        title_frame = tk.Frame(content_frame, bg=self.theme['bg'])
        title_frame.pack(fill='x', pady=(0, 4))

        title_label = tk.Label(
            title_frame,
            text=title,
            bg=self.theme['bg'],
            fg=self.theme['fg'],
            font=('Arial', 9, 'bold')
        )
        title_label.pack(side='left')

        close_button = tk.Button(
            title_frame,
            text="✕",
            bg=self.theme['accent'],
            fg=self.theme['bg'],
            font=('Arial', 8, 'bold'),
            command=self.cancel_clicked,
            width=2,
            pady=0,
            relief='flat',
            bd=0
        )
        close_button.pack(side='right')

        # Sub-Activity Name field
        name_label = tk.Label(
            content_frame,
            text="Name:",
            bg=self.theme['bg'],
            fg=self.theme['accent'],
            font=('Arial', 8)
        )
        name_label.pack(anchor='w', pady=(0, 1))

        self.name_var = tk.StringVar(value=initial_name)
        name_entry = tk.Entry(
            content_frame,
            textvariable=self.name_var,
            bg=self.theme['accent'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            relief='solid',
            bd=1,
            insertbackground=self.theme['fg']
        )
        name_entry.pack(fill='x', pady=(0, 4), ipady=1)

        # Alias field
        alias_label = tk.Label(
            content_frame,
            text="Alias:",
            bg=self.theme['bg'],
            fg=self.theme['accent'],
            font=('Arial', 8)
        )
        alias_label.pack(anchor='w', pady=(0, 1))

        self.alias_var = tk.StringVar(value=initial_alias)
        alias_entry = tk.Entry(
            content_frame,
            textvariable=self.alias_var,
            bg=self.theme['accent'],
            fg=self.theme['fg'],
            font=('Arial', 8),
            relief='solid',
            bd=1,
            insertbackground=self.theme['fg']
        )
        alias_entry.pack(fill='x', pady=(0, 4), ipady=1)

        # Ultra-compact buttons
        button_frame = tk.Frame(content_frame, bg=self.theme['bg'])
        button_frame.pack(fill='x')

        ok_button = tk.Button(
            button_frame,
            text="OK",
            bg=self.theme['accent'],
            fg=self.theme['bg'],
            font=('Arial', 8, 'bold'),
            command=self.ok_clicked,
            width=8,
            pady=3,
            relief='solid',
            bd=1
        )
        ok_button.pack(side='left', padx=(15, 8))

        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            bg=self.theme['accent'],
            fg=self.theme['bg'],
            font=('Arial', 8, 'bold'),
            command=self.cancel_clicked,
            width=8,
            pady=3,
            relief='solid',
            bd=1
        )
        cancel_button.pack(side='left')

        # Set focus to first entry
        name_entry.focus_set()

    def show(self):
        """Show the dialog and wait for result"""
        # Set focus to first entry
        if hasattr(self, 'name_var'):
            for widget in self.dialog.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Entry):
                            child.focus_set()
                            break
                    break

        self.dialog.wait_window()
        return self.result

    def ok_clicked(self):
        """Handle OK button click"""
        name = self.name_var.get().strip()
        alias = self.alias_var.get().strip()

        if not name or not alias:
            # Show simple error message
            error_dialog = tk.Toplevel(self.dialog)
            error_dialog.title("Error")
            error_dialog.geometry("300x100")
            error_dialog.configure(bg='#001100')
            error_dialog.transient(self.dialog)
            error_dialog.grab_set()

            tk.Label(
                error_dialog,
                text="Name and Alias are required!",
                bg='#001100',
                fg='#FF6666',
                font=('Arial', 10)
            ).pack(expand=True)

            tk.Button(
                error_dialog,
                text="OK",
                bg='#330000',
                fg='#FF6666',
                command=error_dialog.destroy
            ).pack(pady=10)

            return

        self.result = (name, alias)
        self.dialog.destroy()

    def cancel_clicked(self) -> None:
        """Handle Cancel button click"""
        self.result = None
        self.dialog.destroy()


class MessageDialog:
    """Compact message dialog"""

    def __init__(self, parent: Any, title: str, message: str,
                 theme: dict[str, str] | None = None) -> None:
        self.parent = parent
        self.start_x = 0
        self.start_y = 0
        # Use provided theme or default to matrix theme
        self.theme = theme if theme else {
            'name': 'Matrix', 'bg': '#001100', 'fg': '#00FF00', 'accent': '#00AA00'
        }

        # Create borderless dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.overrideredirect(True)  # Remove title bar and borders
        self.dialog.geometry("280x110")  # Increased height for button visibility
        self.dialog.configure(bg=self.theme['bg'])
        self.dialog.resizable(False, False)
        self.dialog.attributes('-topmost', True)  # type: ignore[misc]

        # Position relative to parent (without transient for borderless)
        try:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            x = parent_x + 75
            y = parent_y + 75
            self.dialog.geometry(f"280x110+{x}+{y}")
        except (tk.TclError, AttributeError):
            # Fallback to center of screen
            self.dialog.geometry("280x110+300+200")

        self.create_widgets(title, message)

        # Add drag functionality for borderless window
        self.setup_drag_functionality()

        # Focus on dialog (without grab_set to avoid freezing)
        self.dialog.focus_set()

    def setup_drag_functionality(self) -> None:
        """Set up drag functionality for borderless window"""
        def start_drag(event: Any) -> None:
            self.start_x = event.x_root - self.dialog.winfo_x()
            self.start_y = event.y_root - self.dialog.winfo_y()

        def drag_window(event: Any) -> None:
            x = event.x_root - self.start_x
            y = event.y_root - self.start_y
            self.dialog.geometry(f"+{x}+{y}")

        # Bind drag events to the dialog
        self.dialog.bind('<Button-1>', start_drag)
        self.dialog.bind('<B1-Motion>', drag_window)

    def create_widgets(self, title: str, message: str) -> None:
        """Create ultra-compact borderless dialog widgets"""
        # Add thin border frame for borderless window
        border_frame = tk.Frame(self.dialog, bg='#00FF00', bd=0)
        border_frame.pack(fill='both', expand=True, padx=0, pady=0)

        # Main container with minimal spacing - creates thin border effect
        main_frame = tk.Frame(border_frame, bg='#001100')
        main_frame.pack(fill='both', expand=True, padx=1, pady=1)

        # Content container with proper spacing
        content_frame = tk.Frame(main_frame, bg='#001100')
        content_frame.pack(fill='both', expand=True, padx=8, pady=6)

        # Title with close button
        title_frame = tk.Frame(content_frame, bg='#001100')
        title_frame.pack(fill='x', pady=(0, 4))

        title_label = tk.Label(
            title_frame,
            text=title,
            bg='#001100',
            fg='#00FF00',
            font=('Arial', 8, 'bold')
        )
        title_label.pack(side='left')

        close_button = tk.Button(
            title_frame,
            text="✕",
            bg='#330000',
            fg='#FF6666',
            font=('Arial', 7, 'bold'),
            command=self.dialog.destroy,
            width=2,
            pady=0,
            relief='flat',
            bd=0
        )
        close_button.pack(side='right')

        # Ultra-compact message
        message_label = tk.Label(
            content_frame,
            text=message,
            bg='#001100',
            fg='#00AA00',
            font=('Arial', 8),
            wraplength=250,
            justify='center'
        )
        message_label.pack(expand=True, pady=(0, 6))

        # Ultra-compact OK button
        ok_button = tk.Button(
            content_frame,
            text="OK",
            bg='#003300',
            fg='#00FF00',
            font=('Arial', 8, 'bold'),
            command=self.dialog.destroy,
            width=6,
            pady=2,
            relief='solid',
            bd=1
        )
        ok_button.pack()
        ok_button.focus_set()

    def show(self) -> None:
        """Show the dialog and wait for result"""
        self.dialog.wait_window()


class ConfirmDialog:
    """Compact confirmation dialog"""

    def __init__(self, parent: Any, title: str, message: str) -> None:
        self.parent = parent
        self.result = False

        # Create borderless dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.overrideredirect(True)  # Remove title bar and borders
        self.dialog.geometry("300x120")  # Increased height for button visibility
        self.dialog.configure(bg='#001100')
        self.dialog.resizable(False, False)
        self.dialog.attributes('-topmost', True)  # type: ignore[misc]

        # Position relative to parent (without transient for borderless)
        try:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            x = parent_x + 75
            y = parent_y + 75
            self.dialog.geometry(f"300x120+{x}+{y}")
        except (tk.TclError, AttributeError):
            # Fallback to center of screen
            self.dialog.geometry("300x120+300+200")

        self.create_widgets(title, message)

        # Focus on dialog (without grab_set to avoid freezing)
        self.dialog.focus_set()

    def create_widgets(self, title: str, message: str) -> None:
        """Create ultra-compact borderless dialog widgets"""
        # Add thin border frame for borderless window
        border_frame = tk.Frame(self.dialog, bg='#00FF00', bd=0)
        border_frame.pack(fill='both', expand=True, padx=0, pady=0)

        # Main container with minimal spacing - creates thin border effect
        main_frame = tk.Frame(border_frame, bg='#001100')
        main_frame.pack(fill='both', expand=True, padx=1, pady=1)

        # Content container with proper spacing
        content_frame = tk.Frame(main_frame, bg='#001100')
        content_frame.pack(fill='both', expand=True, padx=8, pady=6)

        # Title with close button
        title_frame = tk.Frame(content_frame, bg='#001100')
        title_frame.pack(fill='x', pady=(0, 4))

        title_label = tk.Label(
            title_frame,
            text=title,
            bg='#001100',
            fg='#00FF00',
            font=('Arial', 8, 'bold')
        )
        title_label.pack(side='left')

        close_button = tk.Button(
            title_frame,
            text="✕",
            bg='#330000',
            fg='#FF6666',
            font=('Arial', 7, 'bold'),
            command=self.no_clicked,
            width=2,
            pady=0,
            relief='flat',
            bd=0
        )
        close_button.pack(side='right')

        # Ultra-compact message
        message_label = tk.Label(
            content_frame,
            text=message,
            bg='#001100',
            fg='#00AA00',
            font=('Arial', 8),
            wraplength=270,
            justify='center'
        )
        message_label.pack(expand=True, pady=(0, 6))

        # Ultra-compact buttons
        button_frame = tk.Frame(content_frame, bg='#001100')
        button_frame.pack()

        yes_button = tk.Button(
            button_frame,
            text="Yes",
            bg='#003300',
            fg='#00FF00',
            font=('Arial', 8, 'bold'),
            command=self.yes_clicked,
            width=6,
            pady=2,
            relief='solid',
            bd=1
        )
        yes_button.pack(side='left', padx=(0, 8))

        no_button = tk.Button(
            button_frame,
            text="No",
            bg='#330000',
            fg='#FF6666',
            font=('Arial', 8, 'bold'),
            command=self.no_clicked,
            width=6,
            pady=2,
            relief='solid',
            bd=1
        )
        no_button.pack(side='left')

        # Set focus on No button (safer default)
        no_button.focus_set()

    def show(self) -> bool:
        """Show the dialog and wait for result"""
        self.dialog.wait_window()
        return self.result

    def yes_clicked(self) -> None:
        """Handle Yes button click"""
        self.result = True
        self.dialog.destroy()

    def no_clicked(self) -> None:
        """Handle No button click"""
        self.result = False
        self.dialog.destroy()
