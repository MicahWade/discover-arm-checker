#!/usr/bin/env python3
"""
Linux ARM Compatibility Checker
-------------------------------
Scans installed GUI applications (Flatpaks and native packages)
and analyzes whether they support ARM64 (aarch64) architecture natively.
"""

import sys
import os
import subprocess
import shutil
import re
import platform

# Color support for terminals
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        cls.GREEN = cls.RED = cls.YELLOW = cls.BLUE = cls.CYAN = cls.BOLD = cls.UNDERLINE = cls.END = ''

# Check if stdout is a TTY to handle coloring gracefully
if not sys.stdout.isatty():
    Colors.disable()

def get_package_manager():
    """Detects the host package manager."""
    if shutil.which("dnf"):
        return "dnf"
    elif shutil.which("apt-get"):
        return "apt"
    elif shutil.which("pacman"):
        return "pacman"
    return "unknown"

def get_installed_flatpaks():
    """Fetches all installed Flatpak applications and their details."""
    if not shutil.which("flatpak"):
        return []
    
    try:
        res = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application,name"],
            capture_output=True, text=True, check=True
        )
        apps = []
        for line in res.stdout.strip().split("\n"):
            if "Application ID" in line or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                apps.append((parts[0].strip(), parts[1].strip()))
        return apps
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Failed to fetch installed Flatpaks: {e}{Colors.END}")
        return []

def get_flatpak_architectures(app_ids):
    """Fetches supported architectures for a list of Flatpak App IDs from Flathub."""
    if not shutil.which("flatpak") or not app_ids:
        return {}
    
    print("🔄 Querying Flathub for Flatpak architectures...")
    all_remote_flatpaks = {}
    try:
        res = subprocess.run(
            ["flatpak", "remote-ls", "flathub", "--arch=*", "--columns=application,arch"],
            capture_output=True, text=True, check=True
        )
        for line in res.stdout.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                appid, arch = parts[0].strip(), parts[1].strip()
                if appid not in all_remote_flatpaks:
                    all_remote_flatpaks[appid] = []
                all_remote_flatpaks[appid].append(arch)
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Failed to query Flathub registry: {e}{Colors.END}")
        # Fallback empty dict
    return all_remote_flatpaks

