"""Danish vocabulary trainer.

Add, search and sort Danish words, then practise them with flashcards.
All words are stored in words.json next to this script.

Run with:  python dansk.py
"""

import json
import os
import random
import sys
import tkinter as tk
import unicodedata
import uuid
from datetime import date
from tkinter import messagebox, ttk

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "words.json")

WORD_TYPES = [
    "noun",
    "verb",
    "adjective",
    "adverb",
    "pronoun",
    "preposition",
    "conjunction",
    "phrase",
    "other",
]
ARTICLES = ["", "en", "et"]
ALL_TYPES = "all"

# Danish alphabet: æ, ø, å come after z.
DANISH_ORDER = "abcdefghijklmnopqrstuvwxyzæøå"

# ---- look & feel ---------------------------------------------------------
BG = "#f4f5f7"
SURFACE = "#ffffff"
BORDER = "#e2e5ea"
STRIPE = "#f8f9fb"
TEXT = "#1f2933"
MUTED = "#6b7280"
RED = "#c8102e"          # Danish flag red
RED_DARK = "#a00d25"
RED_SOFT = "#fde4e8"
BLUE = "#1f4e9c"
BLUE_SOFT = "#eef3fc"
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")


def danish_sort_key(text):
    """Sort key that follows Danish alphabetical order (… x y z æ ø å)."""
    key = []
    for ch in text.casefold():
        if ch not in DANISH_ORDER:
            # Strip accents (é -> e) but keep the base letter.
            ch = unicodedata.normalize("NFD", ch)[0]
        if ch in DANISH_ORDER:
            key.append((1, DANISH_ORDER.index(ch)))
        else:
            key.append((0, ord(ch)))  # spaces/punctuation before letters
    return key


def english_sort_key(text):
    return text.casefold()


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------

def load_words():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f).get("words", [])
    except (json.JSONDecodeError, OSError) as e:
        messagebox.showerror("Error", f"Could not read {DATA_FILE}:\n{e}")
        return []


def save_words(words):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"words": words}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)  # atomic: never leaves a half-written file


def danish_display(word):
    """'bil' + 'en' -> 'en bil'."""
    article = word.get("article", "")
    return f"{article} {word['danish']}" if article else word["danish"]


# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------

