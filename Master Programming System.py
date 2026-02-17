##################
# ---------- Ajustes ---------- #
debug_mode = True
auto_run_on_load = False
theme = "dracula"
font_size = 12
tab_size = 4
highlight_syntax = True
show_line_numbers = True
last_opened_file = None
##################

import tkinter as tk
from tkinter import filedialog, messagebox
import random, time, string

# ------------------------------
# Temas estilizados
# ------------------------------
THEMES = {
    "dark": {
        "bg": "#1e1e1e",
        "editor_bg": "#1e1e1e",
        "editor_fg": "#d4d4d4",
        "console_bg": "#111111",
        "console_fg": "#18ff43",
        "status_bg": "#252526",
        "status_fg": "#cccccc",
        "highlight": "#0abaff",
        "selection": "#264f78",
    },
    "light": {
        "bg": "#f5f5f5",
        "editor_bg": "#ffffff",
        "editor_fg": "#000000",
        "console_bg": "#eeeeee",
        "console_fg": "#333333",
        "status_bg": "#dddddd",
        "status_fg": "#000000",
        "highlight": "#0066cc",
        "selection": "#aaccee",
    },
    "dracula": {
        "bg": "#282a36",
        "editor_bg": "#282a36",
        "editor_fg": "#f8f8f2",
        "console_bg": "#21222c",
        "console_fg": "#50fa7b",
        "status_bg": "#44475a",
        "status_fg": "#f8f8f2",
        "highlight": "#ff79c6",
        "selection": "#44475a",
    },
    "solarized_dark": {
        "bg": "#002b36",
        "editor_bg": "#002b36",
        "editor_fg": "#839496",
        "console_bg": "#073642",
        "console_fg": "#b58900",
        "status_bg": "#073642",
        "status_fg": "#93a1a1",
        "highlight": "#268bd2",
        "selection": "#586e75",
    }
}

