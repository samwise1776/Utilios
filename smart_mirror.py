#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import datetime
import os
import shutil
import socket
import subprocess
import sys
import threading
import time


APP = "UTILION SMART MIRROR"
VERSION = "1.0.0"

HOME = Path.home()
UTILION = HOME / "Randomstuff" / "ai.py"


# ============================================================
# 5000 REAL UTILITIES
# ============================================================

ROOTS = [
    ("Home", HOME),
    ("Downloads", HOME / "Downloads"),
    ("Documents", HOME / "Documents"),
    ("Desktop", HOME / "Desktop"),
    ("Pictures", HOME / "Pictures"),
    ("Videos", HOME / "Videos"),
    ("Music", HOME / "Music"),
    ("Config", HOME / ".config"),
    ("LocalShare", HOME / ".local" / "share"),
    ("Tmp", Path("/tmp")),
]


EXTENSIONS = [
    "py", "js", "java", "c", "h",
    "cpp", "hpp", "rs", "go", "rb",
    "php", "pl", "lua", "sh", "bash",
    "zsh", "fish", "html", "htm", "css",
    "scss", "json", "yaml", "yml", "xml",
    "toml", "ini", "conf", "cfg", "env",
    "md", "txt", "log", "csv", "tsv",
    "sql", "db", "sqlite", "sqlite3", "jar",
    "class", "gradle", "kt", "kts", "swift",
    "dart", "r", "R", "jl", "asm",
    "s", "nasm", "wasm", "wat", "exe",
    "dll", "so", "a", "o", "deb",
    "rpm", "appimage", "flatpak", "snap", "zip",
    "tar", "gz", "xz", "bz2", "7z",
    "rar", "iso", "img", "png", "jpg",
    "jpeg", "gif", "webp", "svg", "ico",
    "bmp", "mp3", "wav", "flac", "ogg",
    "mp4", "mkv", "mov", "webm", "avi",
    "pdf", "docx", "odt", "xlsx", "ods",
    "pptx", "desktop", "service", "socket", "timer",
]

EXTENSIONS = EXTENSIONS[:100]

assert len(EXTENSIONS) == 100


def build_registry():

    utilities = []

    def add(name, category, description, kind, **data):

        utilities.append({
            "id": f"{len(utilities) + 1:04d}",
            "name": name,
            "category": category,
            "description": description,
            "kind": kind,
            **data
        })

    # --------------------------------------------------------
    # 1000: FIND FILES BY EXTENSION
    # --------------------------------------------------------

    for root_name, root_path in ROOTS:

        for ext in EXTENSIONS:

            add(
                f"Find .{ext} files in {root_name}",
                "Files / Find",
                f"Find files ending in .{ext} below {root_path}",
                "find_ext",
                root=str(root_path),
                extension=ext
            )

    # --------------------------------------------------------
    # 1000: COUNT FILES BY EXTENSION
    # --------------------------------------------------------

    for root_name, root_path in ROOTS:

        for ext in EXTENSIONS:

            add(
                f"Count .{ext} files in {root_name}",
                "Files / Count",
                f"Count .{ext} files below {root_path}",
                "count_ext",
                root=str(root_path),
                extension=ext
            )

    # --------------------------------------------------------
    # 1000: LARGE FILE SCANNERS
    # 10 roots × 100 thresholds
    # --------------------------------------------------------

    for root_name, root_path in ROOTS:

        for mb in range(
            10,
            1001,
            10
        ):

            add(
                f"Files over {mb} MB in {root_name}",
                "Storage / Large Files",
                f"Locate files larger than {mb} MB below {root_path}",
                "large_files",
                root=str(root_path),
                megabytes=mb
            )

    # --------------------------------------------------------
    # 1000: OLD FILE SCANNERS
    # 10 roots × 100 age thresholds
    # --------------------------------------------------------

    for root_name, root_path in ROOTS:

        for days in range(
            1,
            101
        ):

            add(
                f"Files older than {days} days in {root_name}",
                "Storage / Old Files",
                f"Find files not modified in at least {days} days below {root_path}",
                "old_files",
                root=str(root_path),
                days=days
            )

    # --------------------------------------------------------
    # 1000: LOCAL TCP PORT CHECKS
    # --------------------------------------------------------

    for port in range(
        1,
        1001
    ):

        add(
            f"Check localhost TCP port {port}",
            "Network / Ports",
            f"Check whether TCP port {port} is accepting connections on localhost",
            "port",
            port=port
        )

    assert len(utilities) == 5000

    return utilities