def setup_styles(root, scale):
    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.font", FONT)
    root.option_add("*TCombobox*Listbox.selectBackground", RED)
    root.option_add("*TCombobox*Listbox.selectForeground", "white")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=TEXT, font=FONT,
                    bordercolor=BORDER, focuscolor=BG)

    # Panels: white "cards" on the grey background.
    style.configure("Panel.TFrame", background=SURFACE)
    for widget in ("TLabel", "TRadiobutton", "TCheckbutton"):
        style.configure(f"Panel.{widget}", background=SURFACE)
    style.map("Panel.TRadiobutton", background=[("active", SURFACE)],
              indicatorcolor=[("selected", RED), ("!selected", SURFACE)])
    style.map("Panel.TCheckbutton", background=[("active", SURFACE)],
              indicatorcolor=[("selected", RED), ("!selected", SURFACE)])
    style.configure("Section.TLabel", background=SURFACE, font=("Segoe UI", 11, "bold"))
    style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED)
    style.configure("MutedBg.TLabel", background=BG, foreground=MUTED)

    # Inputs
    style.configure("TEntry", fieldbackground=SURFACE, padding=6,
                    lightcolor=BORDER, darkcolor=BORDER)
    style.map("TEntry", lightcolor=[("focus", RED)], bordercolor=[("focus", RED)])
    style.configure("TCombobox", fieldbackground=SURFACE, padding=5, arrowcolor=MUTED,
                    lightcolor=BORDER, darkcolor=BORDER, background=SURFACE)
    style.map("TCombobox",
              fieldbackground=[("disabled", "#eef0f3"), ("readonly", SURFACE)],
              selectbackground=[("readonly", SURFACE)],
              selectforeground=[("readonly", TEXT)],
              bordercolor=[("focus", RED)], lightcolor=[("focus", RED)])

    # Buttons
    style.configure("TButton", background=SURFACE, padding=(12, 6),
                    lightcolor=SURFACE, darkcolor=BORDER)
    style.map("TButton", background=[("active", "#eef0f3")])
    style.configure("Accent.TButton", background=RED, foreground="white",
                    bordercolor=RED, lightcolor=RED, darkcolor=RED_DARK,
                    font=FONT_BOLD, padding=(16, 6))
    style.map("Accent.TButton",
              background=[("disabled", "#e8a3ad"), ("active", RED_DARK)],
              foreground=[("disabled", "white")])
    style.configure("Key.TButton", font=("Segoe UI", 11, "bold"), foreground=RED,
                    padding=(4, 2), anchor="center")
    style.configure("Danger.TButton", foreground=RED)
    style.map("Danger.TButton", foreground=[("disabled", "#d4a1a9")])
    style.configure("Big.TButton", font=("Segoe UI", 11), padding=(22, 10))
    style.configure("BigAccent.TButton", background=RED, foreground="white",
                    bordercolor=RED, lightcolor=RED, darkcolor=RED_DARK,
                    font=("Segoe UI", 11, "bold"), padding=(22, 10))
    style.map("BigAccent.TButton",
              background=[("disabled", "#e8a3ad"), ("active", RED_DARK)])

    # Tabs
    style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(12, 8, 12, 0))
    style.configure("TNotebook.Tab", background=BG, foreground=MUTED, padding=(20, 8),
                    borderwidth=0, font=FONT_BOLD)
    style.map("TNotebook.Tab",
              background=[("selected", SURFACE), ("active", "#eaecef")],
              foreground=[("selected", RED)],
              lightcolor=[("selected", SURFACE)],
              bordercolor=[("selected", BORDER), ("!selected", BG)],
              expand=[("selected", (0, 0, 0, 0))],
              padding=[("selected", (20, 8))])

    # Word list
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE,
                    rowheight=int(30 * scale), borderwidth=0, font=("Segoe UI", 11))
    style.map("Treeview", background=[("selected", RED_SOFT)],
              foreground=[("selected", TEXT)])
    style.configure("Treeview.Heading", background="#eef0f3", foreground=MUTED,
                    font=FONT_BOLD, relief="flat", padding=(8, 6))
    style.map("Treeview.Heading", background=[("active", "#e4e7eb")])
    style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=SURFACE,
                    bordercolor=SURFACE, arrowcolor=MUTED, lightcolor=BORDER,
                    darkcolor=BORDER)

    style.configure("Red.Horizontal.TProgressbar", background=RED, troughcolor=BORDER,
                    bordercolor=BORDER, lightcolor=RED, darkcolor=RED,
                    thickness=int(6 * scale))


def rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def draw_flag(canvas, w, h):
    """Small Dannebrog."""
    canvas.create_rectangle(0, 0, w, h, fill=RED, outline="")
    bar = h / 7 * 1.5
    cross_x = w * 12 / 37
    canvas.create_rectangle(cross_x - bar / 2, 0, cross_x + bar / 2, h, fill="white", outline="")
    canvas.create_rectangle(0, h / 2 - bar / 2, w, h / 2 + bar / 2, fill="white", outline="")


# --------------------------------------------------------------------------
# Words tab
# --------------------------------------------------------------------------

class WordsTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=14)
        self.app = app
        self.selected_id = None
        self.sort_by = tk.StringVar(value="danish")
        self.descending = tk.BooleanVar(value=False)

        self._build_form()
        self._build_list()
        self.refresh()

    # ---- layout ----------------------------------------------------------

    def _build_form(self):
        form = ttk.Frame(self, style="Panel.TFrame", padding=14)
        form.pack(fill="x")

        self.form_title = ttk.Label(form, text="Add a new word", style="Section.TLabel")
        self.form_title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        keys = ttk.Frame(form, style="Panel.TFrame")
        keys.grid(row=0, column=4, sticky="e", pady=(0, 8))
        ttk.Label(keys, text="Insert letter (Shift+click = capital)",
                  style="Muted.TLabel").pack(side="left", padx=(0, 6))
        for letter in "æøå":
            btn = ttk.Button(keys, text=letter, style="Key.TButton", width=3, takefocus=False)
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, l=letter: self.app.insert_letter(l))
            btn.bind("<Shift-Button-1>", lambda e, l=letter: self.app.insert_letter(l.upper()))

        self.danish_var = tk.StringVar()
        self.english_var = tk.StringVar()
        self.example_var = tk.StringVar()
        self.type_var = tk.StringVar(value=WORD_TYPES[0])
        self.article_var = tk.StringVar(value="")

        def label(text, row, col):
            ttk.Label(form, text=text, style="Muted.TLabel").grid(
                row=row, column=col, sticky="w", padx=(0 if col == 0 else 12, 0))

        label("Danish", 1, 0)
        label("English", 1, 1)
        label("Type", 1, 2)
        label("Article", 1, 3)

        self.danish_entry = ttk.Entry(form, textvariable=self.danish_var, font=("Segoe UI", 11))
        self.danish_entry.grid(row=2, column=0, sticky="we", pady=(2, 0))
        english_entry = ttk.Entry(form, textvariable=self.english_var, font=("Segoe UI", 11))
        english_entry.grid(row=2, column=1, sticky="we", padx=(12, 0), pady=(2, 0))

        type_box = ttk.Combobox(form, textvariable=self.type_var, values=WORD_TYPES,
                                state="readonly", width=12)
        type_box.grid(row=2, column=2, sticky="w", padx=(12, 0), pady=(2, 0))
        type_box.bind("<<ComboboxSelected>>", lambda e: self._update_article_state())

        self.article_box = ttk.Combobox(form, textvariable=self.article_var,
                                        values=ARTICLES, state="readonly", width=5)
        self.article_box.grid(row=2, column=3, sticky="w", padx=(12, 0), pady=(2, 0))

        ttk.Label(form, text="Example sentence (optional)", style="Muted.TLabel").grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(10, 0))
        example_entry = ttk.Entry(form, textvariable=self.example_var, font=("Segoe UI", 11))
        example_entry.grid(row=4, column=0, columnspan=4, sticky="we", pady=(2, 0))

        self.danish_entry.bind("<Return>", lambda e: english_entry.focus_set())
        english_entry.bind("<Return>", lambda e: example_entry.focus_set())
        example_entry.bind("<Return>", lambda e: self.save_word())
        for entry in (self.danish_entry, english_entry, example_entry):
            self.app.track_entry(entry)

        buttons = ttk.Frame(form, style="Panel.TFrame")
        buttons.grid(row=4, column=4, sticky="e", padx=(16, 0), pady=(2, 0))
        self.save_btn = ttk.Button(buttons, text="Add word", style="Accent.TButton",
                                   command=self.save_word)
        self.save_btn.pack(side="left")
        self.delete_btn = ttk.Button(buttons, text="Delete", style="Danger.TButton",
                                     command=self.delete_word, state="disabled")
        self.delete_btn.pack(side="left", padx=6)
        ttk.Button(buttons, text="Clear", command=self.clear_form).pack(side="left")

        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        self._update_article_state()

    def _build_list(self):
        panel = ttk.Frame(self, style="Panel.TFrame", padding=14)
        panel.pack(fill="both", expand=True, pady=(12, 0))

        bar = ttk.Frame(panel, style="Panel.TFrame")
        bar.pack(fill="x", pady=(0, 10))

        ttk.Label(bar, text="🔍", style="Muted.TLabel").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh())
        search_entry = ttk.Entry(bar, textvariable=self.search_var, width=24)
        search_entry.pack(side="left", padx=(4, 0))
        self.app.track_entry(search_entry)

        ttk.Label(bar, text="Type", style="Muted.TLabel").pack(side="left", padx=(16, 4))
        self.filter_var = tk.StringVar(value=ALL_TYPES)
        filter_box = ttk.Combobox(bar, textvariable=self.filter_var,
                                  values=[ALL_TYPES] + WORD_TYPES, state="readonly", width=12)
        filter_box.pack(side="left")
        filter_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Label(bar, text="Sort by", style="Muted.TLabel").pack(side="left", padx=(16, 4))
        ttk.Radiobutton(bar, text="Danish", variable=self.sort_by, value="danish",
                        style="Panel.TRadiobutton", command=self.refresh).pack(side="left")
        ttk.Radiobutton(bar, text="English", variable=self.sort_by, value="english",
                        style="Panel.TRadiobutton", command=self.refresh).pack(side="left", padx=(6, 0))
        ttk.Checkbutton(bar, text="Z → A", variable=self.descending,
                        style="Panel.TCheckbutton", command=self.refresh).pack(side="left", padx=(10, 0))

        self.count_label = ttk.Label(bar, text="", style="Muted.TLabel")
        self.count_label.pack(side="right")

        table_frame = tk.Frame(panel, bg=BORDER, padx=1, pady=1)  # 1px border
        table_frame.pack(fill="both", expand=True)
        columns = ("danish", "type", "english", "example")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                 selectmode="browse")
        self.tree.heading("danish", anchor="w", command=lambda: self._sort_on("danish"))
        self.tree.heading("type", text="Type", anchor="center")
        self.tree.heading("english", anchor="w", command=lambda: self._sort_on("english"))
        self.tree.heading("example", text="Example", anchor="w")
        self.tree.column("danish", width=170)
        self.tree.column("type", width=100, anchor="center")
        self.tree.column("english", width=180)
        self.tree.column("example", width=300)
        self.tree.tag_configure("odd", background=STRIPE)
        self.tree.tag_configure("typecol", foreground=MUTED)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ---- behaviour -------------------------------------------------------

    def _update_article_state(self):
        if self.type_var.get() == "noun":
            self.article_box.configure(state="readonly")
        else:
            self.article_var.set("")
            self.article_box.configure(state="disabled")

    def _sort_on(self, column):
        """Clicking a column header sorts by it; clicking again reverses."""
        if self.sort_by.get() == column:
            self.descending.set(not self.descending.get())
        else:
            self.sort_by.set(column)
            self.descending.set(False)
        self.refresh()

    def _update_headings(self):
        arrow = " ▼" if self.descending.get() else " ▲"
        for col, title in (("danish", "Danish"), ("english", "English")):
            self.tree.heading(col, text=title + (arrow if self.sort_by.get() == col else ""))

    def refresh(self):
        query = self.search_var.get().strip().casefold()
        type_filter = self.filter_var.get()

        words = [
            w for w in self.app.words
            if (type_filter == ALL_TYPES or w["type"] == type_filter)
            and (not query or query in w["danish"].casefold()
                 or query in w["english"].casefold()
                 or query in w.get("example", "").casefold())
        ]
        if self.sort_by.get() == "danish":
            words.sort(key=lambda w: danish_sort_key(w["danish"]),
                       reverse=self.descending.get())
        else:
            words.sort(key=lambda w: english_sort_key(w["english"]),
                       reverse=self.descending.get())

        self.tree.delete(*self.tree.get_children())
        for i, w in enumerate(words):
            self.tree.insert("", "end", iid=w["id"],
                             values=(danish_display(w), w["type"], w["english"],
                                     w.get("example", "")),
                             tags=("odd",) if i % 2 else ())
        total = len(self.app.words)
        self.count_label.configure(
            text=f"{len(words)} of {total} words" if len(words) != total else f"{total} words")
        self._update_headings()

        if self.selected_id and self.tree.exists(self.selected_id):
            self.tree.selection_set(self.selected_id)

    def _on_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        word = self.app.find_word(selection[0])
        if word is None:
            return
        self.selected_id = word["id"]
        self.danish_var.set(word["danish"])
        self.english_var.set(word["english"])
        self.example_var.set(word.get("example", ""))
        self.type_var.set(word["type"])
        self._update_article_state()
        self.article_var.set(word.get("article", ""))
        self.form_title.configure(text=f"Editing “{danish_display(word)}”")
        self.save_btn.configure(text="Save changes")
        self.delete_btn.configure(state="normal")

    def clear_form(self):
        self.selected_id = None
        self.danish_var.set("")
        self.english_var.set("")
        self.example_var.set("")
        self.article_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.form_title.configure(text="Add a new word")
        self.save_btn.configure(text="Add word")
        self.delete_btn.configure(state="disabled")
        self.danish_entry.focus_set()

    def save_word(self):
        danish = self.danish_var.get().strip()
        english = self.english_var.get().strip()
        example = self.example_var.get().strip()
        word_type = self.type_var.get()
        article = self.article_var.get() if word_type == "noun" else ""

        if not danish or not english:
            messagebox.showwarning("Missing data", "Please fill in both Danish and English.")
            return

        duplicate = next(
            (w for w in self.app.words
             if w["id"] != self.selected_id
             and w["danish"].casefold() == danish.casefold()
             and w["type"] == word_type),
            None,
        )
        if duplicate and not messagebox.askyesno(
                "Duplicate",
                f"'{danish}' ({word_type}) already exists as '{duplicate['english']}'.\n"
                "Save anyway?"):
            return

        if self.selected_id:
            word = self.app.find_word(self.selected_id)
            word.update(danish=danish, english=english, type=word_type, article=article,
                        example=example)
        else:
            self.app.words.append({
                "id": uuid.uuid4().hex,
                "danish": danish,
                "article": article,
                "type": word_type,
                "english": english,
                "example": example,
                "added": date.today().isoformat(),
            })
        self.app.save()
        self.clear_form()
        self.refresh()

    def delete_word(self):
        word = self.app.find_word(self.selected_id)
        if word is None:
            return
        if not messagebox.askyesno("Delete", f"Delete '{danish_display(word)}'?"):
            return
        self.app.words.remove(word)
        self.app.save()
        self.clear_form()
        self.refresh()


