import zipfile, os, shutil, json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path

# Set up main Tkinter window
window = tk.Tk()
window.title("Save File Repair Tool")
window.geometry("600x400")

script_dir = Path(__file__).parent.absolute()
temp_dir = script_dir / "temp_zip_extraction"

# Function to log messages to the GUI
def log_message(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)  # Auto-scroll to the bottom
    window.update_idletasks()

# Function to open file dialog
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("ZIP Files", "*.zip")])
    if file_path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)

# Function to repair the save
def RepairSave():
    SavePath = entry_path.get()
    if not SavePath or not os.path.isfile(SavePath):
        messagebox.showerror("Error", "Please select a valid ZIP file.")
        return
    
    try:
        temp_dir.mkdir(exist_ok=True)  # Ensure temp directory exists
        log_message("Extracting ZIP file...")
        
        # Step 1: Extract ZIP
        with zipfile.ZipFile(SavePath, 'r') as zip_file:
            zip_file.extractall(temp_dir)

        # Step 2: Read save version
        target_file = temp_dir / "scene.bb8scene"
        if target_file.exists():
            try:
                with open(target_file, "r", encoding="utf-8-sig") as scenebb8scene:
                    scene_data = json.load(scenebb8scene)
                save_version = scene_data.get("version", "Unknown")
                log_message(f"Save version: {save_version}")
            except json.JSONDecodeError:
                messagebox.showerror("Error", "scene.bb8scene is not a valid JSON file.")
                return
        else:
            messagebox.showerror("Error", "scene.bb8scene not found.")
            return

        # Step 3: Modify files if needed
        if save_version == "0.6.0.1":
            log_message("Modifying save files...")
            target_folder = temp_dir / "bibites"
            if os.path.isdir(target_folder):
                for bibitefilename in os.listdir(target_folder):
                    log_message(f"Attempting to fix {bibitefilename}")
                    bibite_path = target_folder / bibitefilename
                    with open(bibite_path, "r", encoding="utf-8-sig") as bibitefile:
                        bibite = json.load(bibitefile)

                    # Modify MouthMusclesWAG
                    log_message("Increasing Jaw Muscles WAG by removing the e-")
                    MouthMusclesWAG = bibite["genes"]["genes"]["MouthMusclesWAG"]
                    if "e-" in f"{MouthMusclesWAG:e}":
                        exponent = int(f"{MouthMusclesWAG:e}".split("e")[-1])
                        MouthMusclesWAG *= 10 ** abs(exponent)
                    if MouthMusclesWAG == 0:
                        MouthMusclesWAG = 1.0
                    
                    bibite["genes"]["genes"]["MouthMusclesWAG"] = MouthMusclesWAG

                    # Modify EggProduction 
                    log_message("Increasing Egg Production node by 0.4")
                    EggProduction = bibite["brain"]["Nodes"][35]["baseActivation"]
                    EggProduction += 0.4
                    bibite["brain"]["Nodes"][35]["baseActivation"] = EggProduction

                    log_message("Increasing egg Progress by 1 if it is 0.0")
                    eggProgress = bibite["body"]["eggLayer"]["eggProgress"]
                    if eggProgress == 0.0:
                        eggProgress += 1
                    
                    bibite["body"]["eggLayer"]["eggProgress"] = eggProgress

                    with open(bibite_path, "w", encoding="utf-8-sig") as bibitefile:
                        json.dump(bibite, bibitefile, indent=4)

        # Step 4: Recreate the ZIP with modified files
        new_zip_path = SavePath.replace(".zip", "_modified.zip")
        log_message("Creating new ZIP file...")
        with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    zip_file.write(file_path, file_path.relative_to(temp_dir))
        
        # Cleanup temporary files
        log_message("Removing temporary files")
        shutil.rmtree(temp_dir)
        log_message(f"Repair complete! Saved as: {new_zip_path}")
        log_message("You can now load the hopfully fixed save")

    except zipfile.BadZipFile:
        messagebox.showerror("Error", "The selected file is not a valid ZIP file.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# GUI Layout
frame_top = tk.Frame(window)
frame_top.pack(pady=10)

entry_path = tk.Entry(frame_top, width=50)
entry_path.pack(side=tk.LEFT, padx=5)

btn_browse = tk.Button(frame_top, text="Browse", command=select_file)
btn_browse.pack(side=tk.LEFT)

btn_repair = tk.Button(window, text="Repair Save", command=RepairSave, bg="green", fg="white")
btn_repair.pack(pady=10)

log_box = scrolledtext.ScrolledText(window, width=70, height=15, state=tk.NORMAL)
log_box.pack(pady=10)

window.mainloop()