def get_rpm_owner(desktop_file):
    """Finds the RPM package owning a given desktop file."""
    try:
        res = subprocess.run(["rpm", "-qf", desktop_file], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout:
            pkg_full = res.stdout.strip().split("\n")[0]
            # Strip version-release info to get just the package name
            match = re.match(r"^(.+)-[^-]+-[^-]+$", pkg_full)
            return match.group(1) if match else pkg_full
    except Exception:
        pass
    return None

def get_apt_owner(desktop_file):
    """Finds the APT package owning a given desktop file."""
    try:
        res = subprocess.run(["dpkg", "-S", desktop_file], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout:
            # Output format: package_name: /path/to/file
            parts = res.stdout.strip().split(":")
            if parts:
                return parts[0].strip()
    except Exception:
        pass
    return None

def get_pacman_owner(desktop_file):
    """Finds the Pacman package owning a given desktop file."""
    try:
        res = subprocess.run(["pacman", "-Qo", desktop_file], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout:
            # Output format: /path/to/file is owned by package_name version
            parts = res.stdout.strip().split("is owned by")
            if len(parts) >= 2:
                return parts[1].strip().split()[0]
    except Exception:
        pass
    return None

def check_rpm_compatibility(pkg_name):
    """Determines if an RPM package has native ARM64 support."""
    try:
        res = subprocess.run(["rpm", "-q", "--queryformat", "%{arch}", pkg_name], capture_output=True, text=True)
        if res.stdout.strip() == "noarch":
            return True, True
    except Exception:
        pass
    
    if pkg_name in ["steam", "proton", "google-chrome-stable", "skypeforlinux"]:
        return False, False

    if pkg_name in ["codium", "tabby-terminal"]:
        return True, False

    return True, False

def check_apt_compatibility(pkg_name):
    """Determines if an APT package has native ARM64 support."""
    try:
        res = subprocess.run(["dpkg-query", "-W", "-f=${Architecture}", pkg_name], capture_output=True, text=True)
        if res.stdout.strip() == "all":
            return True, True
    except Exception:
        pass

    if pkg_name in ["steam", "google-chrome-stable", "skypeforlinux"]:
        return False, False
        
    return True, False

def check_pacman_compatibility(pkg_name):
    """Determines if a Pacman package has native ARM64 support (via ALARM)."""
    try:
        res = subprocess.run(["pacman", "-Qi", pkg_name], capture_output=True, text=True)
        for line in res.stdout.split("\n"):
            if line.startswith("Architecture"):
                arch = line.split(":")[1].strip()
                if arch == "any":
                    return True, True
    except Exception:
        pass

    if pkg_name in ["steam", "google-chrome-stable"]:
        return False, False

    return True, False

def scan_native_gui_apps(pkg_mgr):
    """Scans desktop files to identify user-installed GUI packages and their owners."""
    app_dir = "/usr/share/applications"
    if not os.path.exists(app_dir):
        return []

    desktop_files = [os.path.join(app_dir, f) for f in os.listdir(app_dir) if f.endswith(".desktop")]
    
    ignored_patterns = re.compile(
        r"(org\.kde\.(?!kmail|korganizer|konsole|okular|dolphin|kcalc|gwenview|discover|partitionmanager|skanpage|spectacle|neochat|kmines|kpat|kwrite|kolourpaint|kamoso|dragon)|"
        r"org\.gnome\.(?!baobab|totem|gedit|evince|calculator|terminal)|"
        r"org\.freedesktop\.|"
        r"mimeinfo|im-chooser|ibus|nm-connection-editor|avahi|ca\.desrt|system-config|qjackctl|obex|pw-)"
    )

    filtered_files = [f for f in desktop_files if not ignored_patterns.search(os.path.basename(f))]
    
    gui_apps = []
    seen_packages = set()

    for f in filtered_files:
        pkg = None
        if pkg_mgr == "dnf":
            pkg = get_rpm_owner(f)
        elif pkg_mgr == "apt":
            pkg = get_apt_owner(f)
        elif pkg_mgr == "pacman":
            pkg = get_pacman_owner(f)
        
        if pkg and pkg not in seen_packages:
            seen_packages.add(pkg)
            
            app_name = os.path.basename(f).replace(".desktop", "")
            try:
                with open(f, "r", errors="ignore") as file:
                    for line in file:
                        if line.startswith("Name="):
                            app_name = line.split("=")[1].strip()
                            break
            except Exception:
                pass
                
            supports_arm, is_noarch = False, False
            if pkg_mgr == "dnf":
                supports_arm, is_noarch = check_rpm_compatibility(pkg)
            elif pkg_mgr == "apt":
                supports_arm, is_noarch = check_apt_compatibility(pkg)
            elif pkg_mgr == "pacman":
                supports_arm, is_noarch = check_pacman_compatibility(pkg)

            gui_apps.append({
                "name": app_name,
                "package": pkg,
                "type": f"Native ({pkg_mgr.upper()})",
                "supports_arm": supports_arm,
                "is_noarch": is_noarch,
                "details": "noarch (Arch Independent)" if is_noarch else "Natively Compiled"
            })
            
    return gui_apps

def main():
    print(f"{Colors.BOLD}{Colors.BLUE}==================================================={Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}        🚀 LINUX ARM COMPATIBILITY CHECKER        {Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}==================================================={Colors.END}")
    
    pkg_mgr = get_package_manager()
    print(f"🖥️  OS: {Colors.CYAN}{platform.system()} {platform.release()}{Colors.END} ({pkg_mgr.upper()} package manager detected)")

    flatpaks = get_installed_flatpaks()
    print(f"📦 Found {Colors.CYAN}{len(flatpaks)}{Colors.END} Flatpak application(s).")
    
    flatpak_details = get_flatpak_architectures([appid for appid, _ in flatpaks])
    
    analyzed_apps = []
    
    for appid, name in flatpaks:
        archs = flatpak_details.get(appid, [])
        supports_arm = "aarch64" in archs
        analyzed_apps.append({
            "name": name,
            "package": appid,
            "type": "Flatpak",
            "supports_arm": supports_arm,
            "is_noarch": False,
            "details": f"Available: {', '.join(archs)}" if archs else "Status Unknown"
        })

    if pkg_mgr != "unknown":
        print(f"🛠️  Scanning native system GUI applications...")
        native_apps = scan_native_gui_apps(pkg_mgr)
        print(f"Found {Colors.CYAN}{len(native_apps)}{Colors.END} native application(s).")
        analyzed_apps.extend(native_apps)
    else:
        print(f"⚠️  No supported native package manager found. Skipping native package scan.")

    total = len(analyzed_apps)
    arm_supported = sum(1 for a in analyzed_apps if a["supports_arm"])
    incompatible_apps = [a for a in analyzed_apps if not a["supports_arm"]]
    
    print(f"\n{Colors.BOLD}📋 COMPATIBILITY BREAKDOWN:{Colors.END}")
    print(f"---------------------------------------------------")
    
    for app in sorted(analyzed_apps, key=lambda x: x["name"]):
        status_color = Colors.GREEN if app["supports_arm"] else Colors.RED
        status_icon = "✅" if app["supports_arm"] else "❌"
        status_text = "Native ARM64" if app["supports_arm"] else "x86_64 Only"
        
        print(f"{status_icon} {Colors.BOLD}{app['name']}{Colors.END} ({app['type']})")
        print(f"   Package ID:  {app['package']}")
        print(f"   ARM Status:  {status_color}{status_text} ({app['details']}){Colors.END}")
        print(f"   ------------------------------------------------")

    print(f"\n{Colors.BOLD}📊 METRICS SUMMARY:{Colors.END}")
    print(f"===================================================")
    print(f"Total Applications Checked:   {Colors.BOLD}{total}{Colors.END}")
    print(f"Natively Compatible on ARM:   {Colors.GREEN}{Colors.BOLD}{arm_supported}{Colors.END}")
    print(f"Require Emulation (x86_64):  {Colors.RED}{Colors.BOLD}{total - arm_supported}{Colors.END}")
    
    if total > 0:
        pct = (arm_supported / total) * 100
        color = Colors.GREEN if pct > 85 else (Colors.YELLOW if pct > 60 else Colors.RED)
        print(f"Compatibility Score:          {color}{Colors.BOLD}{pct:.2f}%{Colors.END}")
    
    if incompatible_apps:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠️  Incompatible Applications Checklist:{Colors.END}")
        for app in incompatible_apps:
            print(f" * [ ] {Colors.BOLD}{app['name']}{Colors.END} ({app['type']}) -> Package: {app['package']}")
            if "Steam" in app['name'] or "Heroic" in app['name']:
                print(f"       {Colors.BLUE}Tip: Can be run via Box64 + Wine emulation layers on ARM Linux.{Colors.END}")
            elif "Signal" in app['name']:
                print(f"       {Colors.BLUE}Tip: Consider running the web app or custom arm64 builds.{Colors.END}")
            elif "Spotify" in app['name']:
                print(f"       {Colors.BLUE}Tip: Spotify Web Player or unofficial clients can be used.{Colors.END}")
                
    print(f"\n{Colors.BOLD}{Colors.BLUE}==================================================={Colors.END}")

if __name__ == "__main__":
    main()