UTILITIES = build_registry()


# ============================================================
# UTILITY ENGINE
# ============================================================

def walk_files(root):

    root = Path(root)

    if not root.exists():

        return

    try:

        for base, dirs, files in os.walk(
            root,
            followlinks=False
        ):

            # Skip a few giant/noisy directories.
            dirs[:] = [
                d
                for d in dirs
                if d not in {
                    ".git",
                    "node_modules",
                    "__pycache__",
                    ".cache"
                }
            ]

            for name in files:

                yield (
                    Path(base)
                    / name
                )

    except (
        PermissionError,
        OSError
    ):

        return


def run_utility(util):

    kind = util["kind"]

    # --------------------------------------------------------
    # FIND EXTENSION
    # --------------------------------------------------------

    if kind == "find_ext":

        ext = (
            "."
            + util["extension"]
            .lower()
        )

        matches = []

        for path in walk_files(
            util["root"]
        ):

            if (
                path.suffix.lower()
                == ext
            ):

                matches.append(
                    str(path)
                )

                if len(matches) >= 250:

                    break

        if not matches:

            return (
                f"No {ext} files found.\n\n"
                f"Root: {util['root']}"
            )

        text = "\n".join(
            matches
        )

        if len(matches) == 250:

            text += (
                "\n\n…results capped at 250."
            )

        return (
            f"Found {len(matches)}+ matching files\n\n"
            + text
        )

    # --------------------------------------------------------
    # COUNT EXTENSION
    # --------------------------------------------------------

    if kind == "count_ext":

        ext = (
            "."
            + util["extension"]
            .lower()
        )

        count = 0

        for path in walk_files(
            util["root"]
        ):

            if (
                path.suffix.lower()
                == ext
            ):

                count += 1

        return (
            f"Extension: {ext}\n"
            f"Root: {util['root']}\n"
            f"Count: {count:,}"
        )

    # --------------------------------------------------------
    # LARGE FILES
    # --------------------------------------------------------

    if kind == "large_files":

        threshold = (
            util["megabytes"]
            * 1024
            * 1024
        )

        matches = []

        for path in walk_files(
            util["root"]
        ):

            try:

                size = path.stat().st_size

            except (
                PermissionError,
                OSError
            ):

                continue

            if size >= threshold:

                matches.append(
                    (
                        size,
                        path
                    )
                )

        matches.sort(
            reverse=True,
            key=lambda item:
            item[0]
        )

        matches = matches[:150]

        if not matches:

            return (
                f"No files >= "
                f"{util['megabytes']} MB found."
            )

        lines = []

        for size, path in matches:

            lines.append(
                f"{size / 1024 / 1024:9.1f} MB   {path}"
            )

        return (
            f"Files >= {util['megabytes']} MB\n\n"
            + "\n".join(lines)
        )

    # --------------------------------------------------------
    # OLD FILES
    # --------------------------------------------------------

    if kind == "old_files":

        cutoff = (
            time.time()
            - util["days"]
            * 86400
        )

        matches = []

        for path in walk_files(
            util["root"]
        ):

            try:

                modified = (
                    path.stat()
                    .st_mtime
                )

            except (
                PermissionError,
                OSError
            ):

                continue

            if modified <= cutoff:

                matches.append(
                    (
                        modified,
                        path
                    )
                )

        matches.sort(
            key=lambda item:
            item[0]
        )

        matches = matches[:150]

        if not matches:

            return (
                f"No files older than "
                f"{util['days']} days found."
            )

        lines = []

        for modified, path in matches:

            date = (
                datetime.datetime
                .fromtimestamp(
                    modified
                )
                .strftime(
                    "%Y-%m-%d"
                )
            )

            lines.append(
                f"{date}   {path}"
            )

        return (
            f"Files older than "
            f"{util['days']} days\n\n"
            + "\n".join(lines)
        )

    # --------------------------------------------------------
    # PORT CHECK
    # --------------------------------------------------------

    if kind == "port":

        port = int(
            util["port"]
        )

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(
            0.30
        )

        try:

            result = sock.connect_ex(
                (
                    "127.0.0.1",
                    port
                )
            )

        finally:

            sock.close()

        if result == 0:

            status = "OPEN ✅"

        else:

            status = "closed"

        return (
            f"Host: 127.0.0.1\n"
            f"TCP port: {port}\n"
            f"Status: {status}"
        )

    return "Unknown utility."


