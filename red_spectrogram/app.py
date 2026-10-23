"""RED-Spectrogram graphical interface (ttkbootstrap)."""

from __future__ import annotations

import logging
import os
import queue
import subprocess
import sys
import threading
import webbrowser
from tkinter import filedialog, messagebox

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, END, HORIZONTAL, LEFT, MULTIPLE, RIGHT, X, Y

from . import APP_NAME, REPO_URL, __version__
from .config import AVAILABLE_THEMES, CONFIG_FILENAME, DEFAULT_THEME, WINDOW_TYPES, AppConfig
from .logging_setup import configure_logging, get_log_path
from .paths import find_sox_path, get_assets_path, get_data_dir
from .sox_backend import (
    SUPPORTED_EXTENSIONS,
    SoxExecutionError,
    SpectrogramParams,
    build_full_cmd,
    build_zoom_cmd,
    is_supported_audio_file,
    run_sox,
)
from .validation import (
    ValidationError,
    is_height_optimal,
    validate_gain,
    validate_height,
    validate_time_format,
    validate_width,
    validate_z_range,
)

logger = logging.getLogger(__name__)

SOX_NG_RELEASES_URL = "https://codeberg.org/sox_ng/sox_ng/releases"
ISSUES_URL = f"{REPO_URL}/issues"
FILE_DIALOG_TYPES = (
    ("Lossless Audio Files", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)),
    ("All Files", "*.*"),
)


