import os
import shutil
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext, filedialog

# --- PyInstaller Utility Function ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # For development environment, use the script's directory
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

# --- Module and OS Check ---
WINDOWS_OS = sys.platform.startswith('win')
try:
    if WINDOWS_OS:
        import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False
    
# --- Folder Categorization for Logging ---
# Folders targeted by the "Clear Cache (Recommended)" option
RECOMMENDED_CACHE_FOLDERS = ["cache", "server-cache", "server-cache-priv", "logs", "crashes"]

# Folders targeted only by the "Clear Data Folder (Deep Clean)" option
DEEP_DATA_FOLDERS = ["game-storage", "nui-storage"]

# --- Utility Functions ---

def get_folder_size_iterative(folder):
    """Calculates the size of a folder in MB using iterative os.walk."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except Exception:
                        pass
    except Exception:
        return 0
        
    return total_size / (1024 * 1024)

def check_windows_theme():
    """Reads the Windows registry to determine if Dark Mode is enabled."""
    if not WINDOWS_OS or not WINREG_AVAILABLE:
        return "Dark"
        
    registry_path = r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
    key_name = 'AppsUseLightTheme'
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
        value, _ = winreg.QueryValueEx(key, key_name)
        winreg.CloseKey(key)
        
        return "Light" if value == 1 else "Dark"
        
    except Exception:
        return "Dark"

# --- Main Application Class (Version 0.4) ---

class FiveMCleanerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("FiveM Cache Cleaner V0.4")
        self.master.geometry("1000x700")
        
        # FIX: Removed the print() statement in the exception block.
        try:
            self.master.iconbitmap(resource_path("fivem_cleaner.ico"))
        except tk.TclError as e:
            # We use 'pass' to silently ignore the error if the icon fails to load
            pass 

        self.master.withdraw()
        
        # --- Variables ---
        self.cache_folder = None
        self.fivem_app_path = None
        self.mode_var = tk.IntVar(value=0)
        self.clean_buttons_list = []
        self.initial_size = 0
        
        self.theme_mode = check_windows_theme()

        # --- Styling ---
        self.style = ttk.Style(master)
        self.style.theme_use('clam')
        self.setup_styles()
        
        if self.show_disclaimer():
            self.build_app_gui()
        else:
            sys.exit()

    def show_disclaimer(self):
        """Displays a disclaimer and returns True if accepted, False if cancelled."""
        disclaimer_text = (
        "Version 0.4 (22-11-2025)\n\n"
        "This tool is provided as-is and is currently in the testing phase.\n"
        "Use it at your own risk.\n\n"
        "Purpose:\n"
        "This tool is designed to simplify the process of clearing FiveM cache folders for users.\n"
        "Users do not need any technical knowledge to clear the FiveM cache folders.\n"
        "The tool is location-aware, meaning it can automatically detect the FiveM installation folder, even if it is installed in a non-default location. However, if FiveM is installed in a non-default location, the search process may take a bit longer.\n\n"
        "The tool provides information about the size and total size of the cache folders.\n"
        "Once the search is complete, it will display the total size of the cache folders. \n"
        "You will have two options to choose from:\n\n"
        "- Clear Cache: This will only clear the cache of your FiveM installation.\n"
        "- Clear Data Folder: This will clear both the cache and the build of FiveM. Only proceed if you are encountering issues with FiveM or want to perform a deep clean. \n\n"
        "After the tool is done, it will ask if you want to start FiveM.\n\n"
        "By continuing, you acknowledge and accept the potential risks.\n\n"
        "© By: Pepreal (Marcus Mosley)"
        )
        response = messagebox.askokcancel("Welcome & Agreement", disclaimer_text)
        return response

    def build_app_gui(self):
        """Builds all GUI components and makes the main window visible."""
        # Configure grid weights
        self.master.grid_rowconfigure(6, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        
        self.create_widgets()
        self.apply_theme_colors()
        self.check_and_log_theme_status()
        
        self.master.deiconify()
    
    def setup_styles(self):
        """Custom Ttk styles for a polished look."""
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('TLabel', font=('Arial', 10))
        self.style.configure('Title.TLabel', font=('Arial', 18, 'bold'))
        self.style.configure('Action.TButton', font=('Arial', 11, 'bold'))
        
    def apply_theme_colors(self):
        """Applies the color scheme based on the detected theme_mode."""
        if self.theme_mode == "Dark":
            bg_color = "#333333"
            status_color = "#cccccc"
            title_color = "#81d4fa"
            log_bg = "#1e1e1e"
        else: # Light Mode
            bg_color = "#f0f0f0"
            status_color = "#555555"
            title_color = "#007bff"
            log_bg = "#ffffff"

        # Apply to main window and frames
        self.master.config(bg=bg_color)
        for widget in [self.master, self.title_frame, self.status_frame, self.launch_mode_frame]:
            widget.config(bg=bg_color)

        # Apply to Text Log
        self.log_text.config(bg=log_bg, fg=status_color)

        # Apply to Labels (using status_color for generic text)
        self.path_label.config(bg=bg_color, fg=status_color)
        self.size_label.config(bg=bg_color, fg=status_color)
        self.mode_display_label.config(bg=bg_color)
        self.title_label.config(bg=bg_color, fg=title_color)

        # Re-run mode update to refresh colors
        self.update_mode_label()

    def check_and_log_theme_status(self):
        """Logs the status of theme detection based on imports."""
        self.log_message("--- Theme Detection Status ---")
        if WINDOWS_OS and WINREG_AVAILABLE:
            self.log_message(f"SUCCESS: Windows theme detected as **{self.theme_mode.upper()}**.")
        elif WINDOWS_OS and not WINREG_AVAILABLE:
            self.log_message(f"WARNING: Automatic theme detection failed (winreg module missing/failed to import).")
            self.log_message("Defaulting to **DARK MODE**.")
        else:
            self.log_message(f"INFO: Non-Windows OS detected ({sys.platform}). Defaulting to **DARK MODE**.")
        self.log_message("---------------------------------------------")


    def create_widgets(self):
        # --- Row 0: Title and Help Button ---
        self.title_frame = tk.Frame(self.master)
        self.title_frame.grid(row=0, column=0, columnspan=2, pady=10)

        self.title_label = tk.Label(self.title_frame, text="FiveM Cache Cleaner", font=("Arial", 18, "bold"))
        self.title_label.pack(side=tk.LEFT)
        
        help_button = ttk.Button(self.title_frame, text="?", command=self.show_help, width=2)
        help_button.pack(side=tk.LEFT, padx=(10, 5))
        
        # --- Row 1: Search Button ---
        self.search_button_ref = ttk.Button(self.master, text="1. Search for FiveM Cache", command=self.search_cache, width=45, style='Action.TButton')
        self.search_button_ref.grid(row=1, column=0, columnspan=2, pady=(10, 5))
        
        # --- Row 2: Status Labels (Immediate Feedback) ---
        self.status_frame = tk.Frame(self.master)
        self.status_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        # Cache Path Label
        self.path_label = tk.Label(self.status_frame, text="Folder: Ready to Search.", font=("Arial", 10))
        self.path_label.pack(side=tk.LEFT, padx=30)
        
        # Cache Size Label
        self.size_label = tk.Label(self.status_frame, text="Size: 0.00 MB", font=("Arial", 10))
        self.size_label.pack(side=tk.LEFT, padx=30)
        
        # --- Row 3: Cleaning Buttons (Dynamically displayed) ---
        
        # --- Row 4: Progress Bar ---
        # FIX F: Change progress bar mode to indeterminate for deletion feedback
        self.progress_bar = ttk.Progressbar(self.master, orient="horizontal", length=700, mode="indeterminate")
        self.progress_bar.grid(row=4, column=0, columnspan=2, pady=10)
        self.progress_bar.grid_forget()
        
        # --- Row 5: Launch Mode Selection ---
        self.launch_mode_frame = tk.Frame(self.master)
        self.launch_mode_frame.grid(row=5, column=0, columnspan=2, pady=(5, 10))

        self.mode_var.trace_add("write", self.update_mode_label)

        # Pure Mode Checkbutton
        self.pure_mode_checkbutton = ttk.Checkbutton(self.launch_mode_frame, text="Force Pure Mode Launch (Set -pure_1)", variable=self.mode_var, onvalue=1, offvalue=0)
        self.pure_mode_checkbutton.pack(side=tk.LEFT, padx=15)
        
        # Mode Display Label (Clear visual confirmation)
        self.mode_display_label = tk.Label(self.launch_mode_frame, font=("Arial", 10, "bold"))
        self.mode_display_label.pack(side=tk.LEFT, padx=15)

        # --- Row 6: Log Text Area ---
        self.log_text = scrolledtext.ScrolledText(self.master, height=12, width=90, state='normal', font=("Consolas", 9))
        self.log_text.grid(row=6, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")


    def log_message(self, msg):
        """Logs messages to the GUI log window."""
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def show_help(self):
        """Displays a help box explaining the cleaning and launch modes."""
        # --- Final Updated Help Text ---
        help_text = (
            "## Cleaning Options\n\n"
            "The cleaner targets three main areas of your FiveM installation. We recommend closing FiveM completely before cleaning.\n\n"
            "1. **Clear Cache (Recommended):**\n"
            "This is the standard fix for most issues (texture glitches, loading problems). It safely removes transient files (cache, logs, crashes) that FiveM generates on every launch. It keeps your login and local settings intact.\n\n"
            "2. **Clear Data Folder (Deep Clean):**\n"
            "This is an aggressive clean for persistent, critical errors. It deletes ALL cache files PLUS the 'nui-storage' (your CFX login profile) and 'game-storage' (your local settings).\n"
            "**WARNING:** You will be forced to re-log into FiveM and may lose local configuration data.\n\n"
            "## Launch Mode\n\n"
            "**✅ Checked**\n"
            "FiveM is launched with the **-pure_1** argument. This tells FiveM to ignore local file modifications and custom scripts. This is often necessary when joining servers with strict rules or for troubleshooting mod-related crashes.\n\n"
            "**⬜ Not Checked**\n"
            "FiveM will start normally, loading any mods or custom files you have installed."
        )
        # -------------------------
        messagebox.showinfo("FiveM Cleaner - How to Use", help_text)

    def find_fivem_paths(self):
        """Search for the FiveM cache folder and derive the FiveM.app path."""
        # 1. Check standard AppData path
        appdata_path = os.environ.get('LOCALAPPDATA')
        if appdata_path:
            default_cache_path = os.path.join(appdata_path, "FiveM", "FiveM.app", "data")
            if os.path.exists(default_cache_path):
                self.fivem_app_path = os.path.dirname(default_cache_path)
                return default_cache_path
        
        # 2. Check for custom installation (via common path structure)
        possible_sub_path = os.path.join("FiveM", "FiveM.app", "data")
        
        # FIX A: Limit drive scanning to common local drives (C-F)
        drives = [f"{d}:\\" for d in "CDEF" if os.path.exists(f"{d}:\\")]
        
        for drive in drives:
            full_cache_path = os.path.join(drive, possible_sub_path)
            if os.path.exists(full_cache_path):
                self.fivem_app_path = os.path.dirname(full_cache_path)
                return full_cache_path
        
        return None

    def calculate_and_log_cache_size(self):
        """Calculates and logs the size of the specific cache folders, labeling them (CACHE) or (DATA)."""
        
        if not self.cache_folder or not self.fivem_app_path:
            self.initial_size = 0
            return 0

        # Define all folders we care about, with their location paths
        data_folders_in_data = [os.path.join(self.cache_folder, f) for f in DEEP_DATA_FOLDERS]
        cache_folders_in_data = [os.path.join(self.cache_folder, f) for f in ["cache", "server-cache", "server-cache-priv"]]
        cache_folders_in_app = [os.path.join(self.fivem_app_path, f) for f in ["logs", "crashes"]]

        # Combine all folder paths for iteration
        all_folders_to_check = cache_folders_in_data + data_folders_in_data + cache_folders_in_app
        
        total_size = 0
        
        self.log_message("--- Analyzing Cache Folders ---")
        
        # Log the header for clarity (25 + 1 + 8 + 1 + 10 = 45 characters)
        self.log_message(f"{'Folder':<25} {'Category':<8} {'Size (MB)':>10}")
        self.log_message("-" * 45)
        
        for folder_path in all_folders_to_check:
            folder_name = os.path.basename(folder_path)
            
            if folder_name in DEEP_DATA_FOLDERS:
                category_raw = "(DATA)"
            else:
                category_raw = "(CACHE)"
                
            category_for_alignment = category_raw

            if os.path.exists(folder_path):
                size = get_folder_size_iterative(folder_path)
                
                # Corrected LOG LINE SYNTAX for right-aligned float with 2 decimals
                log_line = f"{folder_name:<25} {category_for_alignment:<8} {size:>10.2f}"
                self.log_message(log_line)
                total_size += size
            else:
                # FIX E: Log missing folders with aligned placeholder
                log_line = f"{folder_name:<25} {category_for_alignment:<8} {'0.00':>10} [NOT FOUND]"
                self.log_message(log_line)
        
        self.log_message("-" * 45)
        self.initial_size = total_size
        self.log_message(f"Total current cache size: {self.initial_size:.2f} MB")
        return self.initial_size

    def search_cache(self):
        """Searches for the cache folder, updates the log, and displays buttons."""
        
        self.search_button_ref.config(state=tk.DISABLED)
        # FIX D: Clear the log window on new search
        self.log_text.delete('1.0', tk.END)
        self.check_and_log_theme_status()
        
        try:
            self.log_message("Starting search for FiveM cache folder...")
            self.cache_folder = self.find_fivem_paths()
            
            if self.cache_folder:
                self.log_message(f"Cache folder found: {self.cache_folder}")
                
                initial_size = self.calculate_and_log_cache_size()
                self.display_clean_buttons(initial_size)
            else:
                self.log_message("Cache folder not found automatically. Prompting for manual selection.")
                
                status_fg = "#dc3545" if self.theme_mode == "Light" else "#e57373"
                self.path_label.config(text="Folder: Not Found. Please Select Manually.", foreground=status_fg)
                self.size_label.config(text="Size: 0.00 MB", foreground=status_fg)

                # Manual selection fallback
                folder_selected = filedialog.askdirectory(title="Select FiveM Data Folder (e.g., FiveM.app/data)")
                if folder_selected and os.path.basename(folder_selected) == "data":
                    self.cache_folder = folder_selected
                    self.fivem_app_path = os.path.dirname(folder_selected)
                    
                    self.log_message(f"Manual folder selected: {self.cache_folder}")
                    initial_size = self.calculate_and_log_cache_size()
                    self.display_clean_buttons(initial_size)
                else:
                    self.log_message("Invalid folder selected or selection cancelled.")
                    self.path_label.config(text="Folder: Ready to Search.", foreground="gray")

        except Exception as e:
            error_msg = "CRITICAL RUNTIME ERROR in search_cache: %s" % e
            messagebox.showerror("Runtime Error", error_msg)
            self.log_message(error_msg)
        finally:
            self.search_button_ref.config(state=tk.NORMAL)

    def update_mode_label(self, *args):
        """Updates the launch mode display label based on the Checkbutton state."""
        if self.mode_var.get() == 1:
            text = "Launch Mode: PURE MODE (-pure_1)"
            color = "#ff7f50" # Coral
        else:
            text = "Launch Mode: NORMAL MODE (Default)"
            color = "#32cd32" # Lime Green

        self.mode_display_label.config(text=text, foreground=color)

    def set_clean_button_state(self, state):
        """Enables or disables the clean buttons."""
        for button in self.clean_buttons_list:
            button.config(state=state)
        # FIX C: Also disable/enable the launch mode checkbutton
        self.pure_mode_checkbutton.config(state=state)

    def display_clean_buttons(self, initial_size):
        """Displays the two cleaning buttons and updates the status labels."""
        
        path_fg = "#007bff" if self.theme_mode == "Light" else "#81d4fa"
        size_fg = "#dc3545" if self.theme_mode == "Light" else "#e57373"
        
        # Update Status Labels
        self.path_label.config(text=f"Folder: {self.cache_folder}", foreground=path_fg)
        self.size_label.config(text=f"Size: {initial_size:.2f} MB", foreground=size_fg)
        
        # Clear any old references and hide existing buttons
        for button in self.clean_buttons_list:
            button.grid_forget()
        self.clean_buttons_list.clear()

        # Clean buttons are in Row 3 
        button1 = ttk.Button(self.master, text="2. Clear Cache (Recommended)", command=lambda: self.start_cleaning_part1(initial_size), width=35)
        button1.grid(row=3, column=0, pady=10, padx=5, sticky='e')

        button2 = ttk.Button(self.master, text="3. Clear Data Folder (Deep Clean)", command=lambda: self.start_cleaning_part2(initial_size), width=35)
        button2.grid(row=3, column=1, pady=10, padx=5, sticky='w')
        
        self.clean_buttons_list.append(button1)
        self.clean_buttons_list.append(button2)

    def safe_remove(self, path):
        """Remove a folder or file safely, providing detailed logs."""
        folder_name = os.path.basename(path)
        
        if not os.path.exists(path):
            self.log_message(f"Skipped: {folder_name} (Not found)")
            return
            
        self.log_message(f"Attempting to delete: {folder_name}")
        
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.log_message(f"Successfully deleted: {folder_name}")
        except PermissionError:
            self.log_message(f"ERROR: Permission denied. Close FiveM if it's running.")
            messagebox.showwarning("Permission Warning", f"Permission denied for {folder_name}. Ensure FiveM is completely closed.")
        except Exception as e:
            self.log_message(f"ERROR: Failed to delete {folder_name}. {e}")
            messagebox.showwarning("Deletion Error", f"Failed to delete {folder_name}. Details: {e}")

    def delete_folders(self, folders):
        """Deletes a list of folders and updates the progress bar (indeterminate mode)."""
        # FIX F: Start indeterminate progress bar
        self.progress_bar.start(10)
        
        for folder in folders:
            self.safe_remove(folder)

        self.progress_bar.stop()

    def start_cleaning_part1(self, initial_size):
        """Starts cleaning process for 'Clear Cache' (Recommended)."""
        # FIX C: Disable all UI elements during cleanup
        self.set_clean_button_state(tk.DISABLED)
        self.search_button_ref.config(state=tk.DISABLED)
        
        self.log_message(f"Starting essential cache cleanup of {initial_size:.2f} MB...")
        
        self.progress_bar.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Build the list of folders to delete (Cache only)
        folders_to_delete = []
        for folder_name in RECOMMENDED_CACHE_FOLDERS:
            if folder_name in ["logs", "crashes"]:
                folders_to_delete.append(os.path.join(self.fivem_app_path, folder_name))
            else:
                folders_to_delete.append(os.path.join(self.cache_folder, folder_name))
        
        self.delete_folders(folders_to_delete)
        self.progress_bar['value'] = 0
        self.progress_bar.grid_forget()
        
        messagebox.showinfo("Success", "Essential cache cleared successfully!")
        self.log_message("Cache cleanup completed.")
        
        self.launch_fivem_prompt()

    def start_cleaning_part2(self, initial_size):
        """Starts cleaning process for 'Clear Data Folder' (Deep Clean)."""
        response = messagebox.askyesno(
        "Deep Clean Warning",
        "**Are you sure you want to perform a Deep Clean?**\n\n"
        "This process removes all cache and data folders, including **nui-storage** (CFX login) and **game-storage** (Local Settings).\n\n"
        "You will be required to re-log into FiveM and set up your launcher preferences again.\n\n"
        "**Only proceed if the Recommended Clean did not solve your issue.**"
        )
        
        if response:
            # FIX C: Disable all UI elements during cleanup
            self.set_clean_button_state(tk.DISABLED)
            self.search_button_ref.config(state=tk.DISABLED)
            self.log_message(f"Starting deep cache cleanup of {initial_size:.2f} MB...")
            
            self.progress_bar.grid(row=4, column=0, columnspan=2, pady=10)
            
            # Combine all folders (Cache + Data)
            all_folders = RECOMMENDED_CACHE_FOLDERS + DEEP_DATA_FOLDERS

            folders_to_delete = []
            for folder_name in all_folders:
                if folder_name in ["logs", "crashes"]:
                    folders_to_delete.append(os.path.join(self.fivem_app_path, folder_name))
                else:
                    folders_to_delete.append(os.path.join(self.cache_folder, folder_name))
            
            self.delete_folders(folders_to_delete)
            self.progress_bar['value'] = 0
            self.progress_bar.grid_forget()

            messagebox.showinfo("Success", "Deep clean completed successfully!")
            self.log_message("Deep cache cleanup completed.")
            
            self.launch_fivem_prompt()
        else:
            self.log_message("Deep clean cancelled by user.")
            self.search_button_ref.config(state=tk.NORMAL)
            self.set_clean_button_state(tk.NORMAL)

    def find_fivem_exe(self):
        """Derives the FiveM.exe path from the FiveM.app path."""
        # Check based on where FiveM.app was found 
        if self.fivem_app_path:
            base_install_dir = os.path.dirname(self.fivem_app_path) 
            exe_path = os.path.join(base_install_dir, "FiveM.exe")
            if os.path.exists(exe_path):
                return exe_path
        
        # Fallback check for the standard AppData location
        appdata_path = os.environ.get('LOCALAPPDATA')
        if appdata_path:
            exe_path_default = os.path.join(appdata_path, "FiveM", "FiveM.exe")
            if os.path.exists(exe_path_default):
                return exe_path_default
        
        return None

    def launch_fivem(self):
        """Launches FiveM using subprocess.Popen."""
        exe_path = self.find_fivem_exe()
        if not exe_path:
            messagebox.showerror("Launch Error", "FiveM.exe not found.")
            self.log_message("Launch failed: FiveM.exe not found.")
            return

        mode_pure = (self.mode_var.get() == 1)
        
        if mode_pure:
            launch_args = "-pure_1" 
            mode_text = "PURE MODE"
            cmd_list = [exe_path, launch_args] 
        else:
            launch_args = ""
            mode_text = "NORMAL MODE"
            cmd_list = [exe_path] 

        self.log_message(f"Launching FiveM in {mode_text}.")
        self.log_message(f"Execution command: \"{exe_path}\" {launch_args}")
        
        try:
            subprocess.Popen(cmd_list, close_fds=True) 
            self.master.destroy()
        except Exception as e:
            messagebox.showerror("Launch Error", f"An error occurred while launching FiveM: {e}")
            self.log_message(f"Launch failed: {e}")

    def launch_fivem_prompt(self):
        """Asks the user if they want to launch FiveM."""
        
        self.search_button_ref.config(state=tk.NORMAL)
        self.set_clean_button_state(tk.NORMAL) # Re-enable clean buttons and launch option
        
        mode_text = "PURE MODE" if self.mode_var.get() == 1 else "NORMAL MODE"
        
        response = messagebox.askyesno(
            "Launch FiveM", 
            f"Cleanup complete. Do you want to launch FiveM now in {mode_text}?"
        )

        if response:
            self.launch_fivem() 
        else:
            self.log_message("FiveM launch cancelled by user. Program remains open.")

# --- Execution ---

def run_cleaner():
    """Starts the application by creating the root and the main app instance."""
    root = tk.Tk()
    app = FiveMCleanerApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_cleaner()