# ============================================================
# SYSTEM INFO
# ============================================================

def ram_info():

    try:

        values = {}

        with open(
            "/proc/meminfo"
        ) as file:

            for line in file:

                key, value = (
                    line.split(
                        ":",
                        1
                    )
                )

                values[
                    key
                ] = int(
                    value
                    .strip()
                    .split()[0]
                )

        total = (
            values["MemTotal"]
            / 1024
        )

        available = (
            values["MemAvailable"]
            / 1024
        )

        used = (
            total
            - available
        )

        percent = (
            used
            / total
            * 100
        )

        return (
            f"{used:.0f} MB\n"
            f"{percent:.0f}% used"
        )

    except Exception:

        return "Unavailable"


def disk_info():

    try:

        usage = shutil.disk_usage(
            HOME
        )

        used = (
            usage.used
            / 1024 ** 3
        )

        total = (
            usage.total
            / 1024 ** 3
        )

        percent = (
            usage.used
            / usage.total
            * 100
        )

        return (
            f"{used:.1f}/{total:.1f} GB\n"
            f"{percent:.0f}% used"
        )

    except Exception:

        return "Unavailable"


def uptime_info():

    try:

        seconds = float(
            Path(
                "/proc/uptime"
            )
            .read_text()
            .split()[0]
        )

        days = int(
            seconds // 86400
        )

        hours = int(
            seconds % 86400
            // 3600
        )

        minutes = int(
            seconds % 3600
            // 60
        )

        if days:

            return (
                f"{days}d "
                f"{hours}h "
                f"{minutes}m"
            )

        return (
            f"{hours}h "
            f"{minutes}m"
        )

    except Exception:

        return "Unavailable"


def load_info():

    try:

        one, five, fifteen = (
            os.getloadavg()
        )

        return (
            f"{one:.2f}\n"
            f"5m {five:.2f}"
        )

    except Exception:

        return "Unavailable"


# ============================================================
# GUI
# ============================================================

