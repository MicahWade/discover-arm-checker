# 🚀 Linux ARM Compatibility Checker

This simple script scans your system's installed GUI applications (both Flatpaks and native package manager applications) and checks if they natively support the ARM64 (`aarch64`) architecture.

It's designed to be portable and run on any of the following Linux distributions:
* **Fedora / CentOS / RHEL** (DNF)
* **Debian / Ubuntu / Linux Mint** (APT)
* **Arch Linux / Manjaro** (Pacman)

## 📋 How to Run

1. **Open a terminal** and navigate to this folder.
2. **Make the script executable** (if not already):
   ```bash
   chmod +x check_compatibility.py
   ```
3. **Execute the script**:
   ```bash
   ./check_compatibility.py
   ```

## 🛠️ How it Works

1. **Flatpak Scanning:** It queries Flatpak to list all user applications and connects to Flathub to fetch whether an `aarch64` version is actively built and distributed.
2. **Native Scanning:** It scans desktop entry files in `/usr/share/applications` to identify installed GUI apps, matches them to their owner package via the local package manager (DNF, APT, or Pacman), and determines if they are natively compatible with ARM architectures (identifying architecture-independent `noarch` apps, Python scripts, or known x86 proprietary exceptions).
3. **Dashboard Output:** Prints a detailed, color-coded compatibility report directly in your console.