# ------------------------------
# Intérprete MPS
# ------------------------------
class MPSInterpreter:
    def __init__(self, output_callback):
        self.output = output_callback
        self.vars = {}
        self.extras = set()
        self._last_concat = ""
        self._last_result = ""

    def log(self, text):
        self.output(str(text))

    def run(self, code):
        self.vars = {}
        self._last_concat = ""
        self._last_result = ""
        lines = code.split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            self.process_line(line)

    def process_line(self, line):
        # ---------------- VARIABLES ----------------
        if line.startswith("var "):
            parts = line[4:].split("=", 1)
            name = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            self.vars[name] = value
            return

        # ---------------- WRITE.TEXT ----------------
        if line.startswith("write.text("):
            val = line[len("write.text("):-1].strip().strip('"')
            self.log(val)
            return

        # ---------------- WRITE.VAR ----------------
        if line.startswith("write.var("):
            name = line[len("write.var("):-1].strip()
            self.log(self.vars.get(name, f"[ERROR] var '{name}' no existe"))
            return

        # ---------------- CONCATENAR ----------------
        if line.startswith("concatenar.var("):
            args = line[len("concatenar.var("):-1].split(",")
            result = ""
            for a in args:
                a = a.strip()
                if a.startswith('"') and a.endswith('"'):
                    result += a[1:-1]
                else:
                    result += str(self.vars.get(a, f"[ERR:{a}]"))
            self._last_concat = result
            return

        if line.startswith("endwrite.var("):
            name = line[len("endwrite.var("):-1].strip()
            if name == "_last_concat":
                self.log(self._last_concat)
            else:
                self.log(self.vars.get(name, f"[ERROR] var '{name}' no existe"))
            return

        # ---------------- EXTRAS ----------------
        if line.startswith("extra.add("):
            name = line[len("extra.add("):-1].strip()
            self.extras.add(name)
            self.log(f"[Extra {name} cargado]")
            return
        if line.startswith("extra.remove("):
            name = line[len("extra.remove("):-1].strip()
            if name in self.extras:
                self.extras.remove(name)
            self.log(f"[Extra {name} removido]")
            return

        if "=" in line and line.split("=")[1].strip().startswith("["):
            name, arr = line.split("=")
            name = name.replace("var","").strip()
            arr = arr.strip()[1:-1].split(",")
            self.vars[name] = [a.strip() for a in arr]
            return

        if "." in line and "(" not in line:
            name, index = line.split(".")
            if name in self.vars and isinstance(self.vars[name], list):
                i = int(index)-1
                self.log(self.vars[name][i])
            return

        if "math" in self.extras:
            self.handle_math(line)
        if "rand" in self.extras:
            self.handle_rand(line)
        if "console" in self.extras:
            self.handle_console(line)

    def handle_math(self, line):
        try:
            if line.startswith("sumar("):
                a,b = line[6:-1].split(",")
                self._last_result = str(int(a)+int(b))
            elif line.startswith("restar("):
                a,b = line[7:-1].split(",")
                self._last_result = str(int(a)-int(b))
            elif line.startswith("multiplicar("):
                a,b = line[12:-1].split(",")
                self._last_result = str(int(a)*int(b))
            elif line.startswith("dividir("):
                a,b = line[8:-1].split(",")
                self._last_result = str(int(a)//int(b))
        except:
            self.log("[ERROR] math operation")

    def handle_rand(self, line):
        if line.startswith("rand.number("):
            a,b = line[12:-1].split(",")
            self._last_result = str(random.randint(int(a),int(b)))
        elif line=="rand.boolean()":
            self._last_result = str(random.choice([True,False]))
        elif line.startswith("rand.string("):
            n=int(line[12:-1])
            self._last_result = "".join(random.choice(string.ascii_lowercase) for _ in range(n))

    def handle_console(self, line):
        if line=="console.limpiar()":
            self.log("[console cleared]")
        elif line.startswith("console.sleep("):
            t=float(line[14:-1])
            self.log(f"[sleep {t}s]")
            time.sleep(t)

# ------------------------------
# Master Programming System v2.24 — UI
# ------------------------------
class MPSIDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Master Programming System v2.24")
        self.geometry("950x650")
        self.current_theme = theme
        self.configure(bg=THEMES[self.current_theme]["bg"])

        self.interpreter = MPSInterpreter(self.console_output)

        # Frames
        self.sidebar = tk.Frame(self, width=140, bg=THEMES[self.current_theme]["status_bg"])
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.main_area = tk.Frame(self, bg=THEMES[self.current_theme]["bg"])
        self.main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Editor
        self.editor = tk.Text(self.main_area,
                              bg=THEMES[self.current_theme]["editor_bg"],
                              fg=THEMES[self.current_theme]["editor_fg"],
                              insertbackground=THEMES[self.current_theme]["editor_fg"],
                              font=("Consolas", font_size))
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.editor.bind("<<Modified>>", self.resaltar_sintaxis)
        self.editor.bind("<KeyRelease>", self.resaltar_linea_actual)

        # Consola
        self.console = tk.Text(self.main_area,
                               height=14,
                               bg=THEMES[self.current_theme]["console_bg"],
                               fg=THEMES[self.current_theme]["console_fg"],
                               font=("Consolas", font_size),
                               state=tk.DISABLED)
        self.console.pack(fill=tk.X)

        # Sidebar botones en orden
        for t,c in [("📝 Nuevo",self.nuevo_archivo),
                    ("📄 Abrir",self.abrir),
                    ("💾 Guardar",self.guardar),
                    ("▶️ Ejecutar",self.ejecutar),
                    ("🎨 Tema",self.tema_menu),
                    ("📚 Demos",self.demos_menu),
                    ("❓ Ayuda",self.ayuda)]:
            self.add_sidebar_button(t,c)

        # Atajos
        self.bind("<Control-e>", lambda e: self.ejecutar())
        self.bind("<Control-s>", lambda e: self.guardar())
        self.bind("<Control-o>", lambda e: self.abrir())
        self.bind("<Control-h>", lambda e: self.ayuda())
        self.bind("<Control-n>", lambda e: self.nuevo_archivo())

    # ------------------------------ Helpers ------------------------------
    def add_sidebar_button(self, text, command):
        btn = tk.Button(self.sidebar, text=text, bg=THEMES[self.current_theme]["status_bg"],
                        fg=THEMES[self.current_theme]["status_fg"], relief=tk.FLAT, command=command)
        btn.pack(fill=tk.X, padx=5, pady=4)
        btn.bind("<Enter>", lambda e,b=btn: b.config(bg="#555555"))
        btn.bind("<Leave>", lambda e,b=btn: b.config(bg=THEMES[self.current_theme]["status_bg"]))

    def console_output(self, text):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, str(text)+"\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    # ------------------------------ Ejecutar/Archivo ------------------------------
    def ejecutar(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)
        code = self.editor.get(1.0, tk.END)
        self.interpreter.run(code)
        self.resaltar_sintaxis()

    def guardar(self):
        path = filedialog.asksaveasfilename(defaultextension=".mps", filetypes=[("MPS Files","*.mps")])
        if path:
            with open(path,"w",encoding="utf-8") as f:
                f.write(self.editor.get(1.0, tk.END))

    def abrir(self):
        path = filedialog.askopenfilename(filetypes=[("MPS Files","*.mps")])
        if path:
            global last_opened_file
            last_opened_file = path
            with open(path,"r",encoding="utf-8") as f:
                self.editor.delete(1.0, tk.END)
                self.editor.insert(tk.END, f.read())
            if auto_run_on_load:
                self.ejecutar()

    def nuevo_archivo(self):
        self.editor.delete(1.0, tk.END)
        self.console_output("[Nuevo archivo]")

    # ------------------------------ Ayuda ------------------------------
    def ayuda(self):
        messagebox.showinfo("Ayuda Master Programming System v2.24",
            "Comandos MPS:\n"
            "- var nombre = valor\n"
            "- write.text(...), write.var(...)\n"
            "- concatenar.var(...), endwrite.var(...)\n"
            "- Extras: math, rand, console, utils, repetir, invertir, text\n"
            "- Listas 1-indexadas\n\n"
            "Atajos:\n"
            "Ctrl+E = Ejecutar\nCtrl+S = Guardar\nCtrl+O = Abrir\nCtrl+H = Ayuda\nCtrl+N = Nuevo archivo"
        )

    # ------------------------------ Resaltado ------------------------------
    def resaltar_sintaxis(self, event=None):
        keywords = ["var","write.text","write.var","concatenar.var","endwrite.var","extra.add","extra.remove"]
        self.editor.tag_remove("keyword","1.0",tk.END)
        for kw in keywords:
            start="1.0"
            while True:
                pos=self.editor.search(kw,start,stopindex=tk.END)
                if not pos: break
                end=f"{pos}+{len(kw)}c"
                self.editor.tag_add("keyword",pos,end)
                start=end
        self.editor.tag_config("keyword",foreground=THEMES[self.current_theme]["highlight"])

    def resaltar_linea_actual(self, event=None):
        self.editor.tag_remove("current_line","1.0",tk.END)
        index=self.editor.index("insert linestart")
        self.editor.tag_add("current_line",index,f"{index} lineend")
        self.editor.tag_configure("current_line",background=THEMES[self.current_theme]["selection"])

    # ------------------------------ Menus ------------------------------
    def tema_menu(self):
        win = tk.Toplevel(self)
        win.title("Cambiar Tema")
        win.geometry("200x180")
        for t in THEMES.keys():
            tk.Button(win,text=t,command=lambda x=t:self.cambiar_tema(x)).pack(pady=2)

    def cambiar_tema(self,tema):
        if tema in THEMES:
            self.current_theme=tema
            th=THEMES[tema]
            self.configure(bg=th["bg"])
            self.editor.configure(bg=th["editor_bg"],fg=th["editor_fg"],insertbackground=th["editor_fg"])
            self.console.configure(bg=th["console_bg"],fg=th["console_fg"])
            self.sidebar.configure(bg=th["status_bg"])
            for widget in self.sidebar.winfo_children():
                widget.configure(bg=th["status_bg"],fg=th["status_fg"])

    def demos_menu(self):
        demos = [
            ("Demo 1 : Hello World","write.text(\"Hello World\")"),
            ("Demo 2 : Variables","var demo = \"Hola\""),
            ("Demo 3 : Concatenar","concatenar.var(demo,\" Mundo\")"),
            ("Demo 4 : Extra Mates","extra.add(math)\nsumar(2,3)"),
            ("Demo 5 : Extra Random","extra.add(rand)\nrand.number(0,10)")
        ]
        win = tk.Toplevel(self)
        win.title("Demos")
        win.geometry("250x300")
        tk.Label(win,text="Cargar demo (sobrescribe código actual)").pack()
        for n, code in demos:
            tk.Button(win,text=n,command=lambda x=code:self.cargar_demo(x)).pack(pady=2)

    def cargar_demo(self, code):
        resp = messagebox.askyesno("ADVERTENCIA","Al importar una demo, se borrará el código actual. ¿Estás seguro?")
        if resp:
            self.editor.delete(1.0, tk.END)
            self.editor.insert(tk.END, code+"\n")
            self.console_output("[Demo cargada]")

# ------------------------------
# RUN
# ------------------------------
if __name__=="__main__":
    app=MPSIDE()
    app.mainloop()