class SmartMirror(
    tk.Tk
):

    BG = "#05070b"
    PANEL = "#0d1118"
    PANEL2 = "#121823"
    TEXT = "#f1f5f9"
    MUTED = "#8b98aa"
    ACCENT = "#62d9ff"
    GREEN = "#72f1b8"

    def __init__(self):

        super().__init__()

        self.title(
            APP
        )

        self.geometry(
            "1450x880"
        )

        self.minsize(
            1050,
            650
        )

        self.configure(
            bg=self.BG
        )

        self.fullscreen = False
        self.filtered = UTILITIES[:]

        self.bind(
            "<F11>",
            self.toggle_fullscreen
        )

        self.bind(
            "<Escape>",
            self.leave_fullscreen
        )

        self.build_ui()

        self.show_home()

        self.tick()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        self.grid_columnconfigure(
            1,
            weight=1
        )

        self.grid_rowconfigure(
            0,
            weight=1
        )

        # ----------------------------------------------------
        # UTILION SIDEBAR
        # ----------------------------------------------------

        sidebar = tk.Frame(
            self,
            bg="#080d14",
            width=235
        )

        sidebar.grid(
            row=0,
            column=0,
            sticky="nsw"
        )

        sidebar.grid_propagate(
            False
        )

        tk.Label(
            sidebar,
            text="UTILION",
            fg=self.ACCENT,
            bg="#080d14",
            font=(
                "Sans",
                28,
                "bold"
            )
        ).pack(
            pady=(
                28,
                0
            )
        )

        tk.Label(
            sidebar,
            text="SMART MIRROR",
            fg=self.MUTED,
            bg="#080d14",
            font=(
                "Sans",
                10,
                "bold"
            )
        ).pack(
            pady=(
                0,
                25
            )
        )

        self.side_clock = tk.Label(
            sidebar,
            text="",
            fg=self.TEXT,
            bg="#080d14",
            font=(
                "Monospace",
                19,
                "bold"
            )
        )

        self.side_clock.pack(
            pady=(
                0,
                25
            )
        )

        self.nav_button(
            sidebar,
            "⌂  Mirror",
            self.show_home
        )

        self.nav_button(
            sidebar,
            "⚙  5,000 Utilities",
            self.show_utils
        )

        self.nav_button(
            sidebar,
            "▣  System",
            self.show_system
        )

        self.nav_button(
            sidebar,
            "◈  Launch UTILION",
            self.launch_utilion
        )

        self.nav_button(
            sidebar,
            "⌫  Clear Output",
            self.clear_output
        )

        tk.Label(
            sidebar,
            text=(
                "COMMAND\n"
                "/utils\n"
                "/find QUERY\n"
                "/run ID\n"
                "/system"
            ),
            justify="left",
            fg=self.MUTED,
            bg="#080d14",
            font=(
                "Monospace",
                10
            )
        ).pack(
            side="bottom",
            anchor="w",
            padx=20,
            pady=25
        )

        # ----------------------------------------------------
        # MAIN
        # ----------------------------------------------------

        self.main = tk.Frame(
            self,
            bg=self.BG
        )

        self.main.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.main.grid_columnconfigure(
            0,
            weight=1
        )

        self.main.grid_rowconfigure(
            1,
            weight=1
        )

        header = tk.Frame(
            self.main,
            bg=self.BG
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=30,
            pady=(
                20,
                5
            )
        )

        self.big_clock = tk.Label(
            header,
            text="",
            fg=self.TEXT,
            bg=self.BG,
            font=(
                "Sans",
                42,
                "bold"
            )
        )

        self.big_clock.pack(
            side="left"
        )

        self.date_label = tk.Label(
            header,
            text="",
            fg=self.MUTED,
            bg=self.BG,
            font=(
                "Sans",
                16
            )
        )

        self.date_label.pack(
            side="right",
            pady=16
        )

        self.page = tk.Frame(
            self.main,
            bg=self.BG
        )

        self.page.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=30,
            pady=10
        )

        # ----------------------------------------------------
        # COMMAND BAR
        # ----------------------------------------------------

        commandbar = tk.Frame(
            self.main,
            bg=self.PANEL
        )

        commandbar.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=30,
            pady=(
                5,
                20
            )
        )

        tk.Label(
            commandbar,
            text="UTILION >",
            fg=self.ACCENT,
            bg=self.PANEL,
            font=(
                "Monospace",
                12,
                "bold"
            )
        ).pack(
            side="left",
            padx=12
        )

        self.command = tk.Entry(
            commandbar,
            bg=self.PANEL,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=(
                "Monospace",
                12
            )
        )

        self.command.pack(
            side="left",
            fill="x",
            expand=True,
            padx=8,
            pady=12
        )

        self.command.bind(
            "<Return>",
            self.handle_command
        )

    def nav_button(
        self,
        parent,
        text,
        command
    ):

        button = tk.Button(
            parent,
            text=text,
            command=command,
            anchor="w",
            bg="#080d14",
            fg=self.TEXT,
            activebackground=self.PANEL2,
            activeforeground=self.ACCENT,
            relief="flat",
            borderwidth=0,
            font=(
                "Sans",
                11
            ),
            padx=20,
            pady=12
        )

        button.pack(
            fill="x"
        )

    def clear_page(self):

        for child in (
            self.page
            .winfo_children()
        ):

            child.destroy()

    # ========================================================
    # HOME
    # ========================================================

    def show_home(self):

        self.clear_page()

        title = tk.Label(
            self.page,
            text="GOOD SYSTEM.",
            fg=self.TEXT,
            bg=self.BG,
            font=(
                "Sans",
                25,
                "bold"
            )
        )

        title.pack(
            anchor="w",
            pady=(
                15,
                25
            )
        )

        cards = tk.Frame(
            self.page,
            bg=self.BG
        )

        cards.pack(
            fill="x"
        )

        for i in range(4):

            cards.grid_columnconfigure(
                i,
                weight=1
            )

        self.card_ram = self.make_card(
            cards,
            0,
            "RAM",
            ram_info()
        )

        self.card_disk = self.make_card(
            cards,
            1,
            "DISK",
            disk_info()
        )

        self.card_load = self.make_card(
            cards,
            2,
            "LOAD",
            load_info()
        )

        self.card_uptime = self.make_card(
            cards,
            3,
            "UPTIME",
            uptime_info()
        )

        mirror = tk.Frame(
            self.page,
            bg=self.PANEL
        )

        mirror.pack(
            fill="both",
            expand=True,
            pady=25
        )

        tk.Label(
            mirror,
            text="UTILION SMART MIRROR",
            fg=self.ACCENT,
            bg=self.PANEL,
            font=(
                "Sans",
                18,
                "bold"
            )
        ).pack(
            pady=(
                45,
                8
            )
        )

        tk.Label(
            mirror,
            text=(
                "5,000 functional utilities online\n\n"
                "Type /utils to browse everything.\n"
                "Type /find large files to search.\n"
                "Type /run 2001 to execute a utility.\n\n"
                "F11 — fullscreen"
            ),
            justify="center",
            fg=self.MUTED,
            bg=self.PANEL,
            font=(
                "Sans",
                14
            )
        ).pack()

    def make_card(
        self,
        parent,
        column,
        title,
        value
    ):

        card = tk.Frame(
            parent,
            bg=self.PANEL
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=6
        )

        tk.Label(
            card,
            text=title,
            fg=self.MUTED,
            bg=self.PANEL,
            font=(
                "Sans",
                10,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=18,
            pady=(
                15,
                3
            )
        )

        value_label = tk.Label(
            card,
            text=value,
            justify="left",
            fg=self.TEXT,
            bg=self.PANEL,
            font=(
                "Monospace",
                15,
                "bold"
            )
        )

        value_label.pack(
            anchor="w",
            padx=18,
            pady=(
                3,
                18
            )
        )

        return value_label

    # ========================================================
    # UTILITIES
    # ========================================================

    def show_utils(
        self,
        query=""
    ):

        self.clear_page()

        top = tk.Frame(
            self.page,
            bg=self.BG
        )

        top.pack(
            fill="x",
            pady=(
                8,
                12
            )
        )

        tk.Label(
            top,
            text="5,000 UTILITIES",
            fg=self.TEXT,
            bg=self.BG,
            font=(
                "Sans",
                25,
                "bold"
            )
        ).pack(
            side="left"
        )

        self.count_label = tk.Label(
            top,
            text="5000 / 5000",
            fg=self.ACCENT,
            bg=self.BG,
            font=(
                "Monospace",
                11,
                "bold"
            )
        )

        self.count_label.pack(
            side="right"
        )

        self.search_var = tk.StringVar(
            value=query
        )

        search = tk.Entry(
            self.page,
            textvariable=self.search_var,
            bg=self.PANEL,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=(
                "Sans",
                13
            )
        )

        search.pack(
            fill="x",
            ipady=9,
            pady=(
                0,
                12
            )
        )

        search.bind(
            "<KeyRelease>",
            lambda event:
            self.refresh_utility_list()
        )

        body = tk.PanedWindow(
            self.page,
            orient="horizontal",
            bg=self.BG,
            sashwidth=5
        )

        body.pack(
            fill="both",
            expand=True
        )

        left = tk.Frame(
            body,
            bg=self.PANEL
        )

        right = tk.Frame(
            body,
            bg=self.PANEL
        )

        body.add(
            left,
            minsize=500
        )

        body.add(
            right,
            minsize=350
        )

        scroll = tk.Scrollbar(
            left
        )

        scroll.pack(
            side="right",
            fill="y"
        )

        self.util_list = tk.Listbox(
            left,
            bg=self.PANEL,
            fg=self.TEXT,
            selectbackground="#173d50",
            selectforeground=self.ACCENT,
            relief="flat",
            borderwidth=0,
            font=(
                "Monospace",
                10
            ),
            yscrollcommand=scroll.set
        )

        self.util_list.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        scroll.config(
            command=self.util_list.yview
        )

        self.util_list.bind(
            "<<ListboxSelect>>",
            self.select_utility
        )

        self.detail_title = tk.Label(
            right,
            text="Select a utility",
            wraplength=430,
            justify="left",
            anchor="w",
            fg=self.ACCENT,
            bg=self.PANEL,
            font=(
                "Sans",
                17,
                "bold"
            )
        )

        self.detail_title.pack(
            fill="x",
            padx=20,
            pady=(
                25,
                10
            )
        )

        self.detail = tk.Label(
            right,
            text=(
                "Every utility here performs a real "
                "system/file/network operation."
            ),
            wraplength=430,
            justify="left",
            anchor="nw",
            fg=self.MUTED,
            bg=self.PANEL,
            font=(
                "Sans",
                11
            )
        )

        self.detail.pack(
            fill="x",
            padx=20
        )

        self.run_button = tk.Button(
            right,
            text="RUN UTILITY",
            command=self.run_selected,
            bg="#16445a",
            fg="white",
            activebackground="#246680",
            activeforeground="white",
            relief="flat",
            font=(
                "Sans",
                11,
                "bold"
            ),
            padx=15,
            pady=12
        )

        self.run_button.pack(
            fill="x",
            padx=20,
            pady=20
        )

        tk.Label(
            right,
            text="OUTPUT",
            fg=self.MUTED,
            bg=self.PANEL,
            font=(
                "Sans",
                10,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=20
        )

        self.output = tk.Text(
            right,
            bg="#080c12",
            fg=self.GREEN,
            insertbackground=self.TEXT,
            relief="flat",
            wrap="none",
            font=(
                "Monospace",
                10
            )
        )

        self.output.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(
                6,
                20
            )
        )

        self.refresh_utility_list()

        search.focus_set()

    def refresh_utility_list(self):

        if not hasattr(
            self,
            "util_list"
        ):

            return

        query = (
            self.search_var
            .get()
            .strip()
            .lower()
        )

        words = query.split()

        if words:

            self.filtered = [
                util
                for util in UTILITIES
                if all(
                    word in (
                        util["id"]
                        + " "
                        + util["name"]
                        + " "
                        + util["category"]
                        + " "
                        + util["description"]
                    ).lower()
                    for word in words
                )
            ]

        else:

            self.filtered = (
                UTILITIES[:]
            )

        self.util_list.delete(
            0,
            "end"
        )

        for util in self.filtered:

            self.util_list.insert(
                "end",
                (
                    f"{util['id']}   "
                    f"{util['category']:<22} "
                    f"{util['name']}"
                )
            )

        self.count_label.configure(
            text=(
                f"{len(self.filtered)} "
                "/ 5000"
            )
        )

    def selected_util(self):

        selection = (
            self.util_list
            .curselection()
        )

        if not selection:

            return None

        index = selection[0]

        if (
            index
            >= len(
                self.filtered
            )
        ):

            return None

        return self.filtered[
            index
        ]

    def select_utility(
        self,
        event=None
    ):

        util = self.selected_util()

        if not util:

            return

        self.detail_title.configure(
            text=(
                f"#{util['id']}  "
                f"{util['name']}"
            )
        )

        self.detail.configure(
            text=(
                f"{util['category']}\n\n"
                f"{util['description']}\n\n"
                f"Command:\n"
                f"/run {util['id']}"
            )
        )

    def run_selected(self):

        util = self.selected_util()

        if not util:

            self.write_output(
                "Select a utility first."
            )

            return

        self.execute_util(
            util
        )

    def execute_util(
        self,
        util
    ):

        self.write_output(
            f"Running #{util['id']}\n"
            f"{util['name']}\n\n"
            "Working..."
        )

        def worker():

            try:

                result = run_utility(
                    util
                )

            except Exception as error:

                result = (
                    "UTILITY ERROR\n\n"
                    + repr(error)
                )

            self.after(
                0,
                lambda:
                self.write_output(
                    result
                )
            )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def write_output(
        self,
        text
    ):

        if not hasattr(
            self,
            "output"
        ):

            self.show_utils()

        self.output.delete(
            "1.0",
            "end"
        )

        self.output.insert(
            "end",
            text
        )

    # ========================================================
    # SYSTEM PAGE
    # ========================================================

    def show_system(self):

        self.clear_page()

        tk.Label(
            self.page,
            text="SYSTEM",
            fg=self.TEXT,
            bg=self.BG,
            font=(
                "Sans",
                25,
                "bold"
            )
        ).pack(
            anchor="w",
            pady=20
        )

        text = (
            f"Host: {socket.gethostname()}\n"
            f"User: {os.getenv('USER', 'unknown')}\n"
            f"Python: {sys.version.split()[0]}\n"
            f"Home: {HOME}\n\n"
            f"RAM\n{ram_info()}\n\n"
            f"DISK\n{disk_info()}\n\n"
            f"LOAD\n{load_info()}\n\n"
            f"UPTIME\n{uptime_info()}\n\n"
            f"Utility registry: {len(UTILITIES):,}"
        )

        tk.Label(
            self.page,
            text=text,
            justify="left",
            anchor="nw",
            fg=self.GREEN,
            bg=self.PANEL,
            font=(
                "Monospace",
                14
            ),
            padx=25,
            pady=25
        ).pack(
            fill="both",
            expand=True
        )

    # ========================================================
    # COMMANDS
    # ========================================================

    def handle_command(
        self,
        event=None
    ):

        command = (
            self.command
            .get()
            .strip()
        )

        self.command.delete(
            0,
            "end"
        )

        if not command:

            return

        lower = command.lower()

        if lower in {
            "/utils",
            "utils"
        }:

            self.show_utils()

            return

        if lower in {
            "/home",
            "home"
        }:

            self.show_home()

            return

        if lower in {
            "/system",
            "system"
        }:

            self.show_system()

            return

        if lower.startswith(
            "/find "
        ):

            query = command[
                6:
            ].strip()

            self.show_utils(
                query
            )

            return

        if lower.startswith(
            "/run "
        ):

            requested = command[
                5:
            ].strip()

            util = next(
                (
                    x
                    for x in UTILITIES
                    if (
                        x["id"]
                        == requested
                        .zfill(4)
                    )
                ),
                None
            )

            if not util:

                self.show_utils()

                self.write_output(
                    f"No utility ID: "
                    f"{requested}"
                )

                return

            self.show_utils()

            self.after(
                30,
                lambda:
                self.execute_util(
                    util
                )
            )

            return

        if lower in {
            "/help",
            "help"
        }:

            self.show_utils()

            self.write_output(
                "UTILION MIRROR COMMANDS\n\n"
                "/utils\n"
                "/find QUERY\n"
                "/run ID\n"
                "/home\n"
                "/system\n"
                "/help\n\n"
                "Example:\n"
                "/find large files home\n"
                "/run 2001"
            )

            return

        self.show_utils(
            command
        )

    # ========================================================
    # UTILION
    # ========================================================

    def launch_utilion(self):

        if not UTILION.exists():

            self.show_utils()

            self.write_output(
                f"UTILION not found:\n"
                f"{UTILION}"
            )

            return

        try:

            subprocess.Popen(
                [
                    sys.executable,
                    str(UTILION)
                ],
                cwd=str(
                    UTILION.parent
                )
            )

        except Exception as error:

            self.show_utils()

            self.write_output(
                f"Could not launch UTILION:\n"
                f"{error}"
            )

    # ========================================================
    # CLOCK + LIVE SYSTEM
    # ========================================================

    def tick(self):

        now = (
            datetime.datetime.now()
        )

        clock = now.strftime(
            "%H:%M:%S"
        )

        date = now.strftime(
            "%A, %B %d, %Y"
        )

        self.side_clock.configure(
            text=clock
        )

        self.big_clock.configure(
            text=clock
        )

        self.date_label.configure(
            text=date
        )

        if hasattr(
            self,
            "card_ram"
        ):

            try:

                self.card_ram.configure(
                    text=ram_info()
                )

                self.card_disk.configure(
                    text=disk_info()
                )

                self.card_load.configure(
                    text=load_info()
                )

                self.card_uptime.configure(
                    text=uptime_info()
                )

            except tk.TclError:

                pass

        self.after(
            1000,
            self.tick
        )

    # ========================================================
    # MISC
    # ========================================================

    def clear_output(self):

        if hasattr(
            self,
            "output"
        ):

            self.output.delete(
                "1.0",
                "end"
            )

    def toggle_fullscreen(
        self,
        event=None
    ):

        self.fullscreen = (
            not self.fullscreen
        )

        self.attributes(
            "-fullscreen",
            self.fullscreen
        )

    def leave_fullscreen(
        self,
        event=None
    ):

        self.fullscreen = False

        self.attributes(
            "-fullscreen",
            False
        )


if __name__ == "__main__":

    app = SmartMirror()

    app.mainloop()
