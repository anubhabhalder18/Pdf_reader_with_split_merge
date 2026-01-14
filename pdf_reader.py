import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Menu, ttk
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageDraw
import json
import os

# --- Configuration & Theme ---
HISTORY_FILE = "pdf_history.json"
ICON_PATH = "icon.ico"

# Modern Dark Theme Palette
COLORS = {
    "bg": "#2b2b2b",           
    "toolbar": "#3c3f41",      
    "canvas": "#1e1e1e",       
    "sidebar": "#252526",      
    "text": "#cccccc",         
    "accent": "#007acc",       
    "accent_hover": "#0098ff", 
    "btn_text": "#ffffff",
    "shadow": "#101010",       
    "entry_bg": "#3c3f41",
    "list_bg": "#1e1e1e"
}

# --- Global Helper: Apply Icon ---
def apply_window_icon(window):
    """Applies the icon to any given window (Root or Toplevel)"""
    if os.path.exists(ICON_PATH):
        try:
            window.iconbitmap(ICON_PATH)
        except:
            try:
                img = tk.PhotoImage(file=ICON_PATH)
                window.iconphoto(True, img)
            except: pass

# --- Global Helper: Styled Button ---
def create_btn(parent, text, cmd, bg=COLORS["toolbar"], fg=COLORS["text"], width=None, font=("Segoe UI", 10)):
    b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, 
                  bd=0, relief=tk.FLAT, activebackground=COLORS["accent"], activeforeground="white",
                  font=font, width=width, padx=10, pady=5)
    b.bind("<Enter>", lambda e: b.config(bg=COLORS["accent"], fg="white"))
    b.bind("<Leave>", lambda e: b.config(bg=bg, fg=fg))
    return b

