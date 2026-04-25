"""
launcher.py
Exercise selector UI — run this instead of main.py directly.
Choose an exercise (or Sitting mode), then click START to launch the analyzer.

Requires: Python 3.11, tkinter (bundled with Python), Pillow (optional, for icons)
Usage:  python launcher.py
"""

import tkinter as tk
from tkinter import font as tkfont
import subprocess
import sys
import os

# ── exercise data ────────────────────────────────────────────────────────────
EXERCISES = [
    {
        "name":   "SQUATS",
        "emoji":  "🦵",
        "muscles": "Quads · Glutes · Hamstrings",
        "joints":  "Knee + Hip",
        "tip":    "Keep knees over toes, hips back",
    },
    {
        "name":   "PUSH UPS",
        "emoji":  "💪",
        "muscles": "Chest · Triceps · Shoulders",
        "joints":  "Elbow + Hip (plank)",
        "tip":    "Straight body — don't sag or pike",
    },
    {
        "name":   "PULL UPS",
        "emoji":  "🏋️",
        "muscles": "Lats · Biceps · Rear Deltoids",
        "joints":  "Elbow + Shoulder",
        "tip":    "Full dead hang between every rep",
    },
    {
        "name":   "JUMPING JACKS",
        "emoji":  "⭐",
        "muscles": "Full Body Cardio",
        "joints":  "Shoulder + Elbow",
        "tip":    "Fully extend arms overhead",
    },
    {
        "name":   "RUSSIAN TWISTS",
        "emoji":  "🔄",
        "muscles": "Obliques · Core",
        "joints":  "Hip + Knee",
        "tip":    "Lean back 45°, keep feet raised",
    },
    {
        "name":   "LUNGES",
        "emoji":  "🚶",
        "muscles": "Quads · Glutes · Hip Flexors",
        "joints":  "Knee + Hip",
        "tip":    "Front knee must not pass toes",
    },
    {
        "name":   "PLANK",
        "emoji":  "⏱️",
        "muscles": "Core · Shoulders · Glutes",
        "joints":  "Hip + Elbow + Knee",
        "tip":    "Hold flat — timer starts when form is correct",
    },
    {
        "name":   "BICEP CURLS",
        "emoji":  "💪",
        "muscles": "Biceps Brachii",
        "joints":  "Elbow + Shoulder",
        "tip":    "Keep upper arm still — no swinging",
    },
    {
        "name":   "SHOULDER PRESS",
        "emoji":  "🙌",
        "muscles": "Deltoids · Triceps",
        "joints":  "Elbow + Shoulder",
        "tip":    "Brace core, avoid arching back",
    },
    {
        "name":   "DEADLIFT",
        "emoji":  "⚡",
        "muscles": "Hamstrings · Glutes · Back",
        "joints":  "Hip + Knee",
        "tip":    "Hip hinge — push floor away",
    },
]

SITTING = {
    "name":    "SITTING MODE",
    "emoji":   "🪑",
    "muscles": "Posture Monitoring",
    "joints":  "Neck + Spine",
    "tip":     "Face sideways to the camera",
}

# ── colour palette ────────────────────────────────────────────────────────────
BG          = "#0d0d0f"
PANEL       = "#16161a"
CARD_NORMAL = "#1c1c22"
CARD_HOVER  = "#232330"
CARD_SEL    = "#1a1a2e"
ACCENT      = "#00e5a0"      # neon green — matches the OpenCV HUD
ACCENT2     = "#00b8d9"      # cyan for secondary highlights
WARN        = "#ff6b35"      # orange for sitting mode
TEXT_HI     = "#f0f0f4"
TEXT_MID    = "#9090a0"
TEXT_DIM    = "#4a4a58"
BORDER_SEL  = "#00e5a0"
BORDER_NORM = "#2a2a38"
RADIUS      = 10


class ExerciseLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Posture Analyzer")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.selected_idx   = tk.IntVar(value=0)   # 0-9 = gym, 10 = sitting
        self.card_frames    = []
        self._hover_idx     = None

        self._setup_fonts()
        self._build_ui()
        self._select_card(0)

        # centre on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        ww = self.winfo_width()
        wh = self.winfo_height()
        self.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")

    # ── fonts ─────────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        self.f_title    = tkfont.Font(family="Courier New", size=22, weight="bold")
        self.f_subtitle = tkfont.Font(family="Courier New", size=9)
        self.f_exname   = tkfont.Font(family="Courier New", size=11, weight="bold")
        self.f_meta     = tkfont.Font(family="Courier New", size=8)
        self.f_detail   = tkfont.Font(family="Courier New", size=9)
        self.f_btn      = tkfont.Font(family="Courier New", size=13, weight="bold")
        self.f_tip      = tkfont.Font(family="Courier New", size=9, slant="italic")
        self.f_label    = tkfont.Font(family="Courier New", size=8, weight="bold")

    # ── full layout ───────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 0))

        tk.Label(hdr, text="POSTURE ANALYZER", font=self.f_title,
                 bg=BG, fg=ACCENT).pack(side="left")

        ver = tk.Label(hdr, text="v2.0  ·  MediaPipe + OpenCV",
                       font=self.f_subtitle, bg=BG, fg=TEXT_DIM)
        ver.pack(side="left", padx=(12, 0), pady=(8, 0))

        # ── section: gym exercises ────────────────────────────────────────────
        tk.Label(self, text="── GYM EXERCISES ──────────────────────",
                 font=self.f_label, bg=BG, fg=TEXT_DIM).pack(
                 anchor="w", padx=32, pady=(20, 8))

        grid = tk.Frame(self, bg=BG)
        grid.pack(padx=28, fill="x")

        for i, ex in enumerate(EXERCISES):
            row, col = divmod(i, 2)
            card = self._make_card(grid, i, ex, accent=ACCENT)
            card.grid(row=row, column=col, padx=6, pady=5, sticky="nsew")
            self.card_frames.append(card)

        grid.columnconfigure(0, weight=1, uniform="col")
        grid.columnconfigure(1, weight=1, uniform="col")

        # ── section: sitting mode ─────────────────────────────────────────────
        tk.Label(self, text="── SITTING / DESK MODE ─────────────────",
                 font=self.f_label, bg=BG, fg=TEXT_DIM).pack(
                 anchor="w", padx=32, pady=(18, 8))

        sit_wrap = tk.Frame(self, bg=BG)
        sit_wrap.pack(padx=28, fill="x")
        sit_card = self._make_card(sit_wrap, 10, SITTING, accent=WARN, wide=True)
        sit_card.pack(fill="x", padx=6)
        self.card_frames.append(sit_card)   # index 10

        # ── detail panel ──────────────────────────────────────────────────────
        self.detail_frame = tk.Frame(self, bg=PANEL, bd=0)
        self.detail_frame.pack(padx=34, pady=(18, 0), fill="x")

        self.lbl_emoji   = tk.Label(self.detail_frame, text="", font=tkfont.Font(size=28),
                                    bg=PANEL, fg=TEXT_HI)
        self.lbl_emoji.grid(row=0, column=0, rowspan=3, padx=(16, 12), pady=12)

        self.lbl_exname  = tk.Label(self.detail_frame, text="", font=self.f_exname,
                                    bg=PANEL, fg=ACCENT, anchor="w")
        self.lbl_exname.grid(row=0, column=1, sticky="w", pady=(10, 0))

        self.lbl_muscles = tk.Label(self.detail_frame, text="", font=self.f_detail,
                                    bg=PANEL, fg=TEXT_MID, anchor="w")
        self.lbl_muscles.grid(row=1, column=1, sticky="w")

        self.lbl_joints  = tk.Label(self.detail_frame, text="", font=self.f_meta,
                                    bg=PANEL, fg=TEXT_DIM, anchor="w")
        self.lbl_joints.grid(row=2, column=1, sticky="w", pady=(0, 2))

        sep = tk.Frame(self.detail_frame, bg=TEXT_DIM, height=1)
        sep.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=4)

        self.lbl_tip     = tk.Label(self.detail_frame, text="", font=self.f_tip,
                                    bg=PANEL, fg=ACCENT2, anchor="w")
        self.lbl_tip.grid(row=4, column=0, columnspan=2, sticky="w",
                          padx=16, pady=(0, 12))

        self.detail_frame.columnconfigure(1, weight=1)

        # ── start button ──────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(padx=34, pady=(14, 28), fill="x")

        self.start_btn = tk.Button(
            btn_frame, text="▶  START ANALYZER",
            font=self.f_btn,
            bg=ACCENT, fg=BG, activebackground="#00c484", activeforeground=BG,
            relief="flat", bd=0, padx=24, pady=12,
            cursor="hand2",
            command=self._launch
        )
        self.start_btn.pack(fill="x")

        # keyboard shortcut
        self.bind("<Return>", lambda e: self._launch())
        self.bind("<Escape>", lambda e: self.destroy())

        # arrow navigation
        self.bind("<Up>",    lambda e: self._navigate(-2))
        self.bind("<Down>",  lambda e: self._navigate(2))
        self.bind("<Left>",  lambda e: self._navigate(-1))
        self.bind("<Right>", lambda e: self._navigate(1))

        tk.Label(self, text="↑↓←→ navigate  ·  Enter: start  ·  Esc: quit",
                 font=self.f_meta, bg=BG, fg=TEXT_DIM).pack(pady=(0, 6))

    # ── card factory ──────────────────────────────────────────────────────────
    def _make_card(self, parent, idx, data, accent=ACCENT, wide=False):
        outer = tk.Frame(parent, bg=BORDER_NORM, bd=0)

        inner = tk.Frame(outer, bg=CARD_NORMAL, bd=0)
        inner.pack(padx=1, pady=1, fill="both", expand=True)

        row0 = tk.Frame(inner, bg=CARD_NORMAL)
        row0.pack(fill="x", padx=12, pady=(10, 0))

        tk.Label(row0, text=data["emoji"],
                 font=tkfont.Font(size=18 if wide else 16),
                 bg=CARD_NORMAL, fg=TEXT_HI).pack(side="left")

        tk.Label(row0, text=data["name"],
                 font=self.f_exname, bg=CARD_NORMAL, fg=TEXT_HI).pack(
                 side="left", padx=(8, 0))

        tk.Label(inner, text=data["muscles"],
                 font=self.f_meta, bg=CARD_NORMAL, fg=TEXT_MID).pack(
                 anchor="w", padx=12, pady=(2, 6))

        # bind click + hover to whole card hierarchy
        for widget in (outer, inner, row0):
            widget.bind("<Button-1>", lambda e, i=idx: self._select_card(i))
            widget.bind("<Enter>",    lambda e, i=idx, o=outer, c=inner: self._on_hover(i, o, c))
            widget.bind("<Leave>",    lambda e, i=idx, o=outer, c=inner: self._on_leave(i, o, c))

        for child in inner.winfo_children():
            child.bind("<Button-1>", lambda e, i=idx: self._select_card(i))
            child.bind("<Enter>",    lambda e, i=idx, o=outer, c=inner: self._on_hover(i, o, c))
            child.bind("<Leave>",    lambda e, i=idx, o=outer, c=inner: self._on_leave(i, o, c))

        # store refs for recoloring
        outer._inner     = inner
        outer._ex_idx    = idx
        outer._accent    = accent
        outer._selected  = False

        return outer

    # ── interaction ───────────────────────────────────────────────────────────
    def _on_hover(self, idx, outer, inner):
        if not outer._selected:
            outer.configure(bg=outer._accent)
            inner.configure(bg=CARD_HOVER)
            for w in self._all_children(inner):
                try: w.configure(bg=CARD_HOVER)
                except: pass

    def _on_leave(self, idx, outer, inner):
        if not outer._selected:
            outer.configure(bg=BORDER_NORM)
            inner.configure(bg=CARD_NORMAL)
            for w in self._all_children(inner):
                try: w.configure(bg=CARD_NORMAL)
                except: pass

    def _all_children(self, widget):
        children = list(widget.winfo_children())
        for child in widget.winfo_children():
            children += self._all_children(child)
        return children

    def _select_card(self, idx):
        # deselect previous
        prev = self.selected_idx.get()
        if 0 <= prev < len(self.card_frames):
            old = self.card_frames[prev]
            old._selected = False
            old.configure(bg=BORDER_NORM)
            old._inner.configure(bg=CARD_NORMAL)
            for w in self._all_children(old._inner):
                try: w.configure(bg=CARD_NORMAL)
                except: pass

        # select new
        self.selected_idx.set(idx)
        card = self.card_frames[idx]
        card._selected = True
        card.configure(bg=card._accent)
        card._inner.configure(bg=CARD_SEL)
        for w in self._all_children(card._inner):
            try: w.configure(bg=CARD_SEL)
            except: pass

        # update detail panel
        data = SITTING if idx == 10 else EXERCISES[idx]
        acc  = WARN if idx == 10 else ACCENT
        self.lbl_emoji.configure(text=data["emoji"])
        self.lbl_exname.configure(text=data["name"], fg=acc)
        self.lbl_muscles.configure(text=data["muscles"])
        self.lbl_joints.configure(text=f"Joints tracked: {data['joints']}")
        self.lbl_tip.configure(text=f"Tip: {data['tip']}")

        # update start button colour
        self.start_btn.configure(bg=acc, activebackground=acc)

    def _navigate(self, delta):
        total  = len(self.card_frames)   # 11
        cur    = self.selected_idx.get()
        new    = (cur + delta) % total
        self._select_card(new)

    # ── launch ────────────────────────────────────────────────────────────────
    def _launch(self):
        idx     = self.selected_idx.get()
        sitting = (idx == 10)

        # build command — pass chosen exercise + mode as CLI args to main.py
        script  = os.path.join(os.path.dirname(__file__), "main.py")
        cmd     = [sys.executable, script]

        if sitting:
            cmd += ["--mode", "SITTING"]
        else:
            cmd += ["--mode", "GYM", "--exercise", EXERCISES[idx]["name"]]

        self.destroy()
        subprocess.run(cmd)


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ExerciseLauncher()
    app.mainloop()