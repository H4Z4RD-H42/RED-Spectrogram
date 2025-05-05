import os
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import threading
import sys
import configparser
import re

class SpectrogramGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Spettrogram Generator v2.0")
        self.root.geometry("700x500")
        self.root.configure(background="#f0f0f0")
        self.root.resizable(True, True)
        
        # Variabili
        self.selected_files = []
        self.output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Spectrograms")
        self.sox_path = self.find_sox_path()
        self.current_process = None
        self.config = self.load_config()
        
        # Controllo se esiste la cartella di output
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        
        # Creazione dell'interfaccia
        self.create_ui()
    
    def find_sox_path(self):
        """Cerca il percorso dell'eseguibile SoX"""
        default_paths = [
            r"C:\Program Files\sox-14-4-2\sox.exe",
            r"C:\Program Files (x86)\sox-14-4-2\sox.exe",
            r"C:\sox-14-4-2\sox.exe"
        ]
        
        # Controlla i percorsi predefiniti
        for path in default_paths:
            if os.path.exists(path):
                return path
        
        # Altrimenti, cerca in PATH
        if sys.platform == "win32":
            cmd = "where sox"
        else:
            cmd = "which sox"
        
        try:
            result = subprocess.check_output(cmd, shell=True).decode().strip()
            if result and os.path.exists(result):
                return result
        except:
            pass
        
        # Ritorna None se non trovato
        return None
    
    def load_config(self):
        """Carica o crea il file di configurazione"""
        config = configparser.ConfigParser()
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spectrogram_config.ini")
        
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            # Configurazione predefinita
            config["DEFAULT"] = {
                "width": "3000",
                "height": "513",
                "z_range": "120",
                "window_type": "Kaiser",
                "output_folder": self.output_folder,
                "sox_path": self.sox_path if self.sox_path else ""
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
        """Salva le impostazioni attuali nel file di configurazione"""
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spectrogram_config.ini")
        
        # Aggiorna il config con i valori attuali
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
        """Crea l'interfaccia utente"""
        # Frame principale con tabs
        self.notebook = ttk.Notebook(self.root)
        
        # Tab principale
        self.main_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text="Principale")
        self.notebook.add(self.settings_tab, text="Impostazioni")
        self.notebook.pack(expand=1, fill="both", padx=10, pady=10)
        
        # ---------- TAB PRINCIPALE ----------
        # Frame selettore file
        file_frame = ttk.LabelFrame(self.main_tab, text="Seleziona File")
        file_frame.pack(fill="both", expand=False, padx=10, pady=5)
        
        # Lista file
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.MULTIPLE, height=6, width=70)
        self.file_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar per la lista
        listbox_scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_listbox.yview)
        listbox_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.file_listbox.config(yscrollcommand=listbox_scrollbar.set)
        
        # Frame bottoni file
        file_button_frame = ttk.Frame(self.main_tab)
        file_button_frame.pack(fill="x", padx=10, pady=5)
        
        # Bottoni per file
        ttk.Button(file_button_frame, text="Aggiungi File", command=self.browse_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_button_frame, text="Aggiungi Cartella", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_button_frame, text="Rimuovi Selezionati", command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_button_frame, text="Pulisci Lista", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # Frame generazione
        gen_frame = ttk.LabelFrame(self.main_tab, text="Generazione Spettrogrammi")
        gen_frame.pack(fill="both", expand=False, padx=10, pady=5)
        
        # Checkbox per tipi di spettrogrammi
        self.normal_var = tk.BooleanVar(value=True)
        self.zoom_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(gen_frame, text="Spettrogramma Completo", variable=self.normal_var).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(gen_frame, text="Spettrogramma Zoom", variable=self.zoom_var).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Bottone per generare
        ttk.Button(gen_frame, text="Genera Spettrogrammi", command=self.start_generation).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Barra di progresso
        self.progress = ttk.Progressbar(gen_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Status
        self.status_var = tk.StringVar(value="Pronto")
        ttk.Label(gen_frame, textvariable=self.status_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Frame Output
        output_frame = ttk.LabelFrame(self.main_tab, text="Output")
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Listbox per file generati
        self.output_listbox = tk.Listbox(output_frame, height=6, width=70)
        self.output_listbox.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        self.output_listbox.bind("<Double-1>", self.open_selected_output)
        
        # Scrollbar per output
        output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_listbox.yview)
        output_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.output_listbox.config(yscrollcommand=output_scrollbar.set)
        
        # Frame bottoni output
        output_button_frame = ttk.Frame(self.main_tab)
        output_button_frame.pack(fill="x", padx=10, pady=5)
        
        # Bottoni per output
        ttk.Button(output_button_frame, text="Apri File Selezionato", command=self.open_selected_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_button_frame, text="Apri Cartella Output", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_button_frame, text="Aggiorna Lista", command=self.refresh_output_list).pack(side=tk.LEFT, padx=5)
        
        # ---------- TAB IMPOSTAZIONI ----------
        # Frame impostazioni generali
        general_frame = ttk.LabelFrame(self.settings_tab, text="Impostazioni Generali")
        general_frame.pack(fill="x", padx=10, pady=5)
        
        # SoX path
        ttk.Label(general_frame, text="Percorso SoX:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.sox_path_var = tk.StringVar(value=self.sox_path if self.sox_path else "")
        sox_entry = ttk.Entry(general_frame, textvariable=self.sox_path_var, width=50)
        sox_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(general_frame, text="Sfoglia", command=self.browse_sox).grid(row=0, column=2, padx=5, pady=5)
        
        # Output folder
        ttk.Label(general_frame, text="Cartella Output:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.output_folder_var = tk.StringVar(value=self.output_folder)
        output_entry = ttk.Entry(general_frame, textvariable=self.output_folder_var, width=50)
        output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(general_frame, text="Sfoglia", command=self.browse_output_folder).grid(row=1, column=2, padx=5, pady=5)
        
        # Frame impostazioni spettrogramma normale
        normal_frame = ttk.LabelFrame(self.settings_tab, text="Impostazioni Spettrogramma Completo")
        normal_frame.pack(fill="x", padx=10, pady=5)
        
        # Parametri
        ttk.Label(normal_frame, text="Larghezza:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.width_var = tk.StringVar(value=self.config["DEFAULT"]["width"])
        ttk.Entry(normal_frame, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(normal_frame, text="Altezza:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.height_var = tk.StringVar(value=self.config["DEFAULT"]["height"])
        ttk.Entry(normal_frame, textvariable=self.height_var, width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(normal_frame, text="Intervallo Z:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.z_range_var = tk.StringVar(value=self.config["DEFAULT"]["z_range"])
        ttk.Entry(normal_frame, textvariable=self.z_range_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(normal_frame, text="Tipo Finestra:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.window_type_var = tk.StringVar(value=self.config["DEFAULT"]["window_type"])
        window_types = ["Kaiser", "Hamming", "Hann", "Bartlett", "Rectangular"]
        ttk.Combobox(normal_frame, textvariable=self.window_type_var, values=window_types, width=10).grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Frame impostazioni zoom
        zoom_frame = ttk.LabelFrame(self.settings_tab, text="Impostazioni Spettrogramma Zoom")
        zoom_frame.pack(fill="x", padx=10, pady=5)
        
        # Parametri zoom
        ttk.Label(zoom_frame, text="Larghezza:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.zoom_width_var = tk.StringVar(value=self.config["ZOOM"]["width"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_width_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Altezza:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.zoom_height_var = tk.StringVar(value=self.config["ZOOM"]["height"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_height_var, width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Intervallo Z:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.zoom_z_range_var = tk.StringVar(value=self.config["ZOOM"]["z_range"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_z_range_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Tipo Finestra:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.zoom_window_type_var = tk.StringVar(value=self.config["ZOOM"]["window_type"])
        ttk.Combobox(zoom_frame, textvariable=self.zoom_window_type_var, values=window_types, width=10).grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Inizio Zoom:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.zoom_start_var = tk.StringVar(value=self.config["ZOOM"]["zoom_start"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_start_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(zoom_frame, text="Durata Zoom:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.zoom_duration_var = tk.StringVar(value=self.config["ZOOM"]["zoom_duration"])
        ttk.Entry(zoom_frame, textvariable=self.zoom_duration_var, width=10).grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        # Bottoni salvataggio
        button_frame = ttk.Frame(self.settings_tab)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Salva Impostazioni", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ripristina Predefiniti", command=self.reset_settings).pack(side=tk.LEFT, padx=5)
        
        # Inizializza stato
        self.refresh_output_list()
    
    def browse_files(self):
        """Apre il dialogo per selezionare file"""
        files = filedialog.askopenfilenames(
            title="Seleziona file FLAC",
            filetypes=(("File FLAC", "*.flac"), ("Tutti i file", "*.*"))
        )
        
        if files:
            for file in files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
                    self.file_listbox.insert(tk.END, os.path.basename(file))
    
    def browse_folder(self):
        """Apre il dialogo per selezionare una cartella"""
        folder = filedialog.askdirectory(title="Seleziona cartella con file FLAC")
        
        if folder:
            for file in os.listdir(folder):
                if file.lower().endswith('.flac'):
                    full_path = os.path.join(folder, file)
                    if full_path not in self.selected_files:
                        self.selected_files.append(full_path)
                        self.file_listbox.insert(tk.END, file)
    
    def remove_selected(self):
        """Rimuove i file selezionati dalla lista"""
        selected_indices = self.file_listbox.curselection()
        
        # Rimuovi dall'ultimo al primo per evitare problemi con gli indici
        for i in sorted(selected_indices, reverse=True):
            del self.selected_files[i]
            self.file_listbox.delete(i)
    
    def clear_files(self):
        """Pulisce la lista dei file"""
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
    
    def browse_sox(self):
        """Seleziona il percorso di SoX"""
        sox_path = filedialog.askopenfilename(
            title="Seleziona eseguibile SoX",
            filetypes=(("Eseguibili", "*.exe"), ("Tutti i file", "*.*"))
        )
        
        if sox_path:
            self.sox_path = sox_path
            self.sox_path_var.set(sox_path)
    
    def browse_output_folder(self):
        """Seleziona la cartella di output"""
        folder = filedialog.askdirectory(title="Seleziona cartella di output")
        
        if folder:
            self.output_folder = folder
            self.output_folder_var.set(folder)
            
            # Assicurati che la cartella esista
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
    
    def save_settings(self):
        """Salva le impostazioni"""
        self.sox_path = self.sox_path_var.get()
        self.output_folder = self.output_folder_var.get()
        
        # Assicurati che la cartella esista
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        
        self.save_config()
        messagebox.showinfo("Salvataggio", "Impostazioni salvate con successo!")
    
    def reset_settings(self):
        """Ripristina le impostazioni predefinite"""
        if messagebox.askyesno("Ripristino", "Sei sicuro di voler ripristinare le impostazioni predefinite?"):
            # Ripristina impostazioni predefinite
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
        """Aggiorna la lista dei file di output"""
        self.output_listbox.delete(0, tk.END)
        
        if os.path.exists(self.output_folder):
            files = [f for f in os.listdir(self.output_folder) if f.lower().endswith('.png')]
            files.sort()
            
            for file in files:
                self.output_listbox.insert(tk.END, file)
    
    def open_selected_output(self, event=None):
        """Apre il file di output selezionato"""
        selected = self.output_listbox.curselection()
        
        if selected:
            index = selected[0]
            filename = self.output_listbox.get(index)
            filepath = os.path.join(self.output_folder, filename)
            
            # Apri il file con il programma predefinito del sistema operativo
            if sys.platform == "win32":
                os.startfile(filepath)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, filepath])
    
    def open_output_folder(self):
        """Apre la cartella di output"""
        if os.path.exists(self.output_folder):
            if sys.platform == "win32":
                os.startfile(self.output_folder)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, self.output_folder])
    
    def validate_time_format(self, time_str):
        """Valida il formato del tempo (M:SS)"""
        pattern = r"^\d+:\d{2}$"
        return bool(re.match(pattern, time_str))
    
    def start_generation(self):
        """Avvia il processo di generazione degli spettrogrammi"""
        if not self.selected_files:
            messagebox.showwarning("Attenzione", "Nessun file selezionato.")
            return
        
        if not self.sox_path or not os.path.exists(self.sox_path):
            messagebox.showerror("Errore", "Percorso SoX non valido. Controlla le impostazioni.")
            return
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        
        # Controlla che almeno un tipo di spettrogramma sia selezionato
        if not self.normal_var.get() and not self.zoom_var.get():
            messagebox.showwarning("Attenzione", "Seleziona almeno un tipo di spettrogramma da generare.")
            return
        
        # Controlla formato tempo zoom
        if self.zoom_var.get():
            if not self.validate_time_format(self.zoom_start_var.get()) or not self.validate_time_format(self.zoom_duration_var.get()):
                messagebox.showwarning("Attenzione", "Formato tempo zoom non valido. Usa il formato M:SS")
                return
        
        # Crea thread separato per la generazione
        threading.Thread(target=self.generate_spectrograms, daemon=True).start()
    
    def generate_spectrograms(self):
        """Genera gli spettrogrammi per tutti i file selezionati"""
        total_files = len(self.selected_files)
        self.progress["maximum"] = total_files
        self.progress["value"] = 0
        
        for i, file_path in enumerate(self.selected_files):
            file_name = os.path.basename(file_path)
            self.status_var.set(f"Elaborazione {i+1}/{total_files}: {file_name}")
            self.root.update()
            
            try:
                # Genera spettrogramma normale
                if self.normal_var.get():
                    self.generate_normal_spectrogram(file_path, file_name)
                
                # Genera spettrogramma zoom
                if self.zoom_var.get():
                    self.generate_zoomed_spectrogram(file_path, file_name)
                
                # Aggiorna progresso
                self.progress["value"] = i + 1
                self.root.update()
            
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante l'elaborazione di {file_name}: {str(e)}")
        
        self.status_var.set(f"Completato! Generati {total_files} spettrogrammi.")
        self.refresh_output_list()
        messagebox.showinfo("Completato", f"Generazione di {total_files} spettrogrammi completata.")
    
    def generate_normal_spectrogram(self, file_path, file_name):
        """Genera uno spettrogramma normale"""
        output_path = os.path.join(self.output_folder, f"{file_name}_full.png")
        
        # Prepara il comando SoX
        cmd = [
            self.sox_path,
            file_path,
            "-n", 
            "remix", "1",
            "spectrogram",
            "-x", self.width_var.get(),
            "-y", self.height_var.get(),
            "-z", self.z_range_var.get(),
            "-w", self.window_type_var.get(),
            "-t", f"{file_name} [FULL]",
            "-o", output_path
        ]
        
        # Esegui il comando
        subprocess.run(cmd, check=True)
    
    def generate_zoomed_spectrogram(self, file_path, file_name):
        """Genera uno spettrogramma con zoom"""
        output_path = os.path.join(self.output_folder, f"{file_name}_zoom.png")
        
        # Prepara il comando SoX
        cmd = [
            self.sox_path,
            file_path,
            "-n", 
            "remix", "1",
            "spectrogram",
            "-x", self.zoom_width_var.get(),
            "-y", self.zoom_height_var.get(),
            "-z", self.zoom_z_range_var.get(),
            "-w", self.zoom_window_type_var.get(),
            "-t", f"{file_name} [ZOOM {self.zoom_start_var.get()} to {self.zoom_start_var.get()}+{self.zoom_duration_var.get()}]",
            "-S", self.zoom_start_var.get(),
            "-d", self.zoom_duration_var.get(),
            "-o", output_path
        ]
        
        # Esegui il comando
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = SpectrogramGenerator(root)
    root.mainloop()
