
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import pandas as pd
import json

class FootballXGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚽ Football xG Analysis Tool")
        self.geometry("600x400")
        self.configure(bg="white")

        self.save_path = None
        self.match_id = None

        self.matches_df = self.load_matches()

        self.create_widgets()

    def create_widgets(self):
        title_label = ttk.Label(self, text="Football xG Analysis Tool", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=20)

        ttk.Button(self, text="🔎 Select Match", command=self.open_match_selector).pack(pady=10)
        ttk.Button(self, text="📂 Choose Output Folder", command=self.select_folder).pack(pady=10)
        ttk.Button(self, text="🚀 Run xG Analysis", command=self.run_analysis).pack(pady=20)

        self.status_label = ttk.Label(self, text="", font=("Arial", 10), foreground="green")
        self.status_label.pack(pady=5)

    def load_matches(self):
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sb_matches.json"))
        with open(path, encoding='utf-8') as f:
            matches = json.load(f)
        df = pd.json_normalize(matches)
        return df

    def open_match_selector(self):
        selector = tk.Toplevel(self)
        selector.title("📋 Select Match")
        selector.geometry("800x550")

        # === Filter UI ===
        filter_frame = ttk.Frame(selector)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        # Drop-down filter by competition
        ttk.Label(filter_frame, text="🏆 Competition:").grid(row=0, column=0, padx=5, sticky='w')
        competitions = sorted(self.matches_df['competition.competition_name'].dropna().unique())
        self.filter_var = tk.StringVar()
        competition_menu = ttk.Combobox(filter_frame, textvariable=self.filter_var, values=competitions,
                                        state='readonly', width=30)
        competition_menu.grid(row=0, column=1, padx=5)
        competition_menu.bind("<<ComboboxSelected>>", self.apply_filters)

        # Search bar for team name or date
        ttk.Label(filter_frame, text="🔤 Search (Team/Date):").grid(row=0, column=2, padx=5, sticky='w')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=0, column=3, padx=5)
        search_entry.bind("<KeyRelease>", self.apply_filters)

        # === Scrollable Match List ===
        list_frame = ttk.Frame(selector)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.match_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Courier", 10),
                                        selectmode=tk.SINGLE)
        self.populate_match_list(self.matches_df)
        self.match_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.match_listbox.yview)

        # === Confirm Button ===
        def confirm_selection():
            selected_index = self.match_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("No selection", "Please select a match.")
                return
            selected_line = self.match_listbox.get(selected_index)
            self.match_id = int(selected_line.split(":")[0])
            self.status_label.config(text=f"✅ Selected match_id: {self.match_id}", foreground="green")
            selector.destroy()

        confirm_btn = ttk.Button(selector, text="✅ Confirm Selection", command=confirm_selection)
        confirm_btn.pack(pady=10)

    def populate_match_list(self, df):
        self.match_listbox.delete(0, tk.END)
        for _, row in df.iterrows():
            match_id = row['match_id']
            home = row['home_team.home_team_name']
            away = row['away_team.away_team_name']
            date = row.get('match_date', '???')
            line = f"{match_id}: {home} vs {away} | {date}"
            self.match_listbox.insert(tk.END, line)

    def apply_filters(self, event=None):
        df = self.matches_df.copy()

        # Filter by competition
        selected_comp = self.filter_var.get()
        if selected_comp:
            df = df[df['competition.competition_name'] == selected_comp]

        # Filter by team name or date
        search_text = self.search_var.get().lower()
        if search_text:
            df = df[df.apply(lambda row: search_text in str(row.get('match_date', '')).lower()
                                         or search_text in str(row.get('home_team.home_team_name', '')).lower()
                                         or search_text in str(row.get('away_team.away_team_name', '')).lower(),
                             axis=1)]

        self.populate_match_list(df)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.save_path = folder
            self.status_label.config(text=f"📁 Folder selected:\n{folder}", foreground="blue")

    def run_analysis(self):
        if not self.match_id:
            messagebox.showwarning("No Match", "Please select a match first.")
            return
        if not self.save_path:
            messagebox.showwarning("Missing Output Path", "Please select an output folder before running analysis.")
            return

        try:
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis", "load_data.py"))
            subprocess.run(["python", script_path, "--save_path", self.save_path, "--match_id", str(self.match_id)], check=True)
            self.status_label.config(text="✅ xG Analysis Completed!", foreground="green")
        except subprocess.CalledProcessError as e:
            self.status_label.config(text="❌ xG Analysis Failed.", foreground="red")
            print("Error:", e)


if __name__ == "__main__":
    app = FootballXGApp()
    app.mainloop()