class SpectrogramApp:
    """UI orchestration: builds the widgets and delegates validation, config
    and SoX execution to the package's pure modules."""

    def __init__(self, root: tb.Window, config: AppConfig):
        self.root = root
        self.config = config

        self.selected_files: list[str] = []
        self.output_folder = config.output_folder
        self.sox_path = config.sox_path
        self.progress_queue: queue.Queue = queue.Queue()

        os.makedirs(self.output_folder, exist_ok=True)

        self._build_ui()
        self._check_sox_available()
        self.refresh_output_list()

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        self._build_menu()

        self.notebook = tb.Notebook(self.root)
        self.main_tab = tb.Frame(self.notebook)
        self.settings_tab = tb.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.pack(expand=1, fill=BOTH, padx=10, pady=10)

        self._build_main_tab()
        self._build_settings_tab()

    def _build_menu(self) -> None:
        self.menu_bar = tb.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        help_menu = tb.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Project Website", command=lambda: webbrowser.open(REPO_URL))
        help_menu.add_command(label="Report an Issue", command=lambda: webbrowser.open(ISSUES_URL))
        help_menu.add_separator()
        help_menu.add_command(label="Download sox_ng", command=self.open_sox_website)
        help_menu.add_command(label="Open Log File", command=self.open_log_file)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

    def _build_main_tab(self) -> None:
        file_frame = tb.Labelframe(self.main_tab, text="Select Files")
        file_frame.pack(fill=BOTH, expand=False, padx=10, pady=5)

        self.file_listbox = tb.Listbox(file_frame, selectmode=MULTIPLE, height=6)
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

        file_scrollbar = tb.Scrollbar(file_frame, orient="vertical", command=self.file_listbox.yview)
        file_scrollbar.pack(side=RIGHT, fill=Y)
        self.file_listbox.config(yscrollcommand=file_scrollbar.set)

        file_button_frame = tb.Frame(self.main_tab)
        file_button_frame.pack(fill=X, padx=10, pady=5)
        tb.Button(file_button_frame, text="Add Files", command=self.browse_files, bootstyle="primary").pack(side=LEFT, padx=5)
        tb.Button(file_button_frame, text="Add Folder", command=self.browse_folder, bootstyle="primary").pack(side=LEFT, padx=5)
        tb.Button(file_button_frame, text="Remove Selected", command=self.remove_selected, bootstyle="secondary").pack(side=LEFT, padx=5)
        tb.Button(file_button_frame, text="Clear List", command=self.clear_files, bootstyle="secondary").pack(side=LEFT, padx=5)

        gen_frame = tb.Labelframe(self.main_tab, text="Spectrogram Generation")
        gen_frame.pack(fill=BOTH, expand=False, padx=10, pady=5)

        self.normal_var = tb.BooleanVar(value=True)
        self.zoom_var = tb.BooleanVar(value=False)
        tb.Checkbutton(gen_frame, text="Full Spectrogram", variable=self.normal_var, bootstyle="round-toggle").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tb.Checkbutton(gen_frame, text="Zoomed Spectrogram", variable=self.zoom_var, bootstyle="round-toggle").grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tb.Button(gen_frame, text="Generate Spectrograms", command=self.start_generation, bootstyle="success").grid(row=1, column=0, columnspan=2, padx=5, pady=8, sticky="ew")

        self.progress = tb.Progressbar(gen_frame, orient=HORIZONTAL, length=100, mode="determinate", bootstyle="success-striped")
        self.progress.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.status_var = tb.StringVar(value="Ready")
        tb.Label(gen_frame, textvariable=self.status_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        output_frame = tb.Labelframe(self.main_tab, text="Output")
        output_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.output_listbox = tb.Listbox(output_frame, height=6)
        self.output_listbox.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        self.output_listbox.bind("<Double-1>", self.open_selected_output)

        output_scrollbar = tb.Scrollbar(output_frame, orient="vertical", command=self.output_listbox.yview)
        output_scrollbar.pack(side=RIGHT, fill=Y)
        self.output_listbox.config(yscrollcommand=output_scrollbar.set)

        output_button_frame = tb.Frame(self.main_tab)
        output_button_frame.pack(fill=X, padx=10, pady=5)
        tb.Button(output_button_frame, text="Open Selected File", command=self.open_selected_output, bootstyle="secondary").pack(side=LEFT, padx=5)
        tb.Button(output_button_frame, text="Open Output Folder", command=self.open_output_folder, bootstyle="secondary").pack(side=LEFT, padx=5)
        tb.Button(output_button_frame, text="Refresh List", command=self.refresh_output_list, bootstyle="secondary").pack(side=LEFT, padx=5)

        # Packed by _check_sox_available() only when sox_ng is missing.
        self.sox_link = tb.Label(self.main_tab, text="Need sox_ng? Download it here", bootstyle="info", cursor="hand2")
        self.sox_link.bind("<Button-1>", lambda e: self.open_sox_website())

    def _build_settings_tab(self) -> None:
        general_frame = tb.Labelframe(self.settings_tab, text="General Settings")
        general_frame.pack(fill=X, padx=10, pady=5)

        tb.Label(general_frame, text="SoX Path:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.sox_path_var = tb.StringVar(value=self.sox_path or "")
        tb.Entry(general_frame, textvariable=self.sox_path_var, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="we")
        tb.Button(general_frame, text="Browse", command=self.browse_sox, bootstyle="secondary").grid(row=0, column=2, padx=5, pady=5)

        tb.Label(general_frame, text="Output Folder:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.output_folder_var = tb.StringVar(value=self.output_folder)
        tb.Entry(general_frame, textvariable=self.output_folder_var, width=50).grid(row=1, column=1, padx=5, pady=5, sticky="we")
        tb.Button(general_frame, text="Browse", command=self.browse_output_folder, bootstyle="secondary").grid(row=1, column=2, padx=5, pady=5)

        tb.Label(general_frame, text="Theme:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.theme_var = tb.StringVar(value=self.config.theme)
        tb.Combobox(general_frame, textvariable=self.theme_var, values=AVAILABLE_THEMES, width=15, state="readonly").grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.theme_var.trace_add("write", self._on_theme_change)

        general_frame.columnconfigure(1, weight=1)

        normal_frame = tb.Labelframe(self.settings_tab, text="Full Spectrogram Settings")
        normal_frame.pack(fill=X, padx=10, pady=5)

        tb.Label(normal_frame, text="Width (pixels):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.width_var = tb.StringVar(value=self.config.full.width)
        tb.Entry(normal_frame, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tb.Label(normal_frame, text="Height (bins):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.height_var = tb.StringVar(value=self.config.full.height)
        tb.Entry(normal_frame, textvariable=self.height_var, width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        tb.Label(normal_frame, text="Z Range (dB):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.z_range_var = tb.StringVar(value=self.config.full.z_range)
        tb.Entry(normal_frame, textvariable=self.z_range_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tb.Label(normal_frame, text="Window Type:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.window_type_var = tb.StringVar(value=self.config.full.window_type)
        tb.Combobox(normal_frame, textvariable=self.window_type_var, values=WINDOW_TYPES, width=10, state="readonly").grid(row=1, column=3, padx=5, pady=5, sticky="w")

        tb.Label(normal_frame, text="Gain (dB):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.gain_var = tb.StringVar(value=self.config.full.gain)
        tb.Entry(normal_frame, textvariable=self.gain_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        help_text = "Valid ranges - Width: 100-5000 px, Height: 129/257/513/1025 (2^n+1), Z Range: 20-180 dB, Gain: -20 to 20 dB"
        tb.Label(normal_frame, text=help_text, bootstyle="secondary").grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="w")

        zoom_frame = tb.Labelframe(self.settings_tab, text="Zoomed Spectrogram Settings")
        zoom_frame.pack(fill=X, padx=10, pady=5)

        tb.Label(zoom_frame, text="Width (pixels):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.zoom_width_var = tb.StringVar(value=self.config.zoom.width)
        tb.Entry(zoom_frame, textvariable=self.zoom_width_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tb.Label(zoom_frame, text="Height (bins):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.zoom_height_var = tb.StringVar(value=self.config.zoom.height)
        tb.Entry(zoom_frame, textvariable=self.zoom_height_var, width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        tb.Label(zoom_frame, text="Z Range (dB):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.zoom_z_range_var = tb.StringVar(value=self.config.zoom.z_range)
        tb.Entry(zoom_frame, textvariable=self.zoom_z_range_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tb.Label(zoom_frame, text="Window Type:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.zoom_window_type_var = tb.StringVar(value=self.config.zoom.window_type)
        tb.Combobox(zoom_frame, textvariable=self.zoom_window_type_var, values=WINDOW_TYPES, width=10, state="readonly").grid(row=1, column=3, padx=5, pady=5, sticky="w")

        tb.Label(zoom_frame, text="Gain (dB):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.zoom_gain_var = tb.StringVar(value=self.config.zoom.gain)
        tb.Entry(zoom_frame, textvariable=self.zoom_gain_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        tb.Label(zoom_frame, text="Start Time:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.zoom_start_var = tb.StringVar(value=self.config.zoom.zoom_start)
        tb.Entry(zoom_frame, textvariable=self.zoom_start_var, width=10).grid(row=2, column=3, padx=5, pady=5, sticky="w")

        tb.Label(zoom_frame, text="Duration:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.zoom_duration_var = tb.StringVar(value=self.config.zoom.zoom_duration)
        tb.Entry(zoom_frame, textvariable=self.zoom_duration_var, width=10).grid(row=3, column=1, padx=5, pady=5, sticky="w")

        zoom_help_text = "Valid ranges as above. Time Format: M:SS"
        tb.Label(zoom_frame, text=zoom_help_text, bootstyle="secondary").grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="w")

        button_frame = tb.Frame(self.settings_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        tb.Button(button_frame, text="Save Settings", command=self.save_settings, bootstyle="primary").pack(side=LEFT, padx=5)
        tb.Button(button_frame, text="Reset to Defaults", command=self.reset_settings, bootstyle="secondary").pack(side=LEFT, padx=5)

    # ---------- Theme ----------

    def _on_theme_change(self, *_args) -> None:
        theme = self.theme_var.get()
        if theme in AVAILABLE_THEMES:
            self.root.style.theme_use(theme)
            self.config.theme = theme
            apply_title_bar_theme(self.root, theme)

    # ---------- SoX availability / info ----------

    def _check_sox_available(self) -> None:
        if not self.sox_path or not os.path.exists(self.sox_path):
            self.sox_link.pack(side="bottom", pady=5)
            messagebox.showwarning(
                "SoX Not Found",
                "sox_ng/SoX was not found in the default path:\n"
                f"{self.sox_path}\n\n"
                "Make sure the 'sox' folder is present next to the executable.\n"
                "Alternatively, specify the path manually in Settings or download it from the Help menu.",
            )

    def open_sox_website(self) -> None:
        webbrowser.open(SOX_NG_RELEASES_URL)

    def open_log_file(self) -> None:
        log_path = get_log_path()
        if os.path.exists(log_path):
            open_path(log_path)
        else:
            messagebox.showinfo("Log File", "No log file has been created yet.")

    def show_about(self) -> None:
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{__version__}\n\n"
            "Generate spectrograms from lossless audio files using sox_ng/SoX.\n\n"
            "Released under the MIT License.\n"
            f"{REPO_URL}",
        )

    # ---------- File selection ----------

    def browse_files(self) -> None:
        files = filedialog.askopenfilenames(title="Select Audio Files", filetypes=FILE_DIALOG_TYPES)
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.file_listbox.insert(END, os.path.basename(file))

    def browse_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Folder with Audio Files")
        if not folder:
            return
        for entry in sorted(os.listdir(folder)):
            if is_supported_audio_file(entry):
                full_path = os.path.join(folder, entry)
                if full_path not in self.selected_files:
                    self.selected_files.append(full_path)
                    self.file_listbox.insert(END, entry)

    def remove_selected(self) -> None:
        for i in sorted(self.file_listbox.curselection(), reverse=True):
            del self.selected_files[i]
            self.file_listbox.delete(i)

    def clear_files(self) -> None:
        self.selected_files = []
        self.file_listbox.delete(0, END)

    # ---------- Settings ----------

    def browse_sox(self) -> None:
        path = filedialog.askopenfilename(title="Select sox_ng/SoX Executable", filetypes=(("Executable Files", "*.exe"), ("All Files", "*.*")))
        if path:
            self.sox_path = path
            self.sox_path_var.set(path)

    def browse_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_folder_var.set(folder)
            os.makedirs(self.output_folder, exist_ok=True)

    def save_settings(self) -> None:
        self.sox_path = self.sox_path_var.get()
        self.output_folder = self.output_folder_var.get()
        os.makedirs(self.output_folder, exist_ok=True)

        self.config.output_folder = self.output_folder
        self.config.sox_path = self.sox_path
        self.config.theme = self.theme_var.get()
        self.config.full.width = self.width_var.get()
        self.config.full.height = self.height_var.get()
        self.config.full.z_range = self.z_range_var.get()
        self.config.full.window_type = self.window_type_var.get()
        self.config.full.gain = self.gain_var.get()
        self.config.zoom.width = self.zoom_width_var.get()
        self.config.zoom.height = self.zoom_height_var.get()
        self.config.zoom.z_range = self.zoom_z_range_var.get()
        self.config.zoom.window_type = self.zoom_window_type_var.get()
        self.config.zoom.gain = self.zoom_gain_var.get()
        self.config.zoom.zoom_start = self.zoom_start_var.get()
        self.config.zoom.zoom_duration = self.zoom_duration_var.get()

        self.config.save()
        messagebox.showinfo("Save", "Settings saved successfully!")

    def reset_settings(self) -> None:
        if not messagebox.askyesno("Reset", "Are you sure you want to reset all settings to default values?"):
            return
        self.config.reset_spectrogram_defaults()
        self.width_var.set(self.config.full.width)
        self.height_var.set(self.config.full.height)
        self.z_range_var.set(self.config.full.z_range)
        self.window_type_var.set(self.config.full.window_type)
        self.gain_var.set(self.config.full.gain)
        self.zoom_width_var.set(self.config.zoom.width)
        self.zoom_height_var.set(self.config.zoom.height)
        self.zoom_z_range_var.set(self.config.zoom.z_range)
        self.zoom_window_type_var.set(self.config.zoom.window_type)
        self.zoom_gain_var.set(self.config.zoom.gain)
        self.zoom_start_var.set(self.config.zoom.zoom_start)
        self.zoom_duration_var.set(self.config.zoom.zoom_duration)

    # ---------- Output list ----------

    def refresh_output_list(self) -> None:
        self.output_listbox.delete(0, END)
        if not os.path.exists(self.output_folder):
            return
        files = sorted(f for f in os.listdir(self.output_folder) if f.lower().endswith(".png"))
        for file in files:
            self.output_listbox.insert(END, file)

    def open_selected_output(self, event=None) -> None:
        selected = self.output_listbox.curselection()
        if not selected:
            return
        filename = self.output_listbox.get(selected[0])
        open_path(os.path.join(self.output_folder, filename))

    def open_output_folder(self) -> None:
        if os.path.exists(self.output_folder):
            open_path(self.output_folder)

    # ---------- Validation ----------

    def _validate_parameters(self) -> bool:
        try:
            validate_width(self.width_var.get())
            validate_width(self.zoom_width_var.get(), label="Zoomed Width")
            height = validate_height(self.height_var.get())
            zoom_height = validate_height(self.zoom_height_var.get(), label="Zoomed Height")
            validate_z_range(self.z_range_var.get())
            validate_z_range(self.zoom_z_range_var.get(), label="Zoomed Z Range")
            validate_gain(self.gain_var.get())
            validate_gain(self.zoom_gain_var.get(), label="Zoomed Gain")
        except ValidationError as e:
            messagebox.showwarning("Invalid Parameter", str(e))
            return False

        if not is_height_optimal(height):
            if not messagebox.askyesno(
                "Non-optimal Height",
                "The height value is not optimal for SoX processing.\n"
                "For best performance, use values like 129, 257, 513, or 1025.\n"
                "Continue anyway?",
            ):
                return False

        if not is_height_optimal(zoom_height):
            if not messagebox.askyesno(
                "Non-optimal Height",
                "The zoomed height value is not optimal for SoX processing.\n"
                "For best performance, use values like 129, 257, 513, or 1025.\n"
                "Continue anyway?",
            ):
                return False

        return True

    # ---------- Generation ----------

    def start_generation(self) -> None:
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected.")
            return
        if not self.sox_path or not os.path.exists(self.sox_path):
            messagebox.showerror("Error", "Invalid SoX path. Check the settings.")
            return
        os.makedirs(self.output_folder, exist_ok=True)

        if not self.normal_var.get() and not self.zoom_var.get():
            messagebox.showwarning("Warning", "Select at least one spectrogram type to generate.")
            return

        if not self._validate_parameters():
            return

        if self.zoom_var.get():
            if not validate_time_format(self.zoom_start_var.get()) or not validate_time_format(self.zoom_duration_var.get()):
                messagebox.showwarning("Warning", "Invalid zoom time format. Use the format M:SS")
                return

        # The worker thread talks to the UI only through progress_queue, which
        # process_queue() drains on the main thread (Tkinter is not thread-safe).
        threading.Thread(target=self.generate_spectrograms, daemon=True).start()
        self.root.after(100, self.process_queue)

    def process_queue(self) -> None:
        try:
            while True:
                kind, payload = self.progress_queue.get_nowait()
                if kind == "max":
                    self.progress["maximum"] = payload
                    self.progress["value"] = 0
                elif kind == "status":
                    self.status_var.set(payload)
                elif kind == "progress":
                    self.progress["value"] = payload
                elif kind == "error":
                    messagebox.showerror("Error", payload)
                elif kind == "done":
                    self.status_var.set(payload)
                    self.refresh_output_list()
                    messagebox.showinfo("Complete", payload)
                    return
        except queue.Empty:
            pass

        self.root.after(100, self.process_queue)

    def generate_spectrograms(self) -> None:
        """Runs on the worker thread: generates every requested spectrogram."""
        total_files = len(self.selected_files)
        self.progress_queue.put(("max", total_files))

        generated_count = 0

        for i, file_path in enumerate(self.selected_files):
            file_name = os.path.basename(file_path)
            self.progress_queue.put(("status", f"Processing {i + 1}/{total_files}: {file_name}"))

            if self.normal_var.get():
                try:
                    self._generate_full(file_path, file_name)
                    generated_count += 1
                except SoxExecutionError as e:
                    self.progress_queue.put(("error", f"Error generating full spectrogram for {file_name}: {e}"))

            if self.zoom_var.get():
                try:
                    self._generate_zoom(file_path, file_name)
                    generated_count += 1
                except SoxExecutionError as e:
                    self.progress_queue.put(("error", f"Error generating zoomed spectrogram for {file_name}: {e}"))

            self.progress_queue.put(("progress", i + 1))

        noun = "spectrogram" if generated_count == 1 else "spectrograms"
        self.progress_queue.put(("done", f"Completed! Generated {generated_count} {noun}."))

    def _generate_full(self, file_path: str, file_name: str) -> None:
        # The suffix goes after the full file name (extension included) so
        # files that differ only by format ("track.flac" and "track.wav")
        # don't overwrite each other's output.
        output_path = os.path.join(self.output_folder, f"{file_name}_full.png")
        params = SpectrogramParams(
            width=self.width_var.get(),
            height=self.height_var.get(),
            z_range=self.z_range_var.get(),
            window_type=self.window_type_var.get(),
            gain=self.gain_var.get(),
        )
        cmd = build_full_cmd(self.sox_path, file_path, output_path, params, f"{file_name} [FULL]")
        run_sox(cmd, self.sox_path)

    def _generate_zoom(self, file_path: str, file_name: str) -> None:
        output_path = os.path.join(self.output_folder, f"{file_name}_zoom.png")
        start_time = self.zoom_start_var.get()
        duration = self.zoom_duration_var.get()
        params = SpectrogramParams(
            width=self.zoom_width_var.get(),
            height=self.zoom_height_var.get(),
            z_range=self.zoom_z_range_var.get(),
            window_type=self.zoom_window_type_var.get(),
            gain=self.zoom_gain_var.get(),
        )
        title = f"{file_name} [ZOOM {start_time} to {start_time}+{duration}]"
        cmd = build_zoom_cmd(self.sox_path, file_path, output_path, params, title, start_time, duration)
        run_sox(cmd, self.sox_path)


def open_path(path: str) -> None:
    """Open a file or folder with the operating system's default handler."""
    if sys.platform == "win32":
        os.startfile(path)
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])


def _set_windows_app_id() -> None:
    """Give the process its own taskbar identity, so Windows shows the app
    icon instead of the Python one when running from source."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"{APP_NAME}.{__version__}")
    except (AttributeError, OSError):
        pass


def apply_title_bar_theme(root: tb.Window, theme: str) -> None:
    """Match the native Windows title bar to dark/light themes (Windows 10 20H1+)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        root.update_idletasks()  # the native frame window only exists once Tk has mapped it
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        use_dark = ctypes.c_int(1 if "dark" in theme else 0)
        dwmwa_use_immersive_dark_mode = 20
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, dwmwa_use_immersive_dark_mode, ctypes.byref(use_dark), ctypes.sizeof(use_dark)
        )
    except (AttributeError, OSError):
        pass


def main() -> None:
    configure_logging()
    logger.info("Starting %s v%s", APP_NAME, __version__)

    data_dir = get_data_dir()
    default_output_folder = os.path.join(data_dir, "Spectrograms")
    default_sox_path = find_sox_path()
    config_path = os.path.join(data_dir, CONFIG_FILENAME)
    app_config = AppConfig.load(config_path, default_output_folder, default_sox_path)

    _set_windows_app_id()
    theme = app_config.theme if app_config.theme in AVAILABLE_THEMES else DEFAULT_THEME
    root = tb.Window(themename=theme, iconphoto=get_assets_path("icon.png"))
    root.title(f"{APP_NAME} v{__version__}")
    root.geometry("780x640")
    root.minsize(680, 560)

    SpectrogramApp(root, app_config)
    apply_title_bar_theme(root, theme)
    root.mainloop()


if __name__ == "__main__":
    main()
