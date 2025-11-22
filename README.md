# ✨ FiveM Cache Cleaner (V0.3)

---

This is a simple, standalone utility designed to easily manage and clean the cache and data files for the **FiveM** client on Windows.

If you experience frequent loading errors, texture glitches, or persistent crashes in FiveM, clearing the client cache is often the first and most effective troubleshooting step. This tool automates the entire process, including automatically locating the cache folder regardless of your installation path.

## 🔑 Key Features

* **Automatic Path Detection:** Automatically finds the FiveM `FiveM.app/data` folder, even if it's installed in a non-default location (like a custom drive).
* **Cache Size Analysis:** Calculates and displays the size of the cache folders (`cache`, `logs`, `crashes`, etc.) before cleaning.
* **Two Cleaning Modes:**
    * **1. Clear Cache (Recommended):** Safely removes only the essential temporary cache files and logs.
    * **2. Clear Data Folder (Deep Clean):** Removes the cache **and** the user data folders (`nui-storage`, `game-storage`), requiring the user to re-log into FiveM afterward.
* **Pure Mode Launch Option:** Allows users to automatically launch FiveM with the `-pure_1` argument for troubleshooting server issues.

---

## ⚙️ How to Use (For Users)

1.  **Download** the latest compiled executable from the [Releases page](https://github.com/Pepreal/fivemclearcache/blob/main/fivemcachecleaner_v0.3.exe).
2.  **Close** FiveM completely.
3.  **Run** the `fivemcachecleaner_vx.x.exe` file.
4.  Click **"1. Search for FiveM Cache"**.
5.  Select your desired cleaning option (Recommended or Deep Clean).
6.  The tool will ask if you want to **launch FiveM** when finished.

---

## 📝 Project Details (For Developers)

* **Version:** V0.3
* **Built with:** Python 3 (Tkinter for GUI)
* **Dependencies:** `os`, `shutil`, `sys`, `subprocess`, `tkinter`, `winreg` (Windows only)
* **Build Tool:** PyInstaller
