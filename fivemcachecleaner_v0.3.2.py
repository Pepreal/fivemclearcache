import os
import shutil
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext, filedialog

# --- Module-Level Constants ---

# Folders targeted by the "Clear Cache (Recommended)" option
RECOMMENDED_CACHE_FOLDERS = ("cache", "server-cache", "server-cache-priv", "logs", "crashes")

# Folders targeted only by the "Clear Data Folder (Deep Clean)" option
DEEP_DATA_FOLDERS = ("game-storage", "nui-storage")

# --- Module and OS Check ---
WINDOWS_OS = sys.platform.startswith('win')
try:
    if WINDOWS_OS:
        import winreg
        import ctypes
    WINREG_AVAILABLE = True
    CTYPES_AVAILABLE = True
except ImportError:
    # If modules fail to import, set flags to False
    WINREG_AVAILABLE = False
    CTYPES_AVAILABLE = False

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

def get_mounted_drives():
    """Dynamically gets all mounted drive letters (A: to Z:)."""
    if WINDOWS_OS and CTYPES_AVAILABLE:
        try:
            # Using the Windows API to get mounted drives
            drive_bits = ctypes.cdll.kernel32.GetLogicalDrives()
            drives = []
            for i in range(26):
                if drive_bits & (1 << i):
                    drives.append(f"{chr(65 + i)}:\\")
            return drives
        except Exception:
            # Fallback if ctypes call fails for some reason
            return [f"{d}:\\" for d in "CDEFG"] 
    
    # Fallback for non-Windows or import failure
    return [f"{d}:\\" for d in "CDEFG"] 

# --- Main Application Class (Version 0.3.2) ---

class FiveMCleanerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("FiveM Cache Cleaner V0.3.2")
        self.master.geometry("1000x570")
        
        try:
            # Attempt to set the window icon from a resource file
            self.master.iconbitmap(resource_path("fivem_cleaner.ico"))
        except tk.TclError as e:
            pass 

        self.master.withdraw()
        
        # --- Variables ---
        self.cache_folder = None
        self.fivem_app_path = None
        self.pure_mode_var = tk.IntVar(value=0) 
        self.deep_clean_var = tk.IntVar(value=0) 
        
        # References to GUI elements for state/config updates
        self.clean_button_ref = None 
        self.pure_mode_checkbutton = None 
        self.title_frame = None 
        self.centered_content_frame = None 
        self.progress_frame = None 
        self.path_fg = "" # Theme color variable
        self.size_fg = "" # Theme color variable
        
        # Size tracking variables
        self.recommended_cache_size = 0.0
        self.deep_data_size = 0.0
        
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
        "Version 0.3.2 (22-11-2025)\n\n"
        "This tool is provided as-is and is currently in the testing phase.\n"
        "Use it at your own risk.\n\n"
        "Purpose:\n"
        "This tool is designed to simplify the process of clearing FiveM cache folders for users.\n"
        "The tool is location-aware, meaning it can automatically detect the FiveM installation folder.\n\n"
        "The size displayed updates dynamically based on the 'Deep Clean' checkbox.\n"
        " - **Clear Cache (Default)**: Clears only temporary cache.\n"
        " - **Deep Clean (Optional)**: Clears cache PLUS user settings and login data.\n\n"
        "By continuing, you acknowledge and accept the potential risks.\n\n"
        "© By: Pepreal (Marcus Mosley)"
        )
        response = messagebox.askokcancel("Welcome & Agreement", disclaimer_text)
        return response

    def build_app_gui(self):
        """Builds all GUI components and makes the main window visible."""
        # Configure grid weights
        self.master.grid_rowconfigure(7, weight=1) # Log row is now row 7
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
        
        # Style for the Deep Clean text (red foreground)
        self.style.configure('DeepClean.TCheckbutton', foreground='#dc3545', font=('Arial', 10, 'bold'))
        
        # 1. Normal Cleanup Button Style (Default color)
        self.style.configure('NormalCleanup.TButton', font=('Arial', 11, 'bold')) 

        # 2. Deep Cleanup Button Style (Red prominent text)
        self.style.configure('Cleanup.TButton', foreground='#dc3545', font=('Arial', 11, 'bold'))
        
    def apply_theme_colors(self):
        """Applies the color scheme based on the detected theme_mode."""
        if self.theme_mode == "Dark":
            bg_color = "#333333"
            status_color = "#cccccc"
            title_color = "#81d4fa"
            log_bg = "#1e1e1e"
            
            # Specific colors for status labels
            self.path_fg = "#81d4fa"
            self.size_fg = "#e57373"
        else: # Light Mode
            bg_color = "#f0f0f0"
            status_color = "#555555"
            title_color = "#007bff"
            log_bg = "#ffffff"
            
            # Specific colors for status labels
            self.path_fg = "#007bff"
            self.size_fg = "#dc3545"

        # Apply to main window and frames 
        self.master.config(bg=bg_color)
        for widget in [self.master, self.title_frame, self.status_frame, self.clean_frame, self.progress_frame]:
            if widget:
                widget.config(bg=bg_color)
            
        # These frames were created inside create_widgets, so check if they exist
        try:
            self.centered_content_frame.config(bg=bg_color)
            # pure_mode_checkbutton is now directly on self.master, so no need to config its master frame
        except AttributeError:
             pass 

        # Apply to Text Log
        self.log_text.config(bg=log_bg, fg=status_color)

        # Apply to Labels (Default 'Ready to Search' colors)
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
        
        # --- Row 0: Centered Title and Help Button (Isolated for Perfect Centering) ---
        self.title_frame = tk.Frame(self.master)
        # Use columnspan=2 and sticky 'ew' to ensure it takes full master width for centering
        self.title_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky='ew')
        
        # Configure inner grid weights to center the content
        self.title_frame.grid_columnconfigure(0, weight=1)  # Left Spacer
        self.title_frame.grid_columnconfigure(1, weight=0)  # Title Group (Fixed Size)
        self.title_frame.grid_columnconfigure(2, weight=1)  # Right Spacer
        
        # 1. Inner frame for Title and Help (This group goes into the centered column 1)
        title_help_frame = tk.Frame(self.title_frame)
        title_help_frame.grid(row=0, column=1) 

        # Title Label
        self.title_label = tk.Label(title_help_frame, text="FiveM Cache Cleaner", font=("Arial", 18, "bold"))
        self.title_label.pack(side=tk.LEFT)
        
        # Help Button
        help_button = ttk.Button(title_help_frame, text="?", command=self.show_help, width=2)
        help_button.pack(side=tk.LEFT, padx=(10, 5))
        
        # --- Row 1: Force Pure Mode Checkbox (Moved to its own row, aligned right) ---
        self.pure_mode_checkbutton = ttk.Checkbutton(
            self.master, 
            text="Force Pure Mode (-pure_1)", 
            variable=self.pure_mode_var, 
            onvalue=1, 
            offvalue=0, 
            state=tk.DISABLED,
        )
        # Place it on Row 1, spanned over both columns, sticky to the East (right)
        self.pure_mode_checkbutton.grid(row=1, column=0, columnspan=2, padx=10, sticky='e') 

        
        # --- Row 2: Search Button ---
        self.search_button_ref = ttk.Button(self.master, text="Search for FiveM Cache", command=self.search_cache, width=45, style='Action.TButton')
        self.search_button_ref.grid(row=2, column=0, columnspan=2, pady=(10, 5))
        
        # --- Row 3: Status Labels (Immediate Feedback) ---
        self.status_frame = tk.Frame(self.master)
        self.status_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        # Cache Path Label
        self.path_label = tk.Label(self.status_frame, text="Folder: Ready to Search.", font=("Arial", 10))
        self.path_label.pack(side=tk.LEFT, padx=30)
        
        # Cache Size Label - Will be updated dynamically
        self.size_label = tk.Label(self.status_frame, text="Size: 0.00 MB", font=("Arial", 10))
        self.size_label.pack(side=tk.LEFT, padx=30)
        
        # --- Row 4: Cleaning Options and Start Button (Centered Button + Checkbox) ---
        self.clean_frame = tk.Frame(self.master)
        self.clean_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky='ew')
        
        self.clean_frame.grid_columnconfigure(0, weight=1) 
        self.clean_frame.grid_columnconfigure(1, weight=0) 
        self.clean_frame.grid_columnconfigure(2, weight=1) 
        
        self.centered_content_frame = tk.Frame(self.clean_frame)
        self.centered_content_frame.grid(row=0, column=1, sticky='') 
        
        self.clean_button_ref = ttk.Button(
            self.centered_content_frame, 
            text="Start Cleanup (Clear Cache Only)", 
            command=lambda: self.start_cleaning(self.get_current_clean_size()), 
            width=35,
            style='NormalCleanup.TButton', 
            state=tk.DISABLED
        )
        self.clean_button_ref.pack(side=tk.LEFT, padx=(0, 5), pady=0) 

        self.deep_clean_checkbutton = ttk.Checkbutton(
            self.centered_content_frame, 
            text="Deep Clean (Removes login/settings)", 
            variable=self.deep_clean_var,
            style='DeepClean.TCheckbutton', 
            command=self.deep_clean_confirmation 
        )
        self.deep_clean_checkbutton.pack(side=tk.LEFT, padx=(5, 0), pady=0) 


        # --- Row 5: Progress Bar Frame (Managed via grid_forget on the Frame) ---
        self.progress_frame = tk.Frame(self.master)
        self.progress_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Progress bar inside the frame
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=900, mode="indeterminate")
        self.progress_bar.pack(side=tk.TOP)
        self.progress_frame.grid_forget() # Initially hide the entire frame
        
        # --- Row 6: Launch Mode Display Label ---
        self.mode_display_label = tk.Label(self.master, font=("Arial", 10, "bold"))
        self.mode_display_label.grid(row=6, column=0, columnspan=2, pady=(5, 10))
        

        # --- Row 7: Log Text Area ---
        self.log_text = scrolledtext.ScrolledText(self.master, height=12, width=120, state='normal', font=("Consolas", 9))
        self.log_text.grid(row=7, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")
        
        # Ensure all container backgrounds match the master background color
        title_help_frame.config(bg=self.master['bg'])
        self.centered_content_frame.config(bg=self.master['bg'])


    def deep_clean_confirmation(self):
        """Shows a warning popup when the deep clean checkbox is checked and updates size."""
        if self.deep_clean_var.get() == 1:
            response = messagebox.askyesno(
                "Deep Clean Warning: Requires Re-Login",
                "**You have selected Deep Clean.**\n\n"
                "This removes your cached login details (`nui-storage`), local game settings (`game-storage`), and all temporary cache.\n\n"
                "You will be forced to **re-log into FiveM** and may lose local configuration data.\n\n"
                "Do you wish to proceed with Deep Clean?"
            )
            if not response:
                # If the user clicks No, uncheck the box immediately
                self.deep_clean_var.set(0)
        
        # Update the main clean button text and size based on the choice
        self.update_clean_button_text()
        self.update_displayed_size()


    def log_message(self, msg):
        """Logs messages to the GUI log window."""
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def show_help(self):
        """Displays a help box explaining the cleaning and launch modes."""
        help_text = (
            "## Cleaning Options\n\n"
            "The cleaner targets three main areas of your FiveM installation. We recommend closing FiveM completely before cleaning.\n\n"
            "1. **Clear Cache (Default Mode):**\n"
            "This is the standard fix for most issues (texture glitches, loading problems). It safely removes transient files (cache, logs, crashes) that FiveM generates on every launch. It keeps your login and local settings intact.\n\n"
            "2. **Deep Clean (Check the Box):**\n"
            "This is an aggressive clean for persistent, critical errors. It deletes ALL cache files PLUS the 'nui-storage' (your CFX login profile) and 'game-storage' (your local settings).\n"
            "**WARNING:** You will be forced to re-log into FiveM and may lose local configuration data.\n\n"
            "## Launch Mode\n\n"
            "**✅ Checked ('Force Pure Mode'):**\n"
            "FiveM is launched with the **-pure_1** argument. This tells FiveM to ignore local file modifications and custom scripts. This is often necessary when joining servers with strict rules or for troubleshooting mod-related crashes.\n\n"
            "**⬜ Not Checked (Default):**\n"
            "FiveM will start normally, loading any mods or custom files you have installed."
        )
        messagebox.showinfo("FiveM Cleaner - How to Use", help_text)

    
    def _get_full_cache_paths(self, folder_names):
        """
        Calculates the full, absolute paths for a list of cache/data folder names.
        This centralizes the logic for determining if a folder is in FiveM.app or FiveM.app/data.
        """
        if not self.cache_folder or not self.fivem_app_path:
            return []

        paths = []
        for name in folder_names:
            # logs and crashes are in the FiveM.app directory
            if name in ("logs", "crashes"):
                paths.append(os.path.join(self.fivem_app_path, name))
            # All other folders are inside the 'data' directory (self.cache_folder)
            else:
                paths.append(os.path.join(self.cache_folder, name))
        return paths


    def find_fivem_paths(self):
        """Search for the FiveM cache folder and derive the FiveM.app path."""
        
        # Define the target subdirectory path relative to the drive root or AppData
        possible_sub_path = os.path.join("FiveM", "FiveM.app", "data")
        
        # 1. Check Standard AppData Path (Highest Priority)
        appdata_path = os.environ.get('LOCALAPPDATA')
        if appdata_path:
            default_cache_path = os.path.join(appdata_path, "FiveM", "FiveM.app", "data")
            if os.path.exists(default_cache_path):
                self.fivem_app_path = os.path.dirname(default_cache_path)
                return default_cache_path
        
        # 2. Dynamic Search on ALL Mounted Drives (including C: root)
        self.log_message("Standard path not found. Starting dynamic search on all mounted drives...")
        
        # Get all mounted drives dynamically
        drives = get_mounted_drives()
        
        for drive in drives:
            # Check the FiveM sub-path relative to the drive root
            full_cache_path = os.path.join(drive, possible_sub_path)
            
            # Check for the target 'data' folder
            if os.path.exists(full_cache_path):
                self.fivem_app_path = os.path.dirname(full_cache_path)
                return full_cache_path
            
        return None

    def calculate_and_log_cache_size(self):
        """Calculates and logs the size of the specific cache folders."""
        
        if not self.cache_folder or not self.fivem_app_path:
            self.recommended_cache_size = 0.0
            self.deep_data_size = 0.0
            return 0.0

        # Reset size tracking variables
        self.recommended_cache_size = 0.0
        self.deep_data_size = 0.0

        # Build list of all folders to check using the optimized helper
        all_folders_to_check_names = DEEP_DATA_FOLDERS + RECOMMENDED_CACHE_FOLDERS
        all_folders_to_check = self._get_full_cache_paths(all_folders_to_check_names)
        
        total_size = 0.0
        
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
                
                # Assign size to the correct tracking variable
                if folder_name in DEEP_DATA_FOLDERS:
                    self.deep_data_size += size
                else:
                    self.recommended_cache_size += size
                
                # Log line 
                log_line = f"{folder_name:<25} {category_for_alignment:<8} {size:>10.2f}"
                self.log_message(log_line)
                total_size += size
            else:
                # Log missing folders with aligned placeholder
                log_line = f"{folder_name:<25} {category_for_alignment:<8} {'0.00':>10} [NOT FOUND]"
                self.log_message(log_line)
        
        self.log_message("-" * 45)
        self.log_message(f"Total current cache size (All folders): {total_size:.2f} MB")
        self.log_message(f"Cache Size (Default Clean): {self.recommended_cache_size:.2f} MB")
        self.log_message(f"Deep Data Size (Additional): {self.deep_data_size:.2f} MB")

        return self.recommended_cache_size

    def get_current_clean_size(self):
        """Returns the size to be cleaned based on the Deep Clean checkbox state."""
        if self.deep_clean_var.get() == 1:
            return self.recommended_cache_size + self.deep_data_size
        else:
            return self.recommended_cache_size

    def update_displayed_size(self):
        """Updates the size label next to 'Folder:' based on Deep Clean checkbox state."""
        current_size = self.get_current_clean_size()
        self.size_label.config(text=f"Size: {current_size:.2f} MB", foreground=self.size_fg)


    def search_cache(self):
        """Searches for the cache folder, updates the log, and enables buttons."""
        
        self.search_button_ref.config(state=tk.DISABLED)
        # Clear the log window on new search
        self.log_text.delete('1.0', tk.END)
        self.check_and_log_theme_status()
        
        try:
            self.log_message("Starting search for FiveM cache folder...")
            self.cache_folder = self.find_fivem_paths()
            
            if self.cache_folder:
                self.log_message(f"Cache folder found: {self.cache_folder}")
                
                # Calculate sizes and get the default size (recommended cache size)
                default_initial_size = self.calculate_and_log_cache_size()
                
                self.display_clean_buttons(default_initial_size)
            else:
                self.log_message("Cache folder not found automatically. Prompting for manual selection.")
                
                # Use theme-specific colors for 'Not Found' status
                self.path_label.config(text="Folder: Not Found. Please Select Manually.", foreground=self.size_fg)
                self.size_label.config(text="Size: 0.00 MB", foreground=self.size_fg)

                # Manual selection fallback
                folder_selected = filedialog.askdirectory(title="Select FiveM Data Folder (e.g., FiveM.app/data)")
                if folder_selected and os.path.basename(folder_selected) == "data":
                    self.cache_folder = folder_selected
                    self.fivem_app_path = os.path.dirname(folder_selected)
                    
                    self.log_message(f"Manual folder selected: {self.cache_folder}")
                    default_initial_size = self.calculate_and_log_cache_size()
                    self.display_clean_buttons(default_initial_size)
                else:
                    self.log_message("Invalid folder selected or selection cancelled.")
                    # Revert to standard ready state colors
                    self.path_label.config(text="Folder: Ready to Search.", fg=self.master.cget('bg')) 
                    self.size_label.config(text="Size: 0.00 MB", fg=self.master.cget('bg'))


        except Exception as e:
            error_msg = "CRITICAL RUNTIME ERROR in search_cache: %s" % e
            messagebox.showerror("Runtime Error", error_msg)
            self.log_message(error_msg)
        finally:
            self.search_button_ref.config(state=tk.NORMAL)

    def update_mode_label(self, *args):
        """Updates the launch mode display label based on the Checkbutton state."""
        if self.pure_mode_var.get() == 1:
            text = "Launch Mode: PURE MODE (-pure_1)"
            color = "#ff7f50" # Coral
        else:
            text = "Launch Mode: NORMAL MODE (Default)"
            color = "#32cd32" # Lime Green

        self.mode_display_label.config(text=text, foreground=color)
        
    def update_clean_button_text(self, *args):
        """
        Updates the main cleanup button text and color based on the Deep Clean state.
        """
        if self.deep_clean_var.get() == 1:
            text = "Start Cleanup (DEEP CLEAN MODE)"
            style = 'Cleanup.TButton' # Red style
        else:
            text = "Start Cleanup (Clear Cache Only)"
            style = 'NormalCleanup.TButton' # Default style
        
        if self.clean_button_ref:
            self.clean_button_ref.config(text=text, style=style)


    def set_clean_button_state(self, state):
        """Enables or disables the clean buttons and deep clean checkbox."""
        if self.clean_button_ref:
            self.clean_button_ref.config(state=state)
        self.deep_clean_checkbutton.config(state=state)
        self.pure_mode_checkbutton.config(state=state)

    def display_clean_buttons(self, initial_size):
        """Updates the status labels and enables the clean/launch options."""
        
        # Use theme-specific colors for path and size labels
        self.path_label.config(text=f"Folder: {self.cache_folder}", foreground=self.path_fg)
        
        # Initial size update (Deep Clean is off by default)
        self.update_displayed_size() 
        
        # Enable relevant UI elements
        self.clean_button_ref.config(state=tk.NORMAL)
        self.deep_clean_checkbutton.config(state=tk.NORMAL)
        self.pure_mode_checkbutton.config(state=tk.NORMAL)
        
        # Initial text/color update
        self.update_clean_button_text()


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
        # Start indeterminate progress bar by showing the progress frame
        self.progress_frame.grid(row=5, column=0, columnspan=2, pady=10) # Row 5 in new layout
        self.progress_bar.start(10)
        
        for folder in folders:
            self.safe_remove(folder)

        self.progress_bar.stop()
        self.progress_frame.grid_forget() # Hide the progress frame

    def start_cleaning(self, initial_size):
        """Starts the cleaning process based on the Deep Clean checkbox state."""
        
        is_deep_clean = (self.deep_clean_var.get() == 1)
        
        # Disable all UI elements during cleanup
        self.set_clean_button_state(tk.DISABLED)
        self.search_button_ref.config(state=tk.DISABLED)
        
        # Determine the set of folders to delete
        if is_deep_clean:
            self.log_message(f"Starting DEEP CLEANUP of {initial_size:.2f} MB...")
            all_folders_to_clean = RECOMMENDED_CACHE_FOLDERS + DEEP_DATA_FOLDERS
        else:
            self.log_message(f"Starting ESSENTIAL CACHE CLEANUP of {initial_size:.2f} MB...")
            all_folders_to_clean = RECOMMENDED_CACHE_FOLDERS
        
        # Build the final list of full paths using the optimized helper
        folders_to_delete = self._get_full_cache_paths(all_folders_to_clean)
        
        self.delete_folders(folders_to_delete)
        
        if is_deep_clean:
            messagebox.showinfo("Success", "Deep clean completed successfully! Remember to re-log into FiveM.")
        else:
            messagebox.showinfo("Success", "Essential cache cleared successfully!")
            
        self.log_message("Cleanup process completed.")
        
        self.launch_fivem_prompt()

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

        mode_pure = (self.pure_mode_var.get() == 1)
        
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
            # We use subprocess.Popen to launch FiveM and allow the cleaner to close/finish
            subprocess.Popen(cmd_list, close_fds=True) 
            self.master.destroy()
        except Exception as e:
            messagebox.showerror("Launch Error", f"An error occurred while launching FiveM: {e}")
            self.log_message(f"Launch failed: {e}")

    def launch_fivem_prompt(self):
        """Asks the user if they want to launch FiveM."""
        
        self.search_button_ref.config(state=tk.NORMAL)
        self.set_clean_button_state(tk.NORMAL) # Re-enable clean options and launch mode
        
        # Update the displayed size one last time (will show 0.00 if cleaning was successful)
        self.update_displayed_size()

        mode_text = "PURE MODE" if self.pure_mode_var.get() == 1 else "NORMAL MODE"
        
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
    # Bind the Deep Clean Checkbox
    app.deep_clean_var.trace_add("write", app.deep_clean_confirmation) 
    # Bind the Pure Mode variable
    app.pure_mode_var.trace_add("write", app.update_mode_label)
    root.mainloop()

if __name__ == "__main__":
    run_cleaner()
