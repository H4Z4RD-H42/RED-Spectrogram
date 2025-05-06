import os
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import threading
import sys
import configparser
import re
import webbrowser

class SpectrogramGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("RED-Spectrogram v2.0")
        self.root.geometry("700x500")
        self.root.configure(background="#f0f0f0")
        self.root.resizable(True, True)
        
        # Variables
        self.selected_files = []
        # Output folder inside the application directory
        self.output_folder = os.path.join(self.get_application_path(), "Spectrograms")
        self.sox_path = self.find_sox_path()
        self.current_process = None
        self.config = self.load_config()
        
        # SoX download URL
        self.sox_url = "https://sourceforge.net/projects/sox/files/sox/"
        
        # Check if output folder exists
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        
        # Create the user interface
        self.create_ui()
    
    def get_application_path(self):
        """Get the application path, works both in development mode and with PyInstaller"""
        if getattr(sys, 'frozen', False):
            # If running as a PyInstaller bundle
            return os.path.dirname(sys.executable)
        else:
            # If running in development mode
            return os.path.dirname(os.path.abspath(__file__))
    
    def resource_path(self, relative_path):
        """Get the absolute path of the resource, works both in development and with PyInstaller"""
        if getattr(sys, 'frozen', False):
            # If running as a PyInstaller bundle
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            # If running in development mode
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    
    def find_sox_path(self):
        """Find the path of the SoX executable"""
        # Default path next to the application
        app_dir = self.get_application_path()
        default_sox_path = os.path.join(app_dir, "sox", "sox.exe")
        
        # Check if it exists in the default path
        if os.path.exists(default_sox_path):
            print(f"SoX found in default path: {default_sox_path}")
            return default_sox_path
        
        # Alternative system paths
        system_paths = [
            r"C:\Program Files\sox-14-4-2\sox.exe",
            r"C:\Program Files (x86)\sox-14-4-2\sox.exe",
            r"C:\sox-14-4-2\sox.exe"
        ]
        
        # Check system paths
        for path in system_paths:
            if os.path.exists(path):
                print(f"SoX found in system: {path}")
                return path
        
        # Search in PATH
        if sys.platform == "win32":
            cmd = "where sox"
        else:
            cmd = "which sox"
        
        try:
            result = subprocess.check_output(cmd, shell=True).decode().strip()
            if result and os.path.exists(result):
                print(f"SoX found in PATH: {result}")
                return result
        except:
            pass
        
        # Return default path even if it doesn't exist
        # (a warning will be shown to the user later)
        return default_sox_path
    
    def load_config(self):
        """Load or create the configuration file"""
        config = configparser.ConfigParser()
        config_file = os.path.join(self.get_application_path(), "spectrogram_config.ini")
        
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            # Default configuration
            config["DEFAULT"] = {
                "width": "3000",
                "height": "513",
                "z_range": "120",
                "window_type": "Kaiser",
                "output_folder": self.output_folder,
                "sox_path": self.sox_path
            }
            
            config["ZOOM"] = {
                "width": "500",
                "height": "1025",
                "z_range": "120",
                "window_type": "Kaiser",
                "zoom_start": "1:00",
                "zoom_duration": "0:02"
            }
            
            with open(config_file, "w") as f:
                config.write(f)
        
        return config
    
    def save_config(self):
        """Save the current settings to the configuration file"""
        config_file = os.path.join(self.get_application_path(), "spectrogram_config.ini")
        
        # Update config with current values
        self.config["DEFAULT"]["width"] = self.width_var.get()
        self.config["DEFAULT"]["height"] = self.height_var.get()
        self.config["DEFAULT"]["z_range"] = self.z_range_var.get()
        self.config["DEFAULT"]["window_type"] = self.window_type_var.get()
        self.config["DEFAULT"]["output_folder"] = self.output_folder
        self.config["DEFAULT"]["sox_path"] = self.sox_path if self.sox_path else ""
        
        self.config["ZOOM"]["width"] = self.zoom_width_var.get()
        self.config["ZOOM"]["height"] = self.zoom_height_var.get()
        self.config["ZOOM"]["z_range"] = self.zoom_z_range_var.get()
        self.config["ZOOM"]["window_type"] = self.zoom_window_type_var.get()
        self.config["ZOOM"]["zoom_start"] = self.zoom_start_var.get()
        self.config["ZOOM"]["zoom_duration"] = self.zoom_duration_var.get()
        
        with open(config_file, "w") as f:
            self.config.write(f)
    
    def create_ui(self):
        """Create the user interface"""
        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Download SoX", command=self.open_sox_website)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        # Main frame with tabs
        self.notebook = ttk.Notebook(self.root)
        
        # Main tab
        self.main_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.pack(expand=1, fill="both", padx=10, pady=10)
        
        # ---------- MAIN TAB ----------
        # File selector frame
        file_frame = ttk.LabelFrame(self.main_tab, text="Select Files")
        file_frame.pack(fill="both", expand=False, padx=10, pady=5)
        
        # File list
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.MULTIPLE, height=6, width=70)
        self.file_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar for the list
        listbox_scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_listbox.yview)
        listbox_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.file_listbox.config(yscrollcommand=listbox_scrollbar.set)
        
        # File buttons frame
        file_button_frame = ttk.Frame(self.main_tab)
        file_button_frame.pack(fill="x", padx=10, pady=5)
        
        # Buttons for files
        ttk.Button(file_button_frame, text="Add Files", command=self.browse_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_button_frame, text="Add Folder", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_button_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_button_frame, text="Clear List", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # Generation frame
        gen_frame = ttk.LabelFrame(self.main_tab, text="Spectrogram Generation")
        gen_frame.pack(fill="both", expand=False, padx=10, pady=5)
        
        # Checkboxes for spectrogram types
        self.normal_var = tk.BooleanVar(value=True)
        self.zoom_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(gen_frame, text="Full Spectrogram", variable=self.normal_var).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(gen_frame, text="Zoomed Spectrogram", variable=self.zoom_var).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Generate button
        ttk.Button(gen_frame, text="Generate Spectrograms", command=self.start_generation).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(gen_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(gen_frame, textvariable=self.status_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Output Frame
        output_frame = ttk.LabelFrame(self.main_tab, text="Output")
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Listbox for generated files
        self.output_listbox = tk.Listbox(output_frame, height=6, width=70)
        self.output_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        self.output_listbox.bind("<Double-1>", self.open_selected_output)
        
        # Scrollbar for output
        output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_listbox.yview)
        output_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.output_listbox.config(yscrollcommand=output_scrollbar.set)
        
        # Output buttons frame
        output_button_frame = ttk.Frame(self.main_tab)
        output_button_frame.pack(fill="x", padx=10, pady=5)
        
        # Buttons for output
        ttk.Button(output_button_frame, text="Open Selected File", command=self.open_selected_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_button_frame, text="Open Output Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_button_frame, text="Refresh List", command=self.refresh_output_list).pack(side=tk.LEFT, padx=5)
        
        # SoX download link
        sox_link = ttk.Label(self.main_tab, text="Need SoX? Download it here", foreground="blue", cursor="hand2")
        sox_link.pack(side=tk.BOTTOM, pady=5)
        sox_link.bind("<Button-1>", lambda e: self.open_sox_website())
        
        # ---------- SETTINGS TAB ----------
        # General settings frame
        general_frame = ttk.LabelFrame(self.settings_tab, text="General Settings")
        general_frame.pack(fill="x", padx=10, pady=5)
        
        # SoX path
        ttk.Label(general_frame, text="SoX Path:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.sox_path_var = tk.StringVar(value=self.sox_path if self.sox_path else "")
        sox_entry = ttk.Entry(general_frame, textvariable=self.sox_path_var, width=50)
        sox_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(general_frame, text="Browse", command=self.browse_sox).grid(row=0, column=2, padx=5, pady=5)
        
        # Output folder
        ttk.Label(general_frame, text="Output Folder:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.output_folder_var = tk.StringVar(value=self.output_folder)
        output_entry = ttk.Entry(general_frame, textvariable=self.output_folder_var, width=50)
        output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(general_frame, text="Browse", command=self.browse_output_folder).grid(row=1, column=2, padx=5, pady=5)
        
        # Normal spectrogram settings frame
        normal_frame = ttk.LabelFrame(self.settings_tab, text="Full Spectrogram Settings")
        normal_frame.pack(fill="x", padx=10, pady=5)
        
        # Parameters
        ttk.Label(normal_frame, text="Width (pixels):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.width_var = tk.StringVar(value=self.config["DEFAULT"]["width"])
        ttk.Entry(normal_frame, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(normal_frame, text="Height (bins):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.height_var = tk.StringVar(value=self.config["DEFAULT"]["height"])
        ttk.Entry(normal_frame, textvariable=self.height_var, width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(normal_frame, text="Z Range (dB):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.z_range_var = tk.StringVar(value=self.config["DEFAULT"]["z_range"])
        ttk.Entry(normal_frame, textvariable=self.z_range_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(normal_frame, text="Window Type:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.window_type_var = tk.StringVar(value=self.config["DEFAULT"]["window_type"])
        window_types = ["Kaiser", "Hamming", "Hann", "Bartlett", "Rectangular"]
        ttk.Combobox(normal_frame, textvariable=self.window_type_var, values=window_types, width=10).grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Parameters help
        help_text = "Valid ranges - Width: 100-5000 pixels, Height: typically 129, 257, 513, 1025 (2^n+1), Z Range: 20-180 dB"
        ttk.Label(normal_frame, text=help_text, foreground="gray").grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="w")
        
        # Zoom settings frame
        zoom_frame = ttk.LabelFrame(self.settings_tab, text="Zoomed Spectrogram Settings")
        zoom_frame.pack(fill="x", padx=10, pady=5)
        
        # Zoom parameters
        ttk.Label(zoom_frame, text="Width (pixels):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.zoom_width_var = tk.StringVar(value=self.config["ZOOM"]["width"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_width_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Height (bins):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.zoom_height_var = tk.StringVar(value=self.config["ZOOM"]["height"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_height_var, width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Z Range (dB):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.zoom_z_range_var = tk.StringVar(value=self.config["ZOOM"]["z_range"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_z_range_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Window Type:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.zoom_window_type_var = tk.StringVar(value=self.config["ZOOM"]["window_type"])
        ttk.Combobox(zoom_frame, textvariable=self.zoom_window_type_var, values=window_types, width=10).grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Start Time:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.zoom_start_var = tk.StringVar(value=self.config["ZOOM"]["zoom_start"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_start_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Duration:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.zoom_duration_var = tk.StringVar(value=self.config["ZOOM"]["zoom_duration"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_duration_var, width=10).grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        # Parameters help
        zoom_help_text = "Valid ranges - Width: 100-5000 pixels, Height: typically 129, 257, 513, 1025 (2^n+1), Z Range: 20-180 dB, Time Format: M:SS"
        ttk.Label(zoom_frame, text=zoom_help_text, foreground="gray").grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="w")
        
        # Save buttons
        button_frame = ttk.Frame(self.settings_tab)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_settings).pack(side=tk.LEFT, padx=5)
        
        # Check if SoX is available and show warning if necessary
        self.check_sox_available()
        
        # Initialize state
        self.refresh_output_list()
    
    def check_sox_available(self):
        """Check if SoX is available and display warning if necessary"""
        if not self.sox_path or not os.path.exists(self.sox_path):
            messagebox.showwarning(
                "SoX Not Found", 
                "SoX was not found in the default path:\n"
                f"{self.sox_path}\n\n"
                "Make sure the 'sox' folder is present next to the executable.\n"
                "Alternatively, specify the path manually in the settings or download SoX from the Help menu."
            )
    
    def open_sox_website(self):
        """Open the SoX download website"""
        webbrowser.open(self.sox_url)
    
    def show_about(self):
        """Show the About dialog"""
        messagebox.showinfo(
            "About RED-Spectrogram",
            "RED-Spectrogram v2.0\n\n"
            "A tool to create spectrograms from FLAC files using SoX.\n\n"
            "© 2025 RED-Spectrogram Team"
        )
    
    def browse_files(self):
        """Open the dialog to select files"""
        files = filedialog.askopenfilenames(
            title="Select FLAC Files",
            filetypes=(("FLAC Files", "*.flac"), ("All Files", "*.*"))
        )
        
        if files:
            for file in files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
                    self.file_listbox.insert(tk.END, os.path.basename(file))
    
    def browse_folder(self):
        """Open the dialog to select a folder"""
        folder = filedialog.askdirectory(title="Select Folder with FLAC Files")
        
        if folder:
            for file in os.listdir(folder):
                if file.lower().endswith('.flac'):
                    full_path = os.path.join(folder, file)
                    if full_path not in self.selected_files:
                        self.selected_files.append(full_path)
                        self.file_listbox.insert(tk.END, file)
    
    def remove_selected(self):
        """Remove selected files from the list"""
        selected_indices = self.file_listbox.curselection()
        
        # Remove from last to first to avoid issues with indices
        for i in sorted(selected_indices, reverse=True):
            del self.selected_files[i]
            self.file_listbox.delete(i)
    
    def clear_files(self):
        """Clear the file list"""
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
    
    def browse_sox(self):
        """Select the SoX path"""
        sox_path = filedialog.askopenfilename(
            title="Select SoX Executable",
            filetypes=(("Executable Files", "*.exe"), ("All Files", "*.*"))
        )
        
        if sox_path:
            self.sox_path = sox_path
            self.sox_path_var.set(sox_path)
    
    def browse_output_folder(self):
        """Select the output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        
        if folder:
            self.output_folder = folder
            self.output_folder_var.set(folder)
            
            # Make sure the folder exists
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
    
    def save_settings(self):
        """Save the settings"""
        self.sox_path = self.sox_path_var.get()
        self.output_folder = self.output_folder_var.get()
        
        # Make sure the folder exists
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        
        self.save_config()
        messagebox.showinfo("Save", "Settings saved successfully!")
    
    def reset_settings(self):
        """Reset settings to default values"""
        if messagebox.askyesno("Reset", "Are you sure you want to reset all settings to default values?"):
            # Reset to default settings
            self.width_var.set("3000")
            self.height_var.set("513")
            self.z_range_var.set("120")
            self.window_type_var.set("Kaiser")
            
            self.zoom_width_var.set("500")
            self.zoom_height_var.set("1025")
            self.zoom_z_range_var.set("120")
            self.zoom_window_type_var.set("Kaiser")
            self.zoom_start_var.set("1:00")
            self.zoom_duration_var.set("0:02")
    
    def refresh_output_list(self):
        """Update the list of output files"""
        self.output_listbox.delete(0, tk.END)
        
        if os.path.exists(self.output_folder):
            files = [f for f in os.listdir(self.output_folder) if f.lower().endswith('.png')]
            files.sort()
            
            for file in files:
                self.output_listbox.insert(tk.END, file)
    
    def open_selected_output(self, event=None):
        """Open the selected output file"""
        selected = self.output_listbox.curselection()
        
        if selected:
            index = selected[0]
            filename = self.output_listbox.get(index)
            filepath = os.path.join(self.output_folder, filename)
            
            # Open the file with the default system program
            if sys.platform == "win32":
                os.startfile(filepath)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, filepath])
    
    def open_output_folder(self):
        """Open the output folder"""
        if os.path.exists(self.output_folder):
            if sys.platform == "win32":
                os.startfile(self.output_folder)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, self.output_folder])
    
    def validate_time_format(self, time_str):
        """Validate the time format (M:SS)"""
        pattern = r"^\d+:\d{2}$"
        return bool(re.match(pattern, time_str))
    
    def validate_parameters(self):
        """Validate parameters against SoX limits"""
        # Check width parameters (100-5000)
        try:
            width = int(self.width_var.get())
            if width < 100 or width > 5000:
                messagebox.showwarning("Invalid Parameter", "Width must be between 100 and 5000 pixels.")
                return False
            
            zoom_width = int(self.zoom_width_var.get())
            if zoom_width < 100 or zoom_width > 5000:
                messagebox.showwarning("Invalid Parameter", "Zoomed Width must be between 100 and 5000 pixels.")
                return False
        except ValueError:
            messagebox.showwarning("Invalid Parameter", "Width values must be integers.")
            return False
        
        # Check height parameters (should be 2^n+1 for efficiency)
        try:
            height = int(self.height_var.get())
            zoom_height = int(self.zoom_height_var.get())
            
            # Check if heights are proper values (2^n+1)
            # We'll just warn but allow non-optimal values
            valid_heights = [65, 129, 257, 513, 1025, 2049, 4097]
            if height not in valid_heights and height != 0:
                if not messagebox.askyesno("Non-optimal Height", 
                                       "The height value is not optimal for SoX processing.\n"
                                       "For best performance, use values like 129, 257, 513, or 1025.\n"
                                       "Continue anyway?"):
                    return False
            
            if zoom_height not in valid_heights and zoom_height != 0:
                if not messagebox.askyesno("Non-optimal Height", 
                                        "The zoomed height value is not optimal for SoX processing.\n"
                                        "For best performance, use values like 129, 257, 513, or 1025.\n"
                                        "Continue anyway?"):
                    return False
        except ValueError:
            messagebox.showwarning("Invalid Parameter", "Height values must be integers.")
            return False
        
        # Check Z-range parameters (20-180)
        try:
            z_range = int(self.z_range_var.get())
            if z_range < 20 or z_range > 180:
                messagebox.showwarning("Invalid Parameter", "Z Range must be between 20 and 180 dB.")
                return False
            
            zoom_z_range = int(self.zoom_z_range_var.get())
            if zoom_z_range < 20 or zoom_z_range > 180:
                messagebox.showwarning("Invalid Parameter", "Zoomed Z Range must be between 20 and 180 dB.")
                return False
        except ValueError:
            messagebox.showwarning("Invalid Parameter", "Z Range values must be integers.")
            return False
        
        return True
    
    def start_generation(self):
        """Start the spectrogram generation process"""
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected.")
            return
        
        if not self.sox_path or not os.path.exists(self.sox_path):
            messagebox.showerror("Error", "Invalid SoX path. Check the settings.")
            return
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        
        # Check that at least one spectrogram type is selected
        if not self.normal_var.get() and not self.zoom_var.get():
            messagebox.showwarning("Warning", "Select at least one spectrogram type to generate.")
            return
        
        # Validate parameters
        if not self.validate_parameters():
            return
        
        # Check zoom time format
        if self.zoom_var.get():
            if not self.validate_time_format(self.zoom_start_var.get()) or not self.validate_time_format(self.zoom_duration_var.get()):
                messagebox.showwarning("Warning", "Invalid zoom time format. Use the format M:SS")
                return
        
        # Create separate thread for generation
        threading.Thread(target=self.generate_spectrograms, daemon=True).start()
    
    def generate_spectrograms(self):
        """Generate spectrograms for all selected files"""
        total_files = len(self.selected_files)
        self.progress["maximum"] = total_files
        self.progress["value"] = 0
        
        generated_count = 0
        
        for i, file_path in enumerate(self.selected_files):
            file_name = os.path.basename(file_path)
            self.status_var.set(f"Processing {i+1}/{total_files}: {file_name}")
            self.root.update()
            
            try:
                # Generate normal spectrogram
                if self.normal_var.get():
                    try:
                        self.generate_normal_spectrogram(file_path, file_name)
                        generated_count += 1
                    except Exception as e:
                        messagebox.showerror("Error", f"Error generating full spectrogram for {file_name}: {str(e)}")
                
                # Generate zoomed spectrogram
                if self.zoom_var.get():
                    try:
                        self.generate_zoomed_spectrogram(file_path, file_name)
                        generated_count += 1
                    except Exception as e:
                        messagebox.showerror("Error", f"Error generating zoomed spectrogram for {file_name}: {str(e)}")
                
                # Update progress
                self.progress["value"] = i + 1
                self.root.update()
            
            except Exception as e:
                messagebox.showerror("Error", f"Error processing {file_name}: {str(e)}")
        
        # Use correct plural form
        if generated_count == 1:
            completion_message = f"Completed! Generated {generated_count} spectrogram."
        else:
            completion_message = f"Completed! Generated {generated_count} spectrograms."
            
        self.status_var.set(completion_message)
        self.refresh_output_list()
        messagebox.showinfo("Complete", completion_message)
    
    def generate_normal_spectrogram(self, file_path, file_name):
        """Generate a normal spectrogram"""
        output_path = os.path.join(self.output_folder, f"{file_name}_full.png")
        
        # Get the SoX directory to set the correct environment
        sox_dir = os.path.dirname(self.sox_path)
        
        # Prepare the SoX command as a string to use shell=True
        sox_cmd = f'"{self.sox_path}" "{file_path}" -n remix 1 spectrogram -x {self.width_var.get()} -y {self.height_var.get()} -z {self.z_range_var.get()} -w {self.window_type_var.get()} -t "{file_name} [FULL]" -o "{output_path}"'
        
        print(f"Executing command: {sox_cmd}")
        
        try:
            # Save the current directory
            current_dir = os.getcwd()
            
            # Change to the SoX directory to ensure it finds all its DLLs
            if os.path.exists(sox_dir):
                os.chdir(sox_dir)
            
            # Execute the command
            result = subprocess.run(sox_cmd, shell=True, check=True, capture_output=True, text=True)
            
            # Restore the original directory
            os.chdir(current_dir)
            
            # Print any error output
            if result.stderr:
                print(f"Error output: {result.stderr}")
        
        except subprocess.CalledProcessError as e:
            print(f"Error executing SoX: {e}")
            print(f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No details available'}")
            
            # Restore the original directory in case of error
            if os.getcwd() != current_dir:
                os.chdir(current_dir)
            
            messagebox.showerror("SoX Error", f"Error generating spectrogram:\n{str(e)}")
            raise
    
    def generate_zoomed_spectrogram(self, file_path, file_name):
        """Generate a zoomed spectrogram"""
        output_path = os.path.join(self.output_folder, f"{file_name}_zoom.png")
        
        # Get the SoX directory to set the correct environment
        sox_dir = os.path.dirname(self.sox_path)
        
        # Prepare the SoX command as a string to use shell=True
        start_time = self.zoom_start_var.get()
        duration = self.zoom_duration_var.get()
        
        sox_cmd = f'"{self.sox_path}" "{file_path}" -n remix 1 spectrogram -x {self.zoom_width_var.get()} -y {self.zoom_height_var.get()} -z {self.zoom_z_range_var.get()} -w {self.zoom_window_type_var.get()} -t "{file_name} [ZOOM {start_time} to {start_time}+{duration}]" -S {start_time} -d {duration} -o "{output_path}"'
        
        print(f"Executing command: {sox_cmd}")
        
        try:
            # Save the current directory
            current_dir = os.getcwd()
            
            # Change to the SoX directory to ensure it finds all its DLLs
            if os.path.exists(sox_dir):
                os.chdir(sox_dir)
            
            # Execute the command
            result = subprocess.run(sox_cmd, shell=True, check=True, capture_output=True, text=True)
            
            # Restore the original directory
            os.chdir(current_dir)
            
            # Print any error output
            if result.stderr:
                print(f"Error output: {result.stderr}")
        
        except subprocess.CalledProcessError as e:
            print(f"Error executing SoX: {e}")
            print(f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No details available'}")
            
            # Restore the original directory in case of error
            if os.getcwd() != current_dir:
                os.chdir(current_dir)
            
            messagebox.showerror("SoX Error", f"Error generating spectrogram:\n{str(e)}")
            raise


if __name__ == "__main__":
    root = tk.Tk()
    app = SpectrogramGenerator(root)
    root.mainloop()
    