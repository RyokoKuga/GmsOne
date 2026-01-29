import customtkinter as ctk
from tkinter import filedialog
import tkinter as tk
import subprocess
import json
import os
import threading
import shutil
import time
import signal
import glob

CONFIG_FILE = "gms_config.json"

# --- 通知ダイアログ ---
class CTkMessage(ctk.CTkToplevel):
    def __init__(self, parent, title, message, color="#2ecc71"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x220")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        ctk.CTkLabel(self, text="●", text_color=color, font=ctk.CTkFont(size=24)).pack(pady=(20, 0))
        ctk.CTkLabel(self, text=title.upper(), font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(5, 10))
        ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=12), wraplength=350).pack(pady=10, padx=20)
        ctk.CTkButton(self, text="OK", width=100, fg_color=color, hover_color=color, command=self.destroy).pack(pady=15)
        
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

# --- 設定ウィンドウクラス ---
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Configuration")
        self.geometry("500x720") 
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.withdraw()
        
        ctk.CTkLabel(self, text="SYSTEM CONFIGURATION", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        self.entries = {}
        paths = [
            ("GAMESS ROOT (GMSPATH)", "gms_path"),
            ("SCRATCH DIR (SCR)", "scr_path"),
            ("USER SCRATCH (USERSCR)", "userscr_path")
        ]
        for label, attr in paths:
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=40, pady=5)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
            
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x")
            e = ctk.CTkEntry(row, font=ctk.CTkFont(size=11))
            e.insert(0, parent.config.get(attr, ""))
            e.pack(side="left", fill="x", expand=True, pady=2)
            self.entries[attr] = e
            ctk.CTkButton(row, text="Browse", width=60, command=lambda ent=e: self.browse(ent)).pack(side="right", padx=(5,0))

        f_sec = ctk.CTkFrame(self, fg_color="#2c3e50", corner_radius=10)
        f_sec.pack(fill="x", padx=40, pady=15)
        ctk.CTkLabel(f_sec, text="macOS SECURITY", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ecf0f1").pack(pady=(10, 0), padx=15, anchor="w")
        
        self.fix_btn = ctk.CTkButton(f_sec, text="FIX 'DEVELOPER CANNOT BE VERIFIED'", fg_color="#e67e22", hover_color="#d35400",
                                     height=32, font=ctk.CTkFont(size=11, weight="bold"), command=self.fix_security)
        self.fix_btn.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(f_sec, text="Click here to remove Apple's 'Quarantine'\nattribute from the GAMESS folder.", 
                     font=ctk.CTkFont(size=10), text_color="#bdc3c7", justify="left").pack(pady=(0, 10), padx=15, anchor="w")

        f2 = ctk.CTkFrame(self, fg_color="transparent")
        f2.pack(fill="x", padx=40, pady=5)
        ctk.CTkLabel(f2, text="ENGINE VERSION", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.ver_entry = ctk.CTkEntry(f2)
        self.ver_entry.insert(0, parent.config.get("version", "30Jun2020R1"))
        self.ver_entry.pack(fill="x", pady=2)

        ctk.CTkLabel(self, text="PARALLEL CORES", font=ctk.CTkFont(size=11, weight="bold")).pack(padx=40, anchor="w", pady=(10,0))
        self.max_cpu = os.cpu_count() or 4
        self.cpu_slider = ctk.CTkSlider(self, from_=1, to=self.max_cpu, number_of_steps=self.max_cpu-1, command=self.update_slider_label)
        self.cpu_slider.set(int(parent.config.get("cores", 1)))
        self.cpu_slider.pack(fill="x", padx=40, pady=5)
        
        self.slider_feedback = ctk.CTkLabel(self, text=f"{int(self.cpu_slider.get())} / {self.max_cpu} (Max)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3498db")
        self.slider_feedback.pack(pady=(0, 5))
        
        self.apply_btn = ctk.CTkButton(self, text="APPLY SETTINGS", fg_color="#2ecc71", hover_color="#27ae60", height=45, font=ctk.CTkFont(weight="bold"), command=self.save_and_exit)
        self.apply_btn.pack(pady=(20, 20))

        self.update_idletasks()
        self.deiconify()

    def update_slider_label(self, value):
        self.slider_feedback.configure(text=f"{int(value)} / {self.max_cpu} (Max)")

    def fix_security(self):
        gms_dir = self.entries["gms_path"].get().strip()
        if not gms_dir or not os.path.exists(gms_dir):
            CTkMessage(self, "Warning", "Valid GAMESS Root path is required.", color="#f39c12")
            return
        try:
            subprocess.run(["xattr", "-dr", "com.apple.quarantine", gms_dir], check=True)
            CTkMessage(self, "Success", f"Security restrictions removed for:\n{gms_dir}")
        except Exception as e:
            CTkMessage(self, "Error", f"Failed to fix security: {e}", color="#e74c3c")

    def browse(self, entry):
        self.attributes("-topmost", False)
        path = filedialog.askdirectory()
        self.attributes("-topmost", True)
        self.focus_force()
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def save_and_exit(self):
        self.parent.config.update({
            "gms_path": self.entries["gms_path"].get().strip(),
            "scr_path": self.entries["scr_path"].get().strip(),
            "userscr_path": self.entries["userscr_path"].get().strip(),
            "version": self.ver_entry.get().strip(),
            "cores": int(self.cpu_slider.get())
        })
        self.parent.save_config()
        self.parent.update_status_bar()
        self.destroy()

# --- メインアプリケーションクラス ---
class GmsLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        
        # --- メニューバーの初期化 (py2appの不必要なメニューを消去) ---
        menubar = tk.Menu(self)
        # 最小限の「編集」メニューのみ追加（コピペ有効化のため）
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Copy", accelerator="Cmd+C", command=lambda: self.focus_get().event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", accelerator="Cmd+V", command=lambda: self.focus_get().event_generate("<<Paste>>"))
        menubar.add_cascade(label="Edit", menu=edit_menu)
        self.config(menu=menubar)

        self.title("GmsOne")
        self.geometry("950x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.config = self.load_config()
        self.queue_files = []
        self.is_running = False
        self.current_process = None
        self.stop_monitor = threading.Event()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        self.grid_rowconfigure(3, weight=2) 

        # --- UI構築 ---
        self.header = ctk.CTkFrame(self, height=80, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        self.logo_group = ctk.CTkFrame(self.header, fg_color="transparent")
        self.logo_group.pack(side="left", anchor="w")
        self.title_label = ctk.CTkLabel(self.logo_group, text="GmsOne", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(anchor="w")
        self.sub_label = ctk.CTkLabel(self.logo_group, text="- GAMESS Job Manager -", font=ctk.CTkFont(size=11, slant="italic"), text_color="gray60")
        self.sub_label.pack(anchor="w", padx=(2, 0))

        self.set_btn = ctk.CTkButton(self.header, text="SETTINGS", width=100, fg_color="transparent", border_width=1, command=self.open_settings)
        self.set_btn.pack(side="right", padx=5, pady=(10, 0))
        self.clear_btn = ctk.CTkButton(self.header, text="CLEAR QUEUE", width=100, fg_color="transparent", border_width=1, command=self.clear_queue)
        self.clear_btn.pack(side="right", padx=5, pady=(10, 0))
        self.add_btn = ctk.CTkButton(self.header, text="+ ADD JOB", width=100, command=self.add_to_queue)
        self.add_btn.pack(side="right", padx=5, pady=(10, 0))

        self.q_label = ctk.CTkLabel(self, text="JOB QUEUE", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        self.q_label.grid(row=1, column=0, sticky="w", padx=30)
        self.queue_box = ctk.CTkTextbox(self, font=("Menlo", 12), border_width=1, corner_radius=10)
        self.queue_box.grid(row=1, column=0, sticky="nsew", padx=25, pady=(25, 10))
        self.queue_box.configure(state="disabled")

        self.l_label = ctk.CTkLabel(self, text="LIVE LOG MONITOR", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        self.l_label.grid(row=2, column=0, sticky="w", padx=30)
        self.log_box = ctk.CTkTextbox(self, font=("Courier New", 12), fg_color="#0a0a0a", text_color="#2ecc71", border_width=1, corner_radius=10)
        self.log_box.grid(row=3, column=0, sticky="nsew", padx=25, pady=(5, 20))
        self.log_box.configure(state="disabled")

        self.control_bar = ctk.CTkFrame(self, height=90, corner_radius=0)
        self.control_bar.grid(row=4, column=0, sticky="ew")
        self.info_group = ctk.CTkFrame(self.control_bar, fg_color="transparent")
        self.info_group.pack(side="left", padx=30)
        self.status_ind = ctk.CTkLabel(self.info_group, text="● READY", text_color="gray", font=ctk.CTkFont(weight="bold"))
        self.status_ind.pack(anchor="w")
        self.core_info = ctk.CTkLabel(self.info_group, text="1 CORE ACTIVE", font=ctk.CTkFont(size=10), text_color="gray")
        self.core_info.pack(anchor="w")
        self.stop_btn = ctk.CTkButton(self.control_bar, text="TERMINATE BATCH", fg_color="#c0392b", hover_color="#a93226", height=45, width=180, state="disabled", command=self.confirm_stop)
        self.stop_btn.pack(side="right", padx=25, pady=20)
        self.run_btn = ctk.CTkButton(self.control_bar, text="START COMPUTATION", fg_color="#27ae60", hover_color="#219150", height=45, width=220, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_queue_thread)
        self.run_btn.pack(side="right", padx=5, pady=20)

        self.update_status_bar()
        self.update_idletasks()
        self.deiconify()

    def open_settings(self):
        SettingsWindow(self)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w") as f: json.dump(self.config, f)

    def update_status_bar(self):
        cores = self.config.get("cores", 1)
        self.core_info.configure(text=f"{cores} CORES ACTIVE")

    def relocate_temp_files(self, gms_dir, userscr_dir, job_name):
        save_exts = [".dat", ".rst", ".trj", ".casino", ".dmn", ".cim", ".cosmo", ".pot", ".gamma", ".efp", ".dip", ".hs1", ".hs2", ".qmw"]
        for ext in save_exts:
            src = os.path.join(gms_dir, job_name + ext)
            dst = os.path.join(userscr_dir, job_name + ext)
            if os.path.exists(src):
                try:
                    if os.path.exists(dst): os.remove(dst)
                    shutil.move(src, dst)
                except: pass
        f_pattern = os.path.join(gms_dir, f"{job_name}.F*")
        for f_file in glob.glob(f_pattern):
            try: os.remove(f_file)
            except: pass

    def run_single_gamess(self, input_path):
        gms_dir = self.config.get("gms_path", "").strip()
        userscr_dir = self.config.get("userscr_path", "").strip()
        job_base = os.path.splitext(os.path.abspath(input_path))[0]
        job_name = os.path.basename(job_base)
        log_file_path = job_base + ".log"
        self.stop_monitor.clear()
        threading.Thread(target=self.monitor_log, args=(log_file_path,), daemon=True).start()
        env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:" + gms_dir, "GMSPATH": gms_dir, "SCR": self.config.get("scr_path", "").strip(), "USERSCR": userscr_dir, "HOME": os.environ.get("HOME", ""), "TERM": "xterm"}
        cmd = ["./rungms", job_base, self.config.get("version", "").strip(), str(int(self.config.get("cores", 1)))]
        try:
            self.after(0, lambda: self.status_ind.configure(text=f"● RUNNING: {job_name}", text_color="#3498db"))
            with open(log_file_path, "w") as log_out:
                self.current_process = subprocess.Popen(cmd, env=env, cwd=gms_dir, stdout=log_out, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
                self.current_process.wait() 
            time.sleep(1.0)
            self.stop_monitor.set()
            is_success = False
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", errors='ignore') as f:
                    if "TERMINATED NORMALLY" in f.read(): is_success = True
            if self.is_running: self.relocate_temp_files(gms_dir, userscr_dir, job_name)
            return is_success
        except: return False

    def process_queue(self):
        failed_jobs = []
        while self.queue_files and self.is_running:
            current_file = self.queue_files[0]
            self.after(0, self.refresh_queue_display)
            success = self.run_single_gamess(current_file)
            if not success and self.is_running: failed_jobs.append(os.path.basename(current_file))
            if self.is_running: self.queue_files.pop(0)
            else: break
        self.is_running = False
        self.after(0, self.refresh_queue_display)
        self.after(0, lambda: [self.run_btn.configure(state="normal"), self.stop_btn.configure(state="disabled"), self.status_ind.configure(text="● IDLE", text_color="gray")])
        if not self.stop_monitor.is_set() or len(self.queue_files) == 0:
            msg = "Batch Complete" if not failed_jobs else f"Errors in {len(failed_jobs)} job(s)."
            self.after(0, lambda: self.show_finish(msg, bool(failed_jobs)))

    def confirm_stop(self):
        win = ctk.CTkToplevel(self)
        win.title("Confirm Abort")
        win.geometry("380x180")
        win.attributes("-topmost", True)
        ctk.CTkLabel(win, text="Abort current batch?\nUnfinished jobs will be removed.", pady=25).pack()
        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack()
        ctk.CTkButton(f, text="Abort", fg_color="#e74c3c", width=100, command=lambda: [win.destroy(), self.execute_stop()]).pack(side="left", padx=10)
        ctk.CTkButton(f, text="Cancel", fg_color="gray", width=100, command=win.destroy).pack(side="left", padx=10)

    def execute_stop(self):
        if not self.is_running: return
        self.is_running = False
        cur_job = os.path.splitext(os.path.basename(self.queue_files[0]))[0] if self.queue_files else None
        if self.current_process:
            try: os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
            except: pass
        self.stop_monitor.set()
        if cur_job: 
            self.after(0, lambda: self.status_ind.configure(text="● CLEANING UP...", text_color="#f39c12"))
            self.relocate_temp_files(self.config.get("gms_path"), self.config.get("userscr_path"), cur_job)
        self.queue_files = []
        self.after(0, self.refresh_queue_display)
        self.after(0, lambda: self.status_ind.configure(text="● ABORTED", text_color="#e74c3c"))

    def monitor_log(self, log_path):
        while not os.path.exists(log_path) and not self.stop_monitor.is_set(): time.sleep(0.5)
        while not self.stop_monitor.is_set():
            try:
                if os.path.exists(log_path):
                    with open(log_path, "r", errors='ignore') as f:
                        f.seek(0, 2)
                        filesize = f.tell()
                        f.seek(max(0, filesize - 3500))
                        last_lines = "".join(f.readlines()[-15:])
                        self.after(0, self.update_log_display, last_lines)
            except: pass
            time.sleep(0.8)

    def update_log_display(self, text):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.insert("end", text)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def add_to_queue(self):
        files = filedialog.askopenfilenames(filetypes=[("GAMESS Input", "*.inp")])
        for f in files:
            if f not in self.queue_files: self.queue_files.append(f)
        self.refresh_queue_display()
        self.focus_force()

    def clear_queue(self):
        if not self.is_running: self.queue_files = []; self.refresh_queue_display()

    def refresh_queue_display(self):
        self.queue_box.configure(state="normal")
        self.queue_box.delete("1.0", "end")
        for i, f in enumerate(self.queue_files):
            prefix = ">> " if i == 0 and self.is_running else "-- "
            self.queue_box.insert("end", f"{prefix}{os.path.basename(f)}\n")
        self.queue_box.configure(state="disabled")

    def start_queue_thread(self):
        if not self.queue_files: return
        self.is_running = True; self.run_btn.configure(state="disabled"); self.stop_btn.configure(state="normal")
        threading.Thread(target=self.process_queue, daemon=True).start()

    def show_finish(self, message, is_error):
        CTkMessage(self, "Status", message, color="#e74c3c" if is_error else "#2ecc71")

if __name__ == "__main__":
    app = GmsLauncher()
    app.mainloop()