# --------------------------------------------------------------------------
# Practice tab (flashcards)
# --------------------------------------------------------------------------

class PracticeTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=14)
        self.app = app
        self.deck = []
        self.index = 0
        self.flipped = False

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Practise", style="MutedBg.TLabel").pack(side="left")
        self.filter_var = tk.StringVar(value=ALL_TYPES)
        filter_box = ttk.Combobox(top, textvariable=self.filter_var,
                                  values=[ALL_TYPES] + WORD_TYPES, state="readonly", width=12)
        filter_box.pack(side="left", padx=6)
        filter_box.bind("<<ComboboxSelected>>", lambda e: self.start())
        ttk.Button(top, text="⟳  Shuffle", command=self.start,
                   takefocus=False).pack(side="left", padx=4)
        self.progress_label = ttk.Label(top, text="", style="MutedBg.TLabel")
        self.progress_label.pack(side="right")

        self.progress = ttk.Progressbar(self, style="Red.Horizontal.TProgressbar",
                                        mode="determinate")
        self.progress.pack(fill="x", pady=(10, 0))

        self.card = tk.Canvas(self, bg=BG, highlightthickness=0, cursor="hand2")
        self.card.pack(fill="both", expand=True, pady=14)
        self.card.bind("<Button-1>", lambda e: self.flip())
        self.card.bind("<Configure>", lambda e: self.show())

        buttons = ttk.Frame(self)
        buttons.pack()
        # takefocus=False so Space/→ shortcuts don't also "press" a focused button.
        self.flip_btn = ttk.Button(buttons, text="↺  Flip card", style="Big.TButton",
                                   command=self.flip, takefocus=False)
        self.flip_btn.pack(side="left", padx=8)
        self.next_btn = ttk.Button(buttons, text="Next word  →", style="BigAccent.TButton",
                                   command=self.next_word, takefocus=False)
        self.next_btn.pack(side="left", padx=8)
        ttk.Label(self, text="Space to flip  ·  → for next  ·  click the card to flip",
                  style="MutedBg.TLabel").pack(pady=(8, 0))

    def start(self):
        type_filter = self.filter_var.get()
        self.deck = [w for w in self.app.words
                     if type_filter == ALL_TYPES or w["type"] == type_filter]
        random.shuffle(self.deck)
        self.index = 0
        self.flipped = False
        self.card.focus_set()
        self.show()

    def _draw_card(self, label, label_color, main, main_color, sub, fill, edge, example=""):
        c = self.card
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return
        pad = 30
        x1, y1, x2, y2 = pad, 6, w - pad, h - 10
        rounded_rect(c, x1 + 3, y1 + 5, x2 + 3, y2 + 5, 28, fill="#dfe2e7", outline="")  # shadow
        rounded_rect(c, x1, y1, x2, y2, 28, fill=fill, outline=edge, width=2)
        cx, cy = w / 2, (y1 + y2) / 2

        c.create_text(cx, y1 + 30, text=label, fill=label_color,
                      font=("Segoe UI", 10, "bold"))
        size = 38 if len(main) <= 14 else 30 if len(main) <= 24 else 22
        main_y = cy - 30 if example else cy - 8
        c.create_text(cx, main_y, text=main, fill=main_color, justify="center",
                      font=("Segoe UI", size, "bold"), width=x2 - x1 - 60)
        if example:
            c.create_text(cx, main_y + size + 34, text=f"“{example}”", fill=TEXT,
                          justify="center", font=("Segoe UI", 13), width=x2 - x1 - 80)
        if sub:
            c.create_text(cx, y2 - 34, text=sub, fill=MUTED, font=("Segoe UI", 11, "italic"))

    def show(self):
        if not self.deck:
            self._draw_card("NO WORDS YET", MUTED,
                            "Add some words in the Words tab", MUTED, "", SURFACE, BORDER)
            self.progress_label.configure(text="")
            self.progress.configure(value=0)
            self.flip_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            return

        self.flip_btn.configure(state="normal")
        self.next_btn.configure(state="normal")
        word = self.deck[self.index]
        if self.flipped:
            self._draw_card("ENGLISH", BLUE, word["english"], BLUE,
                            f"{danish_display(word)}  ·  {word['type']}", BLUE_SOFT, "#c9d8f2",
                            example=word.get("example", ""))
        else:
            self._draw_card("DANSK", RED, danish_display(word), TEXT,
                            word["type"], SURFACE, BORDER)
        self.progress_label.configure(text=f"Card {self.index + 1} of {len(self.deck)}")
        self.progress.configure(maximum=len(self.deck), value=self.index + 1)

    def flip(self):
        if self.deck:
            self.flipped = not self.flipped
            self.show()

    def next_word(self):
        if not self.deck:
            return
        self.index += 1
        if self.index >= len(self.deck):
            messagebox.showinfo("Godt klaret!",
                                f"You went through all {len(self.deck)} words. Shuffling again!")
            random.shuffle(self.deck)
            self.index = 0
        self.flipped = False
        self.show()


