# 🚀 Linux ARM Compatibility Checker

This simple script scans your system's installed GUI applications (both Flatpaks and native package manager applications) and checks if they natively support the ARM64 (`aarch64`) architecture.

It's designed to be portable and run on any of the following Linux distributions:
* **Fedora / CentOS / RHEL** (DNF)
* **Debian / Ubuntu / Linux Mint** (APT)
* **Arch Linux / Manjaro** (Pacman)

## 🚀 Quick Run (One-liner)

You can run the script instantly without cloning the repository by running this command in your terminal:
```bash
curl -sSL https://raw.githubusercontent.com/MicahWade/discover-arm-checker/main/check_compatibility.py | python3
```

## 📋 Manual Installation & Run

If you prefer to download the script locally first:

1. **Download the script**:
   ```bash
   curl -sSLO https://raw.githubusercontent.com/MicahWade/discover-arm-checker/main/check_compatibility.py
   ```
2. **Make it executable**:
   ```bash
   chmod +x check_compatibility.py
   ```
3. **Run it**:
   ```bash
   ./check_compatibility.py
   ```

## 🛠️ How it Works

1. **Flatpak Scanning:** It queries Flatpak to list all user applications and connects to Flathub to fetch whether an `aarch64` version is actively built and distributed.
2. **Native Scanning:** It scans desktop entry files in `/usr/share/applications` to identify installed GUI apps, matches them to their owner package via the local package manager (DNF, APT, or Pacman), and determines if they are natively compatible with ARM architectures (identifying architecture-independent `noarch` apps, Python scripts, or known x86 proprietary exceptions).
3. **Dashboard Output:** Prints a detailed, color-coded compatibility report directly in your console.

## ✍️ Authorship

This tool and its code were written by Gemini (Advanced Agentic Coding).
