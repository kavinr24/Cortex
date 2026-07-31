import math
import random
import tkinter as tk
from tkinter import ttk


class CortexDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Cortex Backtesting Engine")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 680)


        self._setup_styles()

        self.main_container = ttk.Frame(self.root, style="Main.TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.sidebar_visible = True
        self.current_theme = "dark"
        self.active_timeframe = tk.StringVar(value="1D")
        self.execution_mode = tk.StringVar(value="Spot")

        self.header_frame = ttk.LabelFrame(
            self.main_container,
            text="",
            style="Dark.TLabelframe",
        )
        self.header_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        self._build_header()
        self._build_body()
        self._build_statusbar()

        self.root.after(100, self._draw_mock_chart)

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.bg_dark = "#121212"
        self.bg_panel = "#1e1e1e"
        self.bg_card = "#252526"
        self.fg_main = "#e0e0e0"
        self.accent_green = "#00e676"
        self.accent_red = "#ff5252"
        self.accent_cyan = "#00e5ff"

        self.root.configure(bg=self.bg_dark)

        self.style.configure("Main.TFrame", background=self.bg_dark)
        self.style.configure("Panel.TFrame", background=self.bg_panel)
        self.style.configure("CardFrame", background=self.bg_card, relief="flat")

        self.style.configure(
            "Dark.TLabelframe",
            background=self.bg_panel,
            foreground=self.fg_main,
            bordercolor="#333333",
            relief="solid"
        )
        self.style.configure(
            "Dark.TLabelframe.Label",
            background=self.bg_panel,
            foreground=self.accent_cyan,
            font=("Helvetica", 9, "bold")
        )

        self.style.configure("TLabel", background=self.bg_panel, foreground=self.fg_main, font=("Helvetica", 9))
        self.style.configure("HeaderTitle.TLabel", background=self.bg_panel, foreground="#ffffff", font=("Helvetica", 14, "bold"))
        self.style.configure("CardTitle.TLabel", background=self.bg_card, foreground="#a0a0a0", font=("Helvetica", 8))
        self.style.configure("CardVal.TLabel", background=self.bg_card, foreground=self.accent_green, font=("Helvetica", 11, "bold"))
        self.style.configure("Accent.TButton", font=("Helvetica", 9, "bold"), background="#0080ff", foreground="#ffffff")
        self.style.configure("Action.TButton", font=("Helvetica", 8))

        self.style.configure("TNotebook", background=self.bg_panel, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.bg_card, foreground=self.fg_main, padding=[10, 5], font=("Helvetica", 9))
        self.style.map("TNotebook.Tab", background=[("selected", self.bg_dark)], foreground=[("selected", self.accent_cyan)])

    def _build_header(self):

        title_box = ttk.Frame(self.header_frame, style="Panel.TFrame")
        title_box.pack(side=tk.LEFT, padx=12, pady=8)

        ttk.Label(title_box, text="CORTEX ENGINE", style="HeaderTitle.TLabel").pack(anchor=tk.W)

        controls_box = ttk.Frame(self.header_frame, style="Panel.TFrame")
        controls_box.pack(side=tk.RIGHT, padx=12, pady=8)

        self.sidebar_toggle_btn = ttk.Button(
            controls_box,
            text="Toggle Controls",
            style="Action.TButton",
            command=self._toggle_sidebar
        )
        self.sidebar_toggle_btn.pack(side=tk.RIGHT, padx=5)

        self.chart_redraw_btn = ttk.Button(
            controls_box,
            text="Regenerate Graph",
            style="Action.TButton",
            command=self._draw_mock_chart
        )
        self.chart_redraw_btn.pack(side=tk.RIGHT, padx=5)

        opts_box = ttk.Frame(self.header_frame, style="Panel.TFrame")
        opts_box.pack(side=tk.RIGHT, padx=20, pady=8)

        ttk.Label(opts_box, text="Timeframe:").pack(side=tk.LEFT, padx=(0, 4))
        tf_combo = ttk.Combobox(
            opts_box,
            textvariable=self.active_timeframe,
            values=["15M", "1H", "4H", "1D", "1W"],
            width=5,
            state="readonly"
        )
        tf_combo.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(opts_box, text="Execution Mode:").pack(side=tk.LEFT, padx=(0, 4))
        mode_combo = ttk.Combobox(
            opts_box,
            textvariable=self.execution_mode,
            values=["Spot", "Margin (10x)", "Paper Simulated"],
            width=14,
            state="readonly"
        )
        mode_combo.pack(side=tk.LEFT)

    def _build_body(self):
        self.body_frame = ttk.Frame(self.main_container, style="Main.TFrame")
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_workspace()

    def _build_sidebar(self):
        self.sidebar_frame = ttk.LabelFrame(self.body_frame, text=" Configuration ", style="Dark.TLabelframe")
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.side_canvas = tk.Canvas(self.sidebar_frame, bg=self.bg_panel, highlightthickness=0, width=280)
        self.side_scrollbar = ttk.Scrollbar(self.sidebar_frame, orient=tk.VERTICAL, command=self.side_canvas.yview)

        self.scroll_sidebar_content = ttk.Frame(self.side_canvas, style="Panel.TFrame")
        self.scroll_sidebar_content.bind(
            "<Configure>",
            lambda e: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))
        )

        self.side_canvas.create_window((0, 0), window=self.scroll_sidebar_content, anchor="nw")
        self.side_canvas.configure(yscrollcommand=self.side_scrollbar.set)

        self.side_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.side_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        c = self.scroll_sidebar_content

        ttk.Label(c, text="DATE & SYMBOL", font=("Helvetica", 8, "bold"), foreground=self.accent_cyan).pack(anchor=tk.W, padx=10, pady=(10, 4))

        ttk.Label(c, text="Target Symbol:").pack(anchor=tk.W, padx=10, pady=(2, 2))
        self.asset_combo = ttk.Combobox(c, values=["NVDA", "AAPL", "MSFT", "AMD", "BTC-USD", "ETH-USD"], state="readonly")
        self.asset_combo.set("NVDA")
        self.asset_combo.pack(fill=tk.X, padx=10, pady=(0, 6))

        ttk.Label(c, text="Start Date:").pack(anchor=tk.W, padx=10, pady=(2, 2))
        self.start_date_entry = ttk.Entry(c)
        self.start_date_entry.insert(0, "2024-12-11")
        self.start_date_entry.pack(fill=tk.X, padx=10, pady=(0, 6))

        ttk.Label(c, text="End Date:").pack(anchor=tk.W, padx=10, pady=(2, 2))
        self.end_date_entry = ttk.Entry(c)
        self.end_date_entry.insert(0, "2026-07-23")
        self.end_date_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Separator(c, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(c, text="STRATEGY", font=("Helvetica", 8, "bold"), foreground=self.accent_cyan).pack(anchor=tk.W, padx=10, pady=(5, 4))

        self.strategy_combo = ttk.Combobox(c, values=["EMA Trend + Stochastic Filter", "SMA Crossover", "RSI Mean Reversion", "Bollinger Breakout"], state="readonly")
        self.strategy_combo.set("EMA Trend + Stochastic Filter")
        self.strategy_combo.pack(fill=tk.X, padx=10, pady=(0, 8))

        # MAP
        self.fast_lbl_frame = ttk.Frame(c, style="Panel.TFrame")
        self.fast_lbl_frame.pack(fill=tk.X, padx=10, pady=(4, 0))
        ttk.Label(self.fast_lbl_frame, text="Fast EMA Period:").pack(side=tk.LEFT)
        self.fast_val_label = ttk.Label(self.fast_lbl_frame, text="20", font=("Helvetica", 9, "bold"), foreground=self.accent_green)
        self.fast_val_label.pack(side=tk.RIGHT)

        self.fast_scale = ttk.Scale(c, from_=5, to=50, orient=tk.HORIZONTAL, command=lambda v: self.fast_val_label.config(text=str(int(float(v)))))
        self.fast_scale.set(20)
        self.fast_scale.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.slow_lbl_frame = ttk.Frame(c, style="Panel.TFrame")
        self.slow_lbl_frame.pack(fill=tk.X, padx=10, pady=(4, 0))
        ttk.Label(self.slow_lbl_frame, text="Slow EMA Period:").pack(side=tk.LEFT)
        self.slow_val_label = ttk.Label(self.slow_lbl_frame, text="50", font=("Helvetica", 9, "bold"), foreground=self.accent_green)
        self.slow_val_label.pack(side=tk.RIGHT)

        self.slow_scale = ttk.Scale(c, from_=20, to=200, orient=tk.HORIZONTAL, command=lambda v: self.slow_val_label.config(text=str(int(float(v)))))
        self.slow_scale.set(50)
        self.slow_scale.pack(fill=tk.X, padx=10, pady=(0, 8))

    def _build_workspace(self):
        # build right side workspace
        pass

    def _build_statusbar(self):
        # build bottom status bar
        pass

    def _toggle_sidebar(self):
        # sidebar visitbklity toggle
        pass

    def _draw_mock_chart(self):
        # redraw chart with mock data
        pass

    def execute_backtest(self):
        # execute full pipeline
        pass

    def reset_defaults(self):
        # reset all inputs to default values
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = CortexDesktopApp(root)
    root.mainloop()
