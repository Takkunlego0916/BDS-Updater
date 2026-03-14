import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import requests
import zipfile
import shutil
import os
import re
import tempfile
import time

DOWNLOAD_PAGE = "https://www.minecraft.net/en-us/download/server/bedrock"

DEFAULT_EXCLUDES = [
    "behavior_packs",
    "resource_packs",
    "worlds",
    "config",
    "allowlist.json",
    "permissions.json",
    "server.properties"
]


class BDSUpdater:

    def __init__(self, root):

        self.root = root
        root.title("BDS Updater")
        root.geometry("700x600")

        self.server_process = None
        self.server_path = tk.StringVar()

        tk.Label(root, text="BDS Server Folder").pack()

        path_frame = tk.Frame(root)
        path_frame.pack()

        tk.Entry(path_frame, textvariable=self.server_path, width=65).pack(side=tk.LEFT)

        tk.Button(path_frame, text="Browse", command=self.select_folder).pack(side=tk.LEFT)

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Start Server", command=self.start_server).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Stop Server", command=self.stop_server).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Check Update", command=self.check_update_async).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Update Server", command=self.update_async).grid(row=0, column=3, padx=5)

        tk.Label(root, text="Download Progress").pack()

        self.progress = ttk.Progressbar(root, length=500)
        self.progress.pack(pady=5)

        self.progress_label = tk.Label(root, text="0%")
        self.progress_label.pack()

        tk.Label(root, text="Do NOT overwrite:").pack(pady=5)

        self.excludes = {}
        self.exclude_frame = tk.Frame(root)
        self.exclude_frame.pack()

        for item in DEFAULT_EXCLUDES:
            var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(self.exclude_frame, text=item, variable=var)
            chk.pack(anchor="w")
            self.excludes[item] = var

        tk.Button(root, text="Add custom exclude", command=self.add_exclude).pack()

        tk.Label(root, text="Server Console").pack()

        self.log = tk.Text(root, height=15)
        self.log.pack(fill="both", padx=10, pady=5)

        cmd_frame = tk.Frame(root)
        cmd_frame.pack()

        self.command_entry = tk.Entry(cmd_frame, width=50)
        self.command_entry.pack(side=tk.LEFT)

        tk.Button(cmd_frame, text="Send", command=self.send_custom_command).pack(side=tk.LEFT)

    def log_write(self, text):

        self.root.after(0, lambda: self.log.insert(tk.END, text + "\n"))
        self.root.after(0, lambda: self.log.see(tk.END))

    def select_folder(self):

        path = filedialog.askdirectory()

        if path:
            self.server_path.set(path)

    def add_exclude(self):

        win = tk.Toplevel(self.root)
        entry = tk.Entry(win)
        entry.pack()

        def add():
            name = entry.get()

            if name:

                var = tk.BooleanVar(value=True)
                chk = tk.Checkbutton(self.exclude_frame, text=name, variable=var)
                chk.pack(anchor="w")

                self.excludes[name] = var
                win.destroy()

        tk.Button(win, text="Add", command=add).pack()

    def start_server(self):

        exe = os.path.join(self.server_path.get(), "bedrock_server.exe")

        if not os.path.exists(exe):
            messagebox.showerror("Error", "bedrock_server.exe not found")
            return

        self.server_process = subprocess.Popen(
            exe,
            cwd=self.server_path.get(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        threading.Thread(target=self.read_console, daemon=True).start()

        self.log_write("Server started")

    def read_console(self):

        for line in self.server_process.stdout:
            self.log_write(line.strip())

    def send_command(self, cmd):

        if self.server_process:
            self.server_process.stdin.write(cmd + "\n")
            self.server_process.stdin.flush()

    def send_custom_command(self):

        cmd = self.command_entry.get()

        if cmd:
            self.send_command(cmd)
            self.command_entry.delete(0, tk.END)

    def stop_server(self):

        if self.server_process:

            self.send_command("stop")
            self.server_process.wait()
            self.server_process = None

            self.log_write("Server stopped")

    def stop_server_for_update(self):

        if not self.server_process:
            return

        self.log_write("Notify players...")

        self.send_command("say Server restarting for update in 10 seconds")

        time.sleep(10)

        self.send_command("stop")

        self.server_process.wait()

        self.log_write("Server stopped")

    def get_download_url(self):

        html = requests.get(DOWNLOAD_PAGE).text

        match = re.search(
            r'https://minecraft\.azureedge\.net/bin-win/bedrock-server-[0-9\.]+\.zip',
            html
        )

        if match:
            return match.group(0)

        return None

    def get_local_version(self):

        vfile = os.path.join(self.server_path.get(), "version.txt")

        if os.path.exists(vfile):
            with open(vfile) as f:
                return f.read().strip()

        return "unknown"

    def get_latest_version(self):

        url = self.get_download_url()

        m = re.search(r'bedrock-server-([0-9\.]+)\.zip', url)

        if m:
            return m.group(1)

        return "unknown"

    def check_update_async(self):

        threading.Thread(target=self.check_update, daemon=True).start()

    def check_update(self):

        local = self.get_local_version()
        latest = self.get_latest_version()

        self.log_write(f"Current: {local}")
        self.log_write(f"Latest: {latest}")

        if local == latest:
            messagebox.showinfo("BDS Updater", "Server is up to date")
        else:
            messagebox.showinfo("BDS Updater", "Update available")

    def download_zip(self, url):

        r = requests.get(url, stream=True)

        total = int(r.headers.get('content-length', 0))

        tmp = tempfile.mktemp(".zip")

        downloaded = 0

        with open(tmp, "wb") as f:

            for chunk in r.iter_content(8192):

                f.write(chunk)

                downloaded += len(chunk)

                percent = int(downloaded / total * 100)

                self.root.after(0, lambda p=percent: self.progress.configure(value=p))
                self.root.after(0, lambda p=percent: self.progress_label.config(text=f"{p}%"))

        return tmp

    def extract(self, zip_path):

        tmpdir = tempfile.mkdtemp()

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(tmpdir)

        return tmpdir

    def merge(self, src, dst):

        excludes = [k for k, v in self.excludes.items() if v.get()]

        for item in os.listdir(src):

            if item in excludes:
                self.log_write(f"Skip: {item}")
                continue

            s = os.path.join(src, item)
            d = os.path.join(dst, item)

            if os.path.isdir(s):

                if os.path.exists(d):
                    shutil.rmtree(d)

                shutil.copytree(s, d)

            else:
                shutil.copy2(s, d)

    def update_async(self):

        threading.Thread(target=self.update_with_restart, daemon=True).start()

    def update_with_restart(self):

        self.progress.configure(value=0)
        self.progress_label.config(text="0%")

        self.stop_server_for_update()

        url = self.get_download_url()

        if not url:
            messagebox.showerror("Error", "Download link not found")
            return

        self.log_write("Downloading update...")

        zip_file = self.download_zip(url)

        self.log_write("Extracting...")

        extracted = self.extract(zip_file)

        self.log_write("Installing...")

        self.merge(extracted, self.server_path.get())

        self.log_write("Update complete")

        self.start_server()


root = tk.Tk()

app = BDSUpdater(root)

root.mainloop()