# --------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dansk – Danish vocabulary trainer")
        scale = self.winfo_fpixels("1i") / 96  # follow Windows display scaling
        self.geometry(f"{int(900 * scale)}x{int(640 * scale)}")
        self.minsize(int(760 * scale), int(520 * scale))
        setup_styles(self, scale)

        self.words = load_words()
        self.last_entry = None  # where the æ/ø/å buttons type

        self._build_header(scale)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        self.words_tab = WordsTab(notebook, self)
        self.practice_tab = PracticeTab(notebook, self)
        notebook.add(self.words_tab, text="Words")
        notebook.add(self.practice_tab, text="Practice")
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.notebook = notebook

        # Keyboard shortcuts for the flashcard game (only on the Practice tab).
        self.bind("<space>", lambda e: self._practice_key(self.practice_tab.flip))
        self.bind("<Right>", lambda e: self._practice_key(self.practice_tab.next_word))

    def _build_header(self, scale):
        header = tk.Frame(self, bg=SURFACE, padx=18, pady=12)
        header.pack(fill="x")
        flag_w, flag_h = int(37 * scale), int(28 * scale)
        flag = tk.Canvas(header, width=flag_w, height=flag_h, highlightthickness=0, bg=SURFACE)
        flag.pack(side="left")
        draw_flag(flag, flag_w, flag_h)
        tk.Label(header, text="Dansk", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=(12, 6))
        tk.Label(header, text="your Danish word bank", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 11)).pack(side="left", pady=(6, 0))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def _on_tab_changed(self, _event):
        if self.notebook.select() == str(self.practice_tab):
            self.practice_tab.start()

    def _practice_key(self, action):
        if self.notebook.select() == str(self.practice_tab):
            action()
            return "break"

    def track_entry(self, entry):
        """Remember the most recently focused entry for the æ/ø/å buttons."""
        if self.last_entry is None:
            self.last_entry = entry
        entry.bind("<FocusIn>", lambda e: setattr(self, "last_entry", entry), add="+")

    def insert_letter(self, letter):
        entry = self.last_entry
        if entry is None:
            return "break"
        if entry.selection_present():
            entry.delete("sel.first", "sel.last")
        entry.insert("insert", letter)
        entry.focus_set()
        return "break"

    def find_word(self, word_id):
        return next((w for w in self.words if w["id"] == word_id), None)

    def save(self):
        try:
            save_words(self.words)
        except OSError as e:
            messagebox.showerror("Error", f"Could not save {DATA_FILE}:\n{e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        try:  # crisp (non-blurry) text on high-DPI screens
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    App().mainloop()
