import tkinter as tk
from tkinter import ttk

root = tk.Tk()

# tk button
tk_btn = tk.Button(root, text="Classic Button")
tk_btn.pack()

# ttk button
ttk_btn = ttk.Button(root, text="Themed Button")
ttk_btn.pack()

root.mainloop()