# --- Tool Window: Merge PDF ---
class MergeWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Merge PDFs")
        self.geometry("600x400")
        self.configure(bg=COLORS["bg"])
        self.transient(parent) 
        apply_window_icon(self) # Apply Icon
        
        self.pdf_list = [] 

        # Layout
        main_frame = tk.Frame(self, bg=COLORS["bg"], padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.lb_files = tk.Listbox(main_frame, bg=COLORS["list_bg"], fg=COLORS["text"], 
                                   selectbackground=COLORS["accent"], selectforeground="white",
                                   bd=0, highlightthickness=1, highlightbackground=COLORS["toolbar"])
        self.lb_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sb = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.lb_files.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.lb_files.config(yscrollcommand=sb.set)

        btn_frame = tk.Frame(main_frame, bg=COLORS["bg"], padx=10)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        create_btn(btn_frame, "➕ Add Files", self.add_files, width=12).pack(pady=2)
        create_btn(btn_frame, "➖ Remove", self.remove_file, width=12).pack(pady=2)
        tk.Frame(btn_frame, bg=COLORS["bg"], height=10).pack() 
        create_btn(btn_frame, "▲ Move Up", self.move_up, width=12).pack(pady=2)
        create_btn(btn_frame, "▼ Move Down", self.move_down, width=12).pack(pady=2)
        tk.Frame(btn_frame, bg=COLORS["bg"], height=20).pack() 
        
        btn_merge = tk.Button(btn_frame, text="MERGE NOW", command=self.do_merge, 
                              bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"), 
                              bd=0, relief=tk.FLAT, padx=10, pady=10)
        btn_merge.pack(pady=10, fill=tk.X)
        btn_merge.bind("<Enter>", lambda e: btn_merge.config(bg=COLORS["accent_hover"]))
        btn_merge.bind("<Leave>", lambda e: btn_merge.config(bg=COLORS["accent"]))

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        for f in files:
            self.pdf_list.append(f)
            self.lb_files.insert(tk.END, os.path.basename(f))

    def remove_file(self):
        sel = self.lb_files.curselection()
        if sel:
            idx = sel[0]
            self.lb_files.delete(idx)
            self.pdf_list.pop(idx)

    def move_up(self):
        sel = self.lb_files.curselection()
        if not sel: return
        i = sel[0]
        if i > 0:
            text = self.lb_files.get(i)
            path = self.pdf_list.pop(i)
            self.lb_files.delete(i)
            self.lb_files.insert(i-1, text)
            self.pdf_list.insert(i-1, path)
            self.lb_files.select_set(i-1)

    def move_down(self):
        sel = self.lb_files.curselection()
        if not sel: return
        i = sel[0]
        if i < self.lb_files.size() - 1:
            text = self.lb_files.get(i)
            path = self.pdf_list.pop(i)
            self.lb_files.delete(i)
            self.lb_files.insert(i+1, text)
            self.pdf_list.insert(i+1, path)
            self.lb_files.select_set(i+1)

    def do_merge(self):
        if len(self.pdf_list) < 2:
            messagebox.showwarning("Merge", "Please add at least 2 PDF files.")
            return
        
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not save_path: return

        try:
            out_doc = fitz.open()
            for pdf in self.pdf_list:
                with fitz.open(pdf) as src:
                    out_doc.insert_pdf(src)
            out_doc.save(save_path)
            messagebox.showinfo("Success", "PDFs Merged Successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

# --- Tool Window: Split PDF ---
class SplitWindow(tk.Toplevel):
    def __init__(self, parent, current_doc, current_path):
        super().__init__(parent)
        self.title("Split PDF")
        self.geometry("500x300")
        self.configure(bg=COLORS["bg"])
        self.transient(parent)
        apply_window_icon(self) # Apply Icon
        
        self.doc = current_doc
        self.total_pages = len(current_doc)
        
        filename = os.path.basename(current_path) if current_path else "Untitled"
        tk.Label(self, text=f"Split File: {filename}", bg=COLORS["bg"], fg="white", 
                 font=("Segoe UI", 12, "bold")).pack(pady=(20, 5))
        
        tk.Label(self, text=f"Total Pages: {self.total_pages}", bg=COLORS["bg"], fg="#aaaaaa").pack()

        input_frame = tk.Frame(self, bg=COLORS["bg"], pady=20)
        input_frame.pack()
        
        tk.Label(input_frame, text="Page Range:", bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        self.ent_range = tk.Entry(input_frame, width=40, bg=COLORS["entry_bg"], fg="white", 
                                  insertbackground="white", bd=0, font=("Segoe UI", 11))
        self.ent_range.pack(pady=5, ipady=5)
        
        tk.Label(input_frame, text="Example: 1-5, 8, 10-12", bg=COLORS["bg"], fg="#777777", font=("Segoe UI", 9)).pack(anchor="w")

        btn_split = tk.Button(self, text="Extract & Save", command=self.do_split,
                              bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"),
                              bd=0, relief=tk.FLAT, padx=20, pady=8)
        btn_split.pack(pady=10)
        btn_split.bind("<Enter>", lambda e: btn_split.config(bg=COLORS["accent_hover"]))
        btn_split.bind("<Leave>", lambda e: btn_split.config(bg=COLORS["accent"]))

    def do_split(self):
        range_str = self.ent_range.get()
        if not range_str: return

        try:
            pages_to_keep = []
            for p in range_str.split(','):
                p = p.strip()
                if '-' in p:
                    s, e = map(int, p.split('-'))
                    if s < 1: s = 1
                    if e > self.total_pages: e = self.total_pages
                    pages_to_keep.extend(range(s-1, e))
                else:
                    val = int(p)
                    if 1 <= val <= self.total_pages:
                        pages_to_keep.append(val-1)
            
            if not pages_to_keep:
                messagebox.showwarning("Error", "No valid pages selected.")
                return

            new_doc = fitz.open()
            new_doc.insert_pdf(self.doc, from_page=-1, to_page=-1, start_at=-1)
            new_doc.select(pages_to_keep)
            
            save_path = filedialog.asksaveasfilename(defaultextension=".pdf", title="Save Split PDF")
            if save_path:
                new_doc.save(save_path)
                messagebox.showinfo("Success", "Pages extracted successfully.")
                self.destroy()

        except ValueError:
            messagebox.showerror("Error", "Invalid format. Use numbers and hyphens (e.g. 1-3, 5)")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# --- Main Application ---
class PDFReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Python PDF Reader Pro")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS["bg"])
        
        apply_window_icon(self.root) # Apply Icon
        
        self.doc = None
        self.current_file_path = None
        self.zoom_level = 1.0 
        self.min_zoom = 0.2
        self.max_zoom = 5.0
        self.current_page_index = 0
        self.sidebar_visible = True
        self.resize_timer = None
        
        self.layout_mode = "single"  
        self.text_only_mode = tk.BooleanVar(value=False)
        self.hand_mode = False       
        
        self.page_images = {} 
        self.page_coords = []
        
        self._setup_ui()
        
        # --- Keyboard Shortcuts ---
        self.root.bind('<Control-o>', lambda e: self.open_pdf())
        self.root.bind('<Control-s>', lambda e: self.save_pdf())
        self.root.bind('<Control-equal>', lambda e: self.zoom_in()) # Ctrl +
        self.root.bind('<Control-minus>', lambda e: self.zoom_out()) # Ctrl -
        
        # --- Bindings ---
        self.root.bind('<Configure>', self.on_resize_window)
        self.canvas.bind('<MouseWheel>', self.on_vertical_scroll)       
        self.canvas.bind('<Button-4>', self.on_vertical_scroll)         
        self.canvas.bind('<Button-5>', self.on_vertical_scroll)         
        self.root.bind('<Shift-MouseWheel>', self.on_horizontal_scroll)
        self.root.bind('<Shift-Button-4>', self.on_horizontal_scroll)   
        self.root.bind('<Shift-Button-5>', self.on_horizontal_scroll)   
        self.root.bind('<Control-MouseWheel>', self.on_zoom_scroll) 
        self.canvas.bind('<ButtonPress-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        
        self.history = self.load_history()
        self.check_visibility_loop()

    def _setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", gripcount=0, background=COLORS["toolbar"], troughcolor=COLORS["bg"], borderwidth=0, arrowcolor="white")
        style.configure("Horizontal.TScrollbar", gripcount=0, background=COLORS["toolbar"], troughcolor=COLORS["bg"], borderwidth=0, arrowcolor="white")

        toolbar = tk.Frame(self.root, bd=0, bg=COLORS["toolbar"], height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 1))

        self.btn_toggle = create_btn(toolbar, "☰", self.toggle_sidebar, width=3, font=("Arial", 12))
        self.btn_toggle.pack(side=tk.LEFT)

        create_btn(toolbar, "📂 Open (Ctrl+O)", self.open_pdf).pack(side=tk.LEFT, padx=1)
        create_btn(toolbar, "💾 Save (Ctrl+S)", self.save_pdf).pack(side=tk.LEFT, padx=1)
        
        tk.Frame(toolbar, width=1, bg="gray", height=20).pack(side=tk.LEFT, padx=10, fill=tk.Y, pady=5)

        create_btn(toolbar, "Merge", self.open_merge_window).pack(side=tk.LEFT, padx=1)
        create_btn(toolbar, "Split", self.open_split_window).pack(side=tk.LEFT, padx=1)
        
        tk.Frame(toolbar, width=1, bg="gray", height=20).pack(side=tk.LEFT, padx=10, fill=tk.Y, pady=5)

        self.btn_hand = create_btn(toolbar, "✋", self.toggle_hand_mode, width=3)
        self.btn_hand.pack(side=tk.LEFT, padx=1)

        self.btn_layout = tk.Menubutton(toolbar, text="Layout", bg=COLORS["toolbar"], fg=COLORS["text"], 
                                        bd=0, relief=tk.FLAT, font=("Segoe UI", 10), padx=10, pady=5)
        self.btn_layout.bind("<Enter>", lambda e: self.btn_layout.config(bg=COLORS["accent"], fg="white"))
        self.btn_layout.bind("<Leave>", lambda e: self.btn_layout.config(bg=COLORS["toolbar"], fg=COLORS["text"]))
        
        self.layout_menu = Menu(self.btn_layout, tearoff=0, bg=COLORS["sidebar"], fg=COLORS["text"], activebackground=COLORS["accent"])
        self.layout_menu.add_command(label="Single Column", command=lambda: self.change_layout("single"))
        self.layout_menu.add_command(label="Two Columns", command=lambda: self.change_layout("double"))
        self.btn_layout.config(menu=self.layout_menu)
        self.btn_layout.pack(side=tk.LEFT, padx=1)

        self.chk_txt = tk.Checkbutton(toolbar, text="Txt Only", variable=self.text_only_mode, 
                                      command=self.refresh_view, bg=COLORS["toolbar"], fg=COLORS["text"], 
                                      selectcolor=COLORS["bg"], activebackground=COLORS["toolbar"], activeforeground="white", bd=0)
        self.chk_txt.pack(side=tk.LEFT, padx=5)

        create_btn(toolbar, "Fit", self.fit_width).pack(side=tk.LEFT, padx=1)
        create_btn(toolbar, "-", self.zoom_out, width=2).pack(side=tk.LEFT)
        self.lbl_zoom = tk.Label(toolbar, text="100%", width=5, bg=COLORS["toolbar"], fg=COLORS["text"], font=("Segoe UI", 10, "bold"))
        self.lbl_zoom.pack(side=tk.LEFT)
        create_btn(toolbar, "+", self.zoom_in, width=2).pack(side=tk.LEFT)

        fr_nav = tk.Frame(toolbar, bg=COLORS["toolbar"])
        fr_nav.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(fr_nav, text="Page:", bg=COLORS["toolbar"], fg=COLORS["text"]).pack(side=tk.LEFT)
        self.page_entry_var = tk.StringVar(value="0")
        self.ent_page = tk.Entry(fr_nav, textvariable=self.page_entry_var, width=4, justify="center", 
                                 bg=COLORS["bg"], fg="white", insertbackground="white", bd=0)
        self.ent_page.pack(side=tk.LEFT, padx=5, ipady=3)
        self.ent_page.bind('<Return>', self.jump_to_page_from_entry)
        
        self.lbl_total_pages = tk.Label(fr_nav, text="/ 0", bg=COLORS["toolbar"], fg=COLORS["text"])
        self.lbl_total_pages.pack(side=tk.LEFT)

        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=2, bg=COLORS["bg"], bd=0)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.sidebar_frame = tk.Frame(self.main_pane, bg=COLORS["sidebar"], width=200)
        self.main_pane.add(self.sidebar_frame, minsize=150)
        
        self.page_listbox = tk.Listbox(self.sidebar_frame, selectmode=tk.SINGLE, 
                                       bg=COLORS["sidebar"], fg=COLORS["text"], bd=0, 
                                       highlightthickness=0, activestyle="none",
                                       selectbackground=COLORS["accent"], selectforeground="white")
        self.page_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.page_listbox.bind('<<ListboxSelect>>', self.on_sidebar_click)
        
        tools_frame = tk.Frame(self.sidebar_frame, bg=COLORS["sidebar"])
        tools_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        def create_side_btn(text, cmd, col, fg=COLORS["text"]):
            b = tk.Button(tools_frame, text=text, command=cmd, bg=COLORS["sidebar"], fg=fg, 
                          bd=0, relief=tk.FLAT, activebackground=COLORS["accent"], activeforeground="white")
            b.bind("<Enter>", lambda e: b.config(bg=COLORS["accent"], fg="white"))
            b.bind("<Leave>", lambda e: b.config(bg=COLORS["sidebar"], fg=fg))
            b.grid(row=0, column=col, sticky="ew")
            return b

        create_side_btn("▲", self.move_page_up, 0)
        create_side_btn("▼", self.move_page_down, 1)
        create_side_btn("⟳", self.rotate_current_page, 2)
        create_side_btn("🗑", self.delete_current_page, 3, fg="#ff6b6b")
        
        for i in range(4): tools_frame.columnconfigure(i, weight=1)

        self.frame_container = tk.Frame(self.main_pane, bg=COLORS["canvas"])
        self.main_pane.add(self.frame_container, minsize=400)

        self.v_scroll = ttk.Scrollbar(self.frame_container, orient=tk.VERTICAL, style="Vertical.TScrollbar")
        self.h_scroll = ttk.Scrollbar(self.frame_container, orient=tk.HORIZONTAL, style="Horizontal.TScrollbar")
        
        self.canvas = tk.Canvas(self.frame_container, bg=COLORS["canvas"], highlightthickness=0,
                                yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def open_merge_window(self):
        MergeWindow(self.root)

    def open_split_window(self):
        if not self.doc:
            messagebox.showwarning("Split", "Open a PDF first.")
            return
        SplitWindow(self.root, self.doc, self.current_file_path)

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.main_pane.forget(self.sidebar_frame)
            self.sidebar_visible = False
        else:
            self.main_pane.add(self.sidebar_frame, before=self.frame_container, width=200)
            self.sidebar_visible = True

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try: return json.load(open(HISTORY_FILE, 'r'))
            except: return {}
        return {}

    def save_history(self):
        if self.current_file_path and self.doc:
            self.history[self.current_file_path] = getattr(self, 'current_page_index', 0)
            with open(HISTORY_FILE, 'w') as f: json.dump(self.history, f)

    def open_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path: return
        
        if self.doc:
            self.save_history()
            try: self.doc.close()
            except: pass
        
        self.doc = None
        self.page_images.clear()
        self.page_coords = []
        self.canvas.delete("all")
        
        self.current_file_path = path
        try: 
            self.doc = fitz.open(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.root.title(f"PDF Editor - {os.path.basename(path)}")
        self.lbl_total_pages.config(text=f"/ {len(self.doc)}")
        self.zoom_level = 1.0 
        self.update_sidebar()
        self.refresh_view()
        
        saved_page = self.history.get(path, 0)
        if saved_page >= len(self.doc): saved_page = 0
        self.go_to_page(saved_page)

    def save_pdf(self):
        if not self.doc: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if path:
            try:
                self.doc.save(path, garbage=4)
                messagebox.showinfo("Success", "PDF Saved Successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save: {e}")

    def jump_to_page_from_entry(self, event=None):
        if not self.doc: return
        try:
            val = self.page_entry_var.get()
            page_num = int(val)
            target_idx = page_num - 1
            if 0 <= target_idx < len(self.doc):
                self.go_to_page(target_idx)
                self.canvas.focus_set() 
            else:
                messagebox.showwarning("Range Error", f"Page must be between 1 and {len(self.doc)}")
        except ValueError:
            pass

    def rotate_current_page(self):
        if not self.doc: return
        idx = self.current_page_index
        self.doc[idx].set_rotation(self.doc[idx].rotation + 90)
        self.refresh_view()

    def move_page_up(self):
        if not self.doc: return
        idx = self.get_selected_sidebar_page() or self.current_page_index
        if idx > 0:
            self.doc.move_page(idx, idx - 1)
            self.update_sidebar()
            self.page_listbox.selection_set(idx - 1)
            self.go_to_page(idx - 1)
            self.refresh_view()

    def move_page_down(self):
        if not self.doc: return
        idx = self.get_selected_sidebar_page() or self.current_page_index
        if idx < len(self.doc) - 1:
            self.doc.move_page(idx + 1, idx)
            self.update_sidebar()
            self.page_listbox.selection_set(idx + 1)
            self.go_to_page(idx + 1)
            self.refresh_view()
            
    def delete_current_page(self):
        if not self.doc: return
        idx = self.get_selected_sidebar_page() or self.current_page_index
        if messagebox.askyesno("Confirm", f"Delete Page {idx+1}?"):
            self.doc.delete_page(idx)
            self.update_sidebar()
            self.lbl_total_pages.config(text=f"/ {len(self.doc)}")
            self.refresh_view()

    def update_sidebar(self):
        self.page_listbox.delete(0, tk.END)
        if not self.doc: return
        for i in range(len(self.doc)):
            self.page_listbox.insert(tk.END, f"Page {i+1}")

    def on_sidebar_click(self, event):
        sel = self.page_listbox.curselection()
        if sel: self.go_to_page(sel[0])
            
    def get_selected_sidebar_page(self):
        sel = self.page_listbox.curselection()
        if sel: return sel[0]
        return None

    def change_layout(self, mode):
        self.layout_mode = mode
        self.refresh_view()

    def refresh_view(self):
        self.page_images.clear()
        self.canvas.delete("all")
        self.calculate_layout()
        self.render_visible_pages()

    def calculate_layout(self):
        if not self.doc: return
        self.canvas.delete("placeholder")
        self.page_coords = []
        
        PADDING = 40
        current_y = PADDING
        max_row_h = 0
        total_width = 0
        
        for i in range(len(self.doc)):
            page = self.doc[i]
            rect = page.rect
            w = rect.width * self.zoom_level
            h = rect.height * self.zoom_level
            
            x, y = PADDING, current_y
            
            if self.layout_mode == "single":
                current_y += h + PADDING
                total_width = max(total_width, w + PADDING*2)
            elif self.layout_mode == "double":
                is_right = (i % 2 == 1)
                if not is_right: max_row_h = h
                else:
                    prev_w = self.page_coords[-1]['w']
                    x = PADDING + prev_w + PADDING
                    max_row_h = max(max_row_h, h)
                if is_right or i == len(self.doc)-1:
                    current_y += max_row_h + PADDING
                total_width = max(total_width, x + w + PADDING)

            self.page_coords.append({'x': x, 'y': y, 'w': w, 'h': h})
            
            self.canvas.create_rectangle(x+8, y+8, x+w+8, y+h+8, fill=COLORS["shadow"], outline="", tags=("placeholder", f"ph_{i}"))
            self.canvas.create_rectangle(x, y, x+w, y+h, fill="white", outline="#333", tags=("placeholder", f"ph_{i}"))
            self.canvas.create_text(x-10, y+10, text=str(i+1), anchor=tk.NE, fill=COLORS["text"], font=("Segoe UI", 10))

        self.canvas.config(scrollregion=(0, 0, total_width, current_y))
        self.update_zoom_label()

    def on_resize_window(self, event):
        if self.resize_timer:
            self.root.after_cancel(self.resize_timer)
        self.resize_timer = self.root.after(200, self.fit_width)

    def toggle_hand_mode(self):
        self.hand_mode = not self.hand_mode
        if self.hand_mode:
            self.btn_hand.config(bg=COLORS["accent"], fg="white")
            self.canvas.config(cursor="fleur") 
        else:
            self.btn_hand.config(bg=COLORS["toolbar"], fg=COLORS["text"])
            self.canvas.config(cursor="arrow")

    def on_mouse_down(self, event):
        if self.hand_mode: self.canvas.scan_mark(event.x, event.y)

    def on_mouse_drag(self, event):
        if self.hand_mode: self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_vertical_scroll(self, event):
        if event.state & 4: return 
        delta = int(-1*(event.delta/120)) if event.delta else 0
        if event.num == 4: delta = -1
        elif event.num == 5: delta = 1
        self.canvas.yview_scroll(delta, "units")

    def on_horizontal_scroll(self, event):
        delta = int(-1*(event.delta/120)) if event.delta else 0
        if event.num == 4: delta = -1
        elif event.num == 5: delta = 1
        self.canvas.xview_scroll(delta, "units")

    def on_zoom_scroll(self, event):
        if event.delta > 0 or event.num == 4: self.zoom_in()
        else: self.zoom_out()
        return "break"

    def zoom_in(self):  self._set_zoom(self.zoom_level * 1.25)
    def zoom_out(self): self._set_zoom(self.zoom_level / 1.25)
    
    def fit_width(self):
        if not self.doc: return
        canvas_w = self.canvas.winfo_width()
        if canvas_w < 100: canvas_w = 800
        page_w = self.doc[0].rect.width
        factor = 2 if self.layout_mode == "double" else 1
        sb_width = 0 if not self.sidebar_visible else 200
        target = (canvas_w - sb_width - 120) / (page_w * factor)
        self._set_zoom(target)

    def _set_zoom(self, new_level):
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, new_level))
        top_page = getattr(self, 'current_page_index', 0)
        self.refresh_view()
        self.go_to_page(top_page)

    def update_zoom_label(self):
        self.lbl_zoom.config(text=f"{int(self.zoom_level * 100)}%")

    def check_visibility_loop(self):
        if self.doc:
            self.render_visible_pages()
            y = self.canvas.canvasy(0) + 20
            for i, c in enumerate(self.page_coords):
                if c['y'] <= y < c['y'] + c['h']:
                    if self.current_page_index != i:
                        self.current_page_index = i
                        if self.root.focus_get() != self.ent_page:
                            self.page_entry_var.set(str(i+1))
                        self.page_listbox.selection_clear(0, tk.END)
                        self.page_listbox.selection_set(i)
                        self.page_listbox.see(i)
                    break
        self.root.after(150, self.check_visibility_loop)

    def render_visible_pages(self):
        if not self.doc: return
        view_top = self.canvas.canvasy(0)
        view_h = self.canvas.winfo_height()
        view_bot = view_top + view_h
        buffer = 800 
        visible = set()
        for i, c in enumerate(self.page_coords):
            if (c['y'] + c['h'] > view_top - buffer) and (c['y'] < view_bot + buffer):
                visible.add(i)
                if i not in self.page_images:
                    self._render_page(i)
        for k in list(self.page_images.keys()):
            if k not in visible:
                self.canvas.delete(f"img_{k}")
                del self.page_images[k]

    def _render_page(self, i):
        try:
            page = self.doc.load_page(i)
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            if self.text_only_mode.get():
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                draw = ImageDraw.Draw(img)
                for item in page.get_images(full=True):
                    xref = item[0]
                    for r in page.get_image_rects(xref):
                        x0, y0, x1, y1 = [v * self.zoom_level for v in (r.x0, r.y0, r.x1, r.y1)]
                        draw.rectangle([x0, y0, x1, y1], fill="white")
                tk_img = ImageTk.PhotoImage(img)
            else:
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                tk_img = ImageTk.PhotoImage(img)

            self.page_images[i] = tk_img
            c = self.page_coords[i]
            self.canvas.create_image(c['x'], c['y'], image=tk_img, anchor=tk.NW, tags=f"img_{i}")
            self.canvas.tag_raise(f"img_{i}", "placeholder")
        except Exception as e:
            print(f"Render error page {i}: {e}")

    def on_close(self):
        self.save_history()
        self.root.destroy()

    def go_to_page(self, i):
        if 0 <= i < len(self.page_coords):
            y = self.page_coords[i]['y']
            self.canvas.yview_moveto(y / self.canvas.bbox("all")[3])
            self.page_listbox.selection_clear(0, tk.END)
            self.page_listbox.selection_set(i)
            self.page_listbox.see(i)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFReader(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()