import os
import subprocess
import tkinter as tk
from tkinter import filedialog

# -- VARIABILI --

lFileList = os.listdir(path=".")
pngFolder = f".\\Spectrograms"

# -- INTERFACCIA --

window = tk.Tk()
window.geometry("400x200")
window.title("Spectrograms Generator v1.0")
window.resizable(False, False)
window.configure(background="grey")

# -- BOTTONI --





# -- FUNZIONI --

if not os.path.exists(pngFolder):
    os.makedirs(pngFolder)

percorso = ""

def normalPng():
    for i in lFileList:
        if i.endswith('.flac'):
            outputName = i
            pathFile = f"{percorso}"
            # pathFile = f".\\{outputName}"
            pathPng = f".\\{pngFolder}\\{outputName}.png"
            subprocess.run(f'"C:\sox-14-4-2\sox.exe" "{pathFile}" -n remix 1 spectrogram -x 3000 -y 513 -z 120 -w Kaiser -t "{outputName} [FULL]" -o "{pathPng}"')

def openFiles():
    filename = filedialog.askopenfilename(defaultextension=".flac")
    with open(filename, "rt") as f:
        percorso = f.name
        normalPng()

browseButton = tk.Button(text="Browse...", command=openFiles)
browseButton.grid(row=0, column=0, padx=10)

def zoomedPng():
    for i in lFileList:
        if i.endswith('.flac'):
            outputName = i
            pathFile = f".\\{outputName}"
            pathPng = f".\\{pngFolder}\\{outputName}_zoom.png"
            subprocess.run(f'"C:\sox-14-4-2\sox.exe" "{pathFile}" -n remix 1 spectrogram -x 500 -y 1025 -z 120 -w Kaiser -t "{outputName} [ZOOM 1:00 to 1:02]" -S 1:00 -d 0:02 -o "{pathPng}"')

# -- ESECUZIONE --

if __name__ == "__main__":
    window.mainloop()

# normalPng()
# zoomedPng()