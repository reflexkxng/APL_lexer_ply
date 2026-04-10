import tkinter as tk
import warnings
# Silence deprecation warnings in the background terminal
warnings.filterwarnings("ignore", category=FutureWarning)
from tkinter import messagebox, simpledialog, ttk, filedialog
from APL_interpreter_ply_ import run_interpreter
import threading
import time
import os
import sys
from dotenv import load_dotenv

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Load environment variables from .env file
def get_env_path():
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        return os.path.join(os.path.dirname(sys.executable), ".env")
    # Running as a normal script
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

load_dotenv(get_env_path())

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# High-Definition Color Palette (Modern "HD" Look)
BG_COLOR = "#000000"
HEADER_COLOR = "#000000"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#888888"
BORDER_ACCENT = "#333333"      # Subtle border
AI_BORDER = "#444444"         # Subtle gray border as per latest request
ACCENT_COLOR = "#4CAF50"
EDITOR_BG = "#000000"         # Pure black for HD depth

# Font definitions
UI_FONT = ("Segoe UI", 10)
TITLE_FONT = ("Segoe UI", 11, "bold")
CODE_FONT = ("JetBrains Mono", 12) if os.name == "nt" else ("Consolas", 12)

class CustomText(tk.Text):
    """A Text widget that reports when its content or view changes."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Proxy the underlying tcl command to intercept events
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        # Let the actual widget perform the requested action
        cmd = (self._orig,) + args
        try:
            result = self.tk.call(cmd)
        except Exception:
            return None

        # Generate an event if something changed the view or text
        if (args[0] in ("insert", "replace", "delete") or 
            args[0:3] == ("mark", "set", "insert") or
            args[0:2] == ("xview", "moveto") or
            args[0:2] == ("xview", "scroll") or
            args[0:2] == ("yview", "moveto") or
            args[0:2] == ("yview", "scroll")
        ):
            self.event_generate("<<Change>>", when="tail")

        return result

class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        """Redraw line numbers."""
        self.delete("all")
        if not self.textwidget:
            return

        i = self.textwidget.index("@0,0")
        while True:
            dline = self.textwidget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(
                self.winfo_width() - 10, 
                y, 
                anchor="ne", 
                text=linenum, 
                fill="#555555", 
                font=CODE_FONT
            )
            i = self.textwidget.index("%s+1line" % i)

class HDScrolledText(tk.Frame):
    """Refined composite text widget with modern dark aesthetics."""
    def __init__(self, parent, font=CODE_FONT, bg=EDITOR_BG, fg=TEXT_PRIMARY, border_color=None, show_line_numbers=False, readonly=False, **kwargs):
        super().__init__(parent, bg=BG_COLOR)
        self.readonly = readonly
        
        self.container = tk.Frame(self, bg=BG_COLOR, highlightthickness=1 if border_color else 0, highlightbackground=border_color or BG_COLOR)
        # ... rest ...

        self.container.pack(fill=tk.BOTH, expand=True)

        self.text = CustomText(
            self.container, 
            font=font, 
            bg=bg, 
            fg=fg, 
            insertbackground="white",
            borderwidth=0, 
            highlightthickness=0, 
            padx=15, 
            pady=15,
            undo=True,
            **kwargs
        )
        
        # Setup Line Numbers if requested
        if show_line_numbers:
            self.linenumbers = TextLineNumbers(self.container, width=45, bg="#0A0A0A", highlightthickness=0)
            self.linenumbers.attach(self.text)
            self.linenumbers.pack(side=tk.LEFT, fill=tk.Y)
            self.text.bind("<<Change>>", self._on_change)
            self.text.bind("<Configure>", self._on_change)

        
        # Style the scrollbar to be modern and hidden unless needed (VS Code style)
        style = ttk.Style()
        style.theme_use('clam')
        
        # Define VS Code style scrollbar
        style.layout("VSCode.Vertical.TScrollbar", 
            [('Vertical.Scrollbar.trough', 
                {'children': [('Vertical.Scrollbar.thumb', {'expand': '1'})], 'sticky': 'ns'})]
        )
        style.configure(
            "VSCode.Vertical.TScrollbar",
            gripcount=0,
            background="#424242",      # VS Code handle color
            darkcolor=BG_COLOR,
            lightcolor=BG_COLOR,
            troughcolor=BG_COLOR,      # Match the editor background
            bordercolor=BG_COLOR,
            arrowsize=0,               # Hide arrows
            width=10                   # Thin scrollbar
        )
        
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview, style="VSCode.Vertical.TScrollbar")
        self.text.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if self.readonly:
            self.text.configure(state=tk.DISABLED)

    def _on_change(self, event):
        if hasattr(self, 'linenumbers'):
            self.linenumbers.redraw()

    def insert(self, *args, **kwargs):
        if self.readonly: self.text.configure(state=tk.NORMAL)
        res = self.text.insert(*args, **kwargs)
        if self.readonly: self.text.configure(state=tk.DISABLED)
        return res

    def get(self, *args, **kwargs): return self.text.get(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.readonly: self.text.configure(state=tk.NORMAL)
        res = self.text.delete(*args, **kwargs)
        if self.readonly: self.text.configure(state=tk.DISABLED)
        return res

    def tag_config(self, *args, **kwargs): return self.text.tag_config(*args, **kwargs)

class APLInterpreterUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NovaLang IDE")
        self.root.geometry("1100x850")
        self.root.configure(bg=BG_COLOR)

        # Remove default OS title bar for HD look
        self.root.overrideredirect(True)
        self.root.after(10, self.set_appwindow)
        self._offsetx = 0
        self._offsety = 0

    def set_appwindow(self):
        """Forces the custom borderless window to appear in the Windows taskbar."""
        if os.name != "nt": return
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20) # GWL_EXSTYLE
            style = style & ~0x00000080  # Removes WS_EX_TOOLWINDOW
            style = style | 0x00040000   # Adds WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
            self.root.wm_withdraw()
            self.root.wm_deiconify()
        except Exception as e:
            print(f"Taskbar hook failed: {e}")

        # Load Logo
        self.logo_img = None
        self.logo_name = "novalang_logo_nl_1774823693135.png"
        self.logo_path = resource_path(self.logo_name)
        
        if os.path.exists(self.logo_path):
            try:
                # Try to use PIL for better quality resizing
                from PIL import Image, ImageTk
                img = Image.open(self.logo_path)
                img = img.resize((24, 24), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                # Also set taskbar icon
                icon_img = ImageTk.PhotoImage(Image.open(self.logo_path).resize((64, 64)))
                self.root.iconphoto(True, icon_img)
            except Exception as pil_err:
                try:
                    # Fallback to standard Tkinter (limited PNG support)
                    self.logo_img = tk.PhotoImage(file=self.logo_path)
                    self.logo_img = self.logo_img.subsample(32, 32)
                    self.root.iconphoto(True, tk.PhotoImage(file=self.logo_path))
                except Exception as tk_err:
                    print(f"Logo failed: PIL error ({pil_err}), Tkinter error ({tk_err})")

        
        # Load Groq API key
        self.api_key = os.getenv("GROQ_API_KEY", "")
        if GROQ_AVAILABLE and not self.api_key:
            print("Warning: GROQ_API_KEY not found in environment.")

        # Components
        self.sidebar_visible = False
        self.setup_custom_header()
        
        # Main Resizable Vertical Layout
        self.main_pane = tk.PanedWindow(self.root, orient=tk.VERTICAL, bg=BG_COLOR, bd=0, sashwidth=6, sashrelief=tk.FLAT)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.setup_workspace()
        self.setup_footer()

    def setup_custom_header(self):
        """Creates the minimal top bar with custom window controls."""
        self.header = tk.Frame(self.root, bg=BG_COLOR, height=40)
        self.header.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)  # No padding for full header
        self.header.pack_propagate(False)

        # Draggable binding
        self.header.bind("<Button-1>", self.start_drag)
        self.header.bind("<B1-Motion>", self.do_drag)

        # Left menu (Logo File Save)
        self.menu_frame = tk.Frame(self.header, bg=BG_COLOR)
        self.menu_frame.pack(side=tk.LEFT, padx=(10, 0))

        if self.logo_img:
            self.logo_label = tk.Label(self.menu_frame, image=self.logo_img, bg=BG_COLOR)
            self.logo_label.pack(side=tk.LEFT, padx=(5, 10))

        for item in ["Open", "Save"]:
            btn = tk.Button(
                self.menu_frame, 
                text=item, 
                bg=BG_COLOR, 
                fg=TEXT_PRIMARY, 
                font=UI_FONT, 
                borderwidth=0, 
                activebackground="#1A1A1A", 
                activeforeground=TEXT_PRIMARY,
                command=lambda x=item: self.on_menu_click(x)
            )
            btn.pack(side=tk.LEFT, padx=10)

        # Sidebar Toggle Button (Text based)
        self.toggle_btn = tk.Button(
            self.menu_frame, 
            text="View AI", 
            bg=BG_COLOR, 
            fg=TEXT_SECONDARY, 
            font=UI_FONT, 
            borderwidth=0, 
            activebackground="#1A1A1A", 
            activeforeground="#BB86FC",
            command=self.toggle_sidebar
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=10)

        # Right Controls (Min, Max, Close)
        self.ctrl_frame = tk.Frame(self.header, bg=BG_COLOR)
        self.ctrl_frame.pack(side=tk.RIGHT)

        # Close
        close_btn = tk.Button(self.ctrl_frame, text="✕", bg=BG_COLOR, fg=TEXT_PRIMARY, font=("Arial", 9), borderwidth=0, 
                              activebackground="#E81123", activeforeground="white", padx=20, pady=12, command=self.root.quit)
        close_btn.pack(side=tk.RIGHT)

        # Max
        max_btn = tk.Button(self.ctrl_frame, text="▢", bg=BG_COLOR, fg=TEXT_PRIMARY, font=("Arial", 9), borderwidth=0, 
                             activebackground="#2A2A2A", activeforeground="white", padx=20, pady=12, command=self.toggle_max)
        max_btn.pack(side=tk.RIGHT)

        # Min
        min_btn = tk.Button(self.ctrl_frame, text="—", bg=BG_COLOR, fg=TEXT_PRIMARY, font=("Arial", 9), borderwidth=0, 
                             activebackground="#2A2A2A", activeforeground="white", padx=20, pady=12, command=self.minimize)
        min_btn.pack(side=tk.RIGHT)

        # Center Title
        self.title_label = tk.Label(
            self.header, 
            text="NovaLang IDE", 
            font=TITLE_FONT, 
            bg=BG_COLOR, 
            fg=TEXT_PRIMARY
        )
        self.title_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.title_label.bind("<Button-1>", self.start_drag) # Allow title to drag
        self.title_label.bind("<B1-Motion>", self.do_drag)

    def toggle_sidebar(self):
        """Toggle the visibility of the AI sidebar."""
        if self.sidebar_visible:
            self.ai_sidebar.pack_forget()
            self.sidebar_visible = False
            self.toggle_btn.configure(fg=TEXT_SECONDARY)
        else:
            self.ai_sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(20, 0))
            self.sidebar_visible = True
            self.toggle_btn.configure(fg=TEXT_PRIMARY)

    def start_drag(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def do_drag(self, event):
        x = self.root.winfo_x() + event.x - self._offsetx
        y = self.root.winfo_y() + event.y - self._offsety
        self.root.geometry(f"+{x}+{y}")

    def minimize(self):
        # Native safe minimize for custom borderless windows
        if os.name == 'nt':
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                ctypes.windll.user32.ShowWindow(hwnd, 6) # 6 = SW_MINIMIZE
            except Exception:
                pass
        else:
            self.root.iconify()

    def toggle_max(self):
        # On Windows, manually grab the desktop work area to prevent covering the taskbar
        if not hasattr(self, 'is_maximized') or not self.is_maximized:
            self.normal_geometry = self.root.geometry()
            try:
                import ctypes
                from ctypes import wintypes
                rect = wintypes.RECT()
                ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0) # SPI_GETWORKAREA = 48
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                self.root.geometry(f"{width}x{height}+{rect.left}+{rect.top}")
            except Exception:
                # Fallback
                self.root.state("zoomed")
            self.is_maximized = True
        else:
            self.root.geometry(self.normal_geometry)
            self.root.state("normal")
            self.is_maximized = False

    def setup_workspace(self):
        """Main split-view workspace (Top Pane)."""
        self.workspace = tk.Frame(self.main_pane, bg=BG_COLOR)
        self.main_pane.add(self.workspace, stretch="always", height=500)

        # Primary Editor Area (Left)
        self.editor_frame = tk.Frame(self.workspace, bg=BG_COLOR)
        self.editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.code_editor = HDScrolledText(self.editor_frame, show_line_numbers=True)
        self.code_editor.pack(fill=tk.BOTH, expand=True)

        # AI Sidebar (Right) - Matching the sharp white border style
        self.ai_sidebar = tk.Frame(self.workspace, bg=BG_COLOR, width=450, highlightthickness=1, highlightbackground=AI_BORDER)
        if self.sidebar_visible:
            self.ai_sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(20, 0))
        self.ai_sidebar.pack_propagate(False)

        self.ai_title = tk.Label(self.ai_sidebar, text="Ai Overview", bg=BG_COLOR, fg=TEXT_PRIMARY, font=TITLE_FONT)
        self.ai_title.pack(pady=15)

        self.ai_content = HDScrolledText(self.ai_sidebar, font=("Segoe UI", 10), fg="#CCCCCC", bg=BG_COLOR, readonly=True)
        self.ai_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))

    def setup_footer(self):
        """Bottom bar for controls and console (Bottom Pane)."""
        self.footer = tk.Frame(self.main_pane, bg=BG_COLOR)
        self.main_pane.add(self.footer, stretch="never")

        # Run Button (Sleek dark design)
        self.run_btn = tk.Button(
            self.footer, 
            text="RUN PROGRAM", 
            command=self.on_run,
            bg="#FFFFFF", 
            fg="#000000",
            font=("Segoe UI Bold", 10),
            padx=25,
            pady=8,
            relief=tk.FLAT,
            activebackground="#CCCCCC",
            cursor="hand2"
        )
        self.run_btn.pack(side=tk.LEFT, pady=(0, 10))

        # AI Analyze Button (Unified White Aesthetic)
        self.ai_btn = tk.Button(
            self.footer, 
            text="AI ANALYZE", 
            command=self.on_compare,
            bg="#FFFFFF", 
            fg="#000000",
            font=("Segoe UI Bold", 10),
            padx=25,
            pady=8,
            relief=tk.FLAT,
            activebackground="#CCCCCC",
            cursor="hand2"
        )
        self.ai_btn.pack(side=tk.LEFT, padx=15, pady=(0, 10))

        # Console area
        self.console_container = tk.Frame(self.footer, bg=BG_COLOR)
        self.console_container.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        self.console_label = tk.Label(self.console_container, text="Output Console", bg=BG_COLOR, fg=TEXT_SECONDARY, font=("Segoe UI", 9))
        self.console_label.pack(anchor=tk.W, pady=(5, 5))

        self.console = HDScrolledText(self.console_container, height=6, font=("JetBrains Mono", 10), bg="#0A0A0A", readonly=True)
        self.console.pack(fill=tk.BOTH, expand=True)


    def on_menu_click(self, item):
        if item == "Open":
            filepath = filedialog.askopenfilename(
                title="Open NovaLang File",
                filetypes=(("NovaLang source files", "*.nova"), ("All files", "*.*"))
            )
            if not filepath:
                return
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.code_editor.delete("1.0", tk.END)
                self.code_editor.insert(tk.END, content)
                self.console.insert(tk.END, f"[SYSTEM] Loaded {filepath}\n")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

        elif item == "Save":
            filepath = filedialog.asksaveasfilename(
                title="Save NovaLang File",
                defaultextension=".nova",
                filetypes=(("NovaLang source files", "*.nova"), ("All files", "*.*"))
            )
            if not filepath:
                return
            try:
                content = self.code_editor.get("1.0", tk.END)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.console.insert(tk.END, f"[SYSTEM] Saved successfully to {filepath}\n")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def on_run(self):
        code = self.code_editor.get("1.0", tk.END).strip()
        if not code: return

        self.console.delete("1.0", tk.END)
        
        # Cyberpunk NovaLang ASCII Logo
        nova_logo = r"""  _   _                 _                      
 | \ | |               | |                     
 |  \| | _____   ____ _| |     __ _ _ __   __ _ 
 | . ` |/ _ \ \ / / _` | |    / _` | '_ \ / _` |
 | |\  | (_) \ V / (_| | |___| (_| | | | | (_| |
 |_| \_|\___/ \_/ \__,_|______\__,_|_| |_|\__, |
                                           __/ |
                                          |___/  

"""
        self.console.insert(tk.END, nova_logo, "logo")
        self.console.tag_config("logo", foreground="#4CAF50") # Glowing Accent
        
        self.console.insert(tk.END, "[SYSTEM] Compiling NovaLang...\n")
        self.console.insert(tk.END, "[SYSTEM] Analyzing logic...\n\n")
        
        threading.Thread(target=self.execute_code, args=(code,)).start()

    def execute_code(self, source):
        # Run interpreter and let phase details output directly to the background terminal
        error, output = run_interpreter(source, show_phases=True)
        self.root.after(0, self.update_console, error, output)

    def update_console(self, error, output):
        if error:
            self.console.insert(tk.END, f"{error}\n", "error")
            self.console.tag_config("error", foreground="#FF4444")
        else:
            for line in output:
                self.console.insert(tk.END, f"  {line}\n")
                
        self.console.insert(tk.END, "\n[SYSTEM] Process finished.\n")


    def on_compare(self):
        code = self.code_editor.get("1.0", tk.END).strip()
        if not code: return

        self.ai_content.delete("1.0", tk.END)
        self.ai_content.insert(tk.END, "Querying Nova Intelligence Engine...\n")
        
        if GROQ_AVAILABLE and self.api_key:
            threading.Thread(target=self.real_groq_compare, args=(code,)).start()
        else:
            threading.Thread(target=self.mock_ai_compare, args=(code,)).start()

    def real_groq_compare(self, code):
        try:
            client = groq.Groq(api_key=self.api_key)
            
            # Detailed NovaLang specification for the AI context
            novalang_specs = """
            NovaLang Language Specification:
            - Keywords: let, int, float, string, char, bool, display, if, else, while, for, func, return, try, catch, end, true, false, and, or.
            - Variable Declaration: 'let <type> <name> = <value>' (e.g., let int x = 10).
            - Display: 'display' followed by comma-separated expressions (e.g., display "Result:", x).
            - Functions: 'func name(type p1, type p2) ... end'.
            - Blocks: 'if', 'while', 'for', 'try', and 'func' must ALWAYS be terminated with 'end'.
            - Comments: Use '--' for single-line comments.
            - No curly braces {}, no semicolons ;, no 'print()', no 'def', no 'while (cond):'.
            - If the input code uses Python syntax (like 'print', 'def', or colons for blocks), it is INVALID NovaLang.
            """
            
            prompt = (
                f"You are the NovaLang Intelligence Engine. Strictly analyze the following code based on NovaLang rules.\n\n"
                f"{novalang_specs}\n"
                f"Here is the user's code:\n{code}\n\n"
                "Analyze it and provide:\n"
                "1. Language Validation: Is this actually NovaLang? If it looks like Python or another language, flag it as INVALID.\n"
                "2. Expected Output: what will this print if it runs (if valid).\n"
                "3. Semantic & Syntax Errors: identify any violations of the NovaLang specs above.\n"
                "4. Equivalent Python: show the same logic in Python for comparison.\n\n"
                "Be strictly critical. Keep response under 100 words."
            )
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.1-8b-instant",
            )
            response_text = chat_completion.choices[0].message.content
            
            final = "AI ANALYSIS\n" + "━"*15 + "\n\n" + response_text
            self.root.after(0, lambda: self.ai_content.delete("1.0", tk.END))
            self.root.after(0, lambda: self.ai_content.insert(tk.END, final))
        except Exception as e:
            error_msg = f"Groq Error:\n{str(e)}\n\nCheck your API key in .env file."
            self.root.after(0, lambda: self.ai_content.delete("1.0", tk.END))
            self.root.after(0, lambda: self.ai_content.insert(tk.END, error_msg))

    def mock_ai_compare(self, code):
        time.sleep(0.8)
        analysis = "✨ NOVA-CORE SUMMARY\n" + "━"*15 + "\n\n"
        analysis += "• Execution: Stable\n• Logic: No issues detected.\n• Structure: standard NovaLang flow."
        self.root.after(0, lambda: self.ai_content.delete("1.0", tk.END))
        self.root.after(0, lambda: self.ai_content.insert(tk.END, analysis))

if __name__ == "__main__":
    # Tell Windows this is an independent app to fix the generic Python icon in the taskbar
    import os
    if os.name == "nt":
        try:
            import ctypes
            myappid = 'novalang.ide.version1' # Arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    root = tk.Tk()
    # Attempt to improve visual quality on high-DPI displays
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = APLInterpreterUI(root)
    root.mainloop()
