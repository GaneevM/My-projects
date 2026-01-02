import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import re

def translate_function(func):
    func = func.replace('^', '**')
    func = re.sub(r'\b(sin|cos|tan|exp|log|sqrt)\b', r'np.\1', func)
    func = re.sub(r'(\d)(x)', r'\1*\2', func)
    func = re.sub(r'(x)(\d)', r'\1*\2', func)
    func = re.sub(r'(\d|x)(np\.\w+\()', r'\1*\2', func)
    func = re.sub(r'(\d|\))\(', r'\1*(', func)
    func = re.sub(r'\)(\d|x)', r')*\1', func)
    return func

class GraphingCalc:
    def __init__(self, root):
        self.root = root
        self.root.title("Ganeev's graphing calculator")
        self.root.geometry("1100x700") 

        self.saved_graphs = []
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tk.LabelFrame(self.main_frame, text="Functions", width=250, padx=5, pady=5)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.plot_container = tk.Frame(self.main_frame)
        self.plot_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.controls = tk.Frame(self.plot_container)
        self.controls.pack(side=tk.TOP, fill=tk.X)

        self.entry_func = tk.Entry(self.controls, width=30, font=("Arial", 16))
        self.entry_func.grid(row=0, column=0, columnspan=5, padx=5, pady=5)
        self.entry_func.bind('<Return>', lambda e: self.add_graph())

        tk.Label(self.controls, text="x min:").grid(row=1, column=0)
        self.entry_min = tk.Entry(self.controls, width=5)
        self.entry_min.grid(row=1, column=1)
        self.entry_min.insert(0, "-10")

        tk.Label(self.controls, text="x max:").grid(row=1, column=2)
        self.entry_max = tk.Entry(self.controls, width=5)
        self.entry_max.grid(row=1, column=3)
        self.entry_max.insert(0, "10")

        tk.Button(self.controls, text="Add Graph", width=10, command=self.add_graph).grid(row=1, column=4, padx=5)

        self.calc_frame = tk.Frame(self.controls)
        self.calc_frame.grid(row=2, column=0, columnspan=5)
        self.setup_buttons()

        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_container)
        self.toolbar.update()

    def setup_buttons(self):
        buttons = [
            ['7','8','9','/','('],
            ['4','5','6','*',')'],
            ['1','2','3','-','^'],
            ['0','.','+','sin','cos'],
            ['tan','exp','log','sqrt','C'],
            ['x']
        ]
        for r, row in enumerate(buttons):
            for c, char in enumerate(row):
                if char == 'C':
                    tk.Button(self.calc_frame, text=char, width=5, height=1, command=self.clear).grid(row=r, column=c)
                else:
                    tk.Button(self.calc_frame, text=char, width=5, height=1, command=lambda ch=char: self.press(ch)).grid(row=r, column=c)

    def press(self, key):
        self.entry_func.insert(tk.END, key)

    def clear(self):
        self.entry_func.delete(0, tk.END)

    def add_graph(self):
        expr = self.entry_func.get()
        if not expr: return
        
        try:
            test_x = 1.0
            test_func = translate_function(expr)
            eval(test_func, {"x": test_x, "np": np})
        except Exception:
            messagebox.showerror("Parsing Error", "Could not understand input.\nPlease fix input.")
            return

        color = self.colors[len(self.saved_graphs) % len(self.colors)]
        visible_var = tk.BooleanVar(value=True)
        
        chk = tk.Checkbutton(self.sidebar, text=f"y = {expr}", variable=visible_var, 
                             fg=color, font=("Arial", 10, "bold"), command=self.update_plot)
        chk.pack(anchor='w')
        
        self.saved_graphs.append({"expr": expr, "visible": visible_var, "color": color})
        self.update_plot()
        self.clear()

    def update_plot(self):
        self.ax.clear()
        try:
            x_min = float(self.entry_min.get())
            x_max = float(self.entry_max.get())
        except ValueError:
            x_min, x_max = -10, 10
            
        x = np.linspace(x_min, x_max, 2000)

        self.fig.texts = [] 
        self.fig.text(0.5, 0.5, "Ganeev's graphing calc", 
                 fontsize=35, color='gray', ha='center', va='center', 
                 alpha=0.15, fontname='Albemarle Swash', family='cursive', zorder=0)

        for graph in self.saved_graphs:
            if graph["visible"].get():
                try:
                    func_translated = translate_function(graph["expr"])
                    y = eval(func_translated, {"x": x, "np": np})
                    y = np.where(np.abs(y) > 20, np.nan, y)
                    self.ax.plot(x, y, label=f"y={graph['expr']}", color=graph['color'], linewidth=2)
                except Exception:
                    pass

        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        if self.saved_graphs:
            self.ax.legend()
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphingCalc(root)
    root.mainloop()
