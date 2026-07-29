import tkinter as tk
from tkinter import ttk


class CortexDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Cortex Backtesting Engine")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        # Main Container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # header panel
        self.header_frame = ttk.LabelFrame(self.main_container)
        self.header_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        self.title_label = ttk.Label(
            self.header_frame,
            text="CORTEX ENGINE",
            font=("Helvetica", 16, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=10, pady=10)


        # sidebar and workspace area
        self.body_frame = ttk.Frame(self.main_container)
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        # left sidebar
        self.sidebar_frame = ttk.LabelFrame(self.body_frame, text=" Configuration & Controls ")
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # ticker controls
        self.asset_label = ttk.Label(self.sidebar_frame, text="Select Symbol:")
        self.asset_label.pack(anchor=tk.W, padx=10, pady=(10, 2))

        self.asset_combo = ttk.Combobox(
            self.sidebar_frame,
            values=["AAPL", "MSFT", "GOOGL", "NVDA", "SPY", "AMZN"]
        )
        self.asset_combo.set("AAPL")
        self.asset_combo.pack(fill=tk.X, padx=10, pady=(0, 10))

        # date
        self.start_date_label = ttk.Label(self.sidebar_frame, text="Start Date (YYYY-MM-DD):")
        self.start_date_label.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.start_date_entry = ttk.Entry(self.sidebar_frame)
        self.start_date_entry.insert(0, "2024-12-11")
        self.start_date_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.end_date_label = ttk.Label(self.sidebar_frame, text="End Date (YYYY-MM-DD):")
        self.end_date_label.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.end_date_entry = ttk.Entry(self.sidebar_frame)
        self.end_date_entry.insert(0, "2026-07-23")
        self.end_date_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.separator_1 = ttk.Separator(self.sidebar_frame, orient="horizontal")
        self.separator_1.pack(fill=tk.X, padx=10, pady=10)

        # strategy selection
        self.strategy_label = ttk.Label(self.sidebar_frame, text="Strategy Module:")
        self.strategy_label.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.strategy_combo = ttk.Combobox(
            self.sidebar_frame,
            values=["SMA Crossover", "RSI Mean Reversion", "EMA Stochastic Filter"]
        )
        self.strategy_combo.set("SMA Crossover")
        self.strategy_combo.pack(fill=tk.X, padx=10, pady=(0, 10))

        # parameter sliders
        self.p1_label = ttk.Label(self.sidebar_frame, text="Fast Period (5 - 50):")
        self.p1_label.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.p1_scale = ttk.Scale(self.sidebar_frame, from_=5, to=50, orient=tk.HORIZONTAL)
        self.p1_scale.set(20)
        self.p1_scale.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.p2_label = ttk.Label(self.sidebar_frame, text="Slow Period (20 - 200):")
        self.p2_label.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.p2_scale = ttk.Scale(self.sidebar_frame, from_=20, to=200, orient=tk.HORIZONTAL)
        self.p2_scale.set(50)
        self.p2_scale.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.separator_2 = ttk.Separator(self.sidebar_frame, orient="horizontal")
        self.separator_2.pack(fill=tk.X, padx=10, pady=10)

        # capital & commission inputs
        self.capital_label = ttk.Label(self.sidebar_frame, text="Initial Capital ($):")
        self.capital_label.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.capital_entry = ttk.Entry(self.sidebar_frame)
        self.capital_entry.insert(0, "100000.0")
        self.capital_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.commission_label = ttk.Label(self.sidebar_frame, text="Commission Rate (%):")
        self.commission_label.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.commission_entry = ttk.Entry(self.sidebar_frame)
        self.commission_entry.insert(0, "0.1")
        self.commission_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.slippage_label = ttk.Label(self.sidebar_frame, text="Slippage Rate (%):")
        self.slippage_label.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.slippage_entry = ttk.Entry(self.sidebar_frame)
        self.slippage_entry.insert(0, "0.05")
        self.slippage_entry.pack(fill=tk.X, padx=10, pady=(0, 15))

        # action buttons
        self.run_button = ttk.Button(self.sidebar_frame, text="Execute Backtest", command=self.execute_backtest)
        self.run_button.pack(fill=tk.X, padx=10, pady=(5, 10))

        self.reset_button = ttk.Button(self.sidebar_frame, text="Reset Defaults", command=self.reset_defaults)
        self.reset_button.pack(fill=tk.X, padx=10, pady=(0, 10))

        # right workspace
        self.workspace_frame = ttk.Frame(self.body_frame)
        self.workspace_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # metrics
        self.metrics_frame = ttk.LabelFrame(self.workspace_frame, text=" Performance Indicators ")
        self.metrics_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        self.m1_frame = ttk.Frame(self.metrics_frame, relief=tk.GROOVE, borderwidth=1)
        self.m1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(self.m1_frame, text="Total Return", font=("Helvetica", 9)).pack(pady=(5, 0))
        ttk.Label(self.m1_frame, text="--.--%", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        self.m2_frame = ttk.Frame(self.metrics_frame, relief=tk.GROOVE, borderwidth=1)
        self.m2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(self.m2_frame, text="Final Equity", font=("Helvetica", 9)).pack(pady=(5, 0))
        ttk.Label(self.m2_frame, text="$---,---.--", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        self.m3_frame = ttk.Frame(self.metrics_frame, relief=tk.GROOVE, borderwidth=1)
        self.m3_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(self.m3_frame, text="Sharpe Ratio", font=("Helvetica", 9)).pack(pady=(5, 0))
        ttk.Label(self.m3_frame, text="-.--", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        self.m4_frame = ttk.Frame(self.metrics_frame, relief=tk.GROOVE, borderwidth=1)
        self.m4_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(self.m4_frame, text="Max Drawdown", font=("Helvetica", 9)).pack(pady=(5, 0))
        ttk.Label(self.m4_frame, text="--.--%", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        self.m5_frame = ttk.Frame(self.metrics_frame, relief=tk.GROOVE, borderwidth=1)
        self.m5_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(self.m5_frame, text="Win Rate", font=("Helvetica", 9)).pack(pady=(5, 0))
        ttk.Label(self.m5_frame, text="--.--%", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))

        # tabs
        self.notebook = ttk.Notebook(self.workspace_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # chart view (currently placeholder)
        self.tab_charts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_charts, text=" Equity Curve & Drawdown ")

        self.canvas_placeholder = tk.Canvas(self.tab_charts, bg="#ffffff", borderwidth=1, relief=tk.SUNKEN)
        self.canvas_placeholder.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas_placeholder.create_text(
            300, 200,
            text="matplotlib render goes into here",
            font=("Helvetica", 12),
            fill="#888888"
        )

        # trade execution log
        self.tab_trades = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_trades, text=" Executed Trades Log ")

        self.tree_columns = ("Trade ID", "Entry Date", "Exit Date", "Type", "Entry Price", "Exit Price", "PnL ($)", "Return (%)")
        self.trade_tree = ttk.Treeview(self.tab_trades, columns=self.tree_columns, show="headings")

        for col in self.tree_columns:
            self.trade_tree.heading(col, text=col)
            self.trade_tree.column(col, width=90, anchor=tk.CENTER)

        self.tree_scroll = ttk.Scrollbar(self.tab_trades, orient=tk.VERTICAL, command=self.trade_tree.yview)
        self.trade_tree.configure(yscrollcommand=self.tree_scroll.set)

        self.trade_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

    def execute_backtest(self) -> None:
        print("executing backtest")

    def reset_defaults(self) -> None:
        self.asset_combo.set("AAPL")
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, "2024-12-11")
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, "2026-07-23")
        self.strategy_combo.set("SMA Crossover")
        self.p1_scale.set(20)
        self.p2_scale.set(50)
        self.capital_entry.delete(0, tk.END)
        self.capital_entry.insert(0, "100000.0")
        self.commission_entry.delete(0, tk.END)
        self.commission_entry.insert(0, "0.1")
        self.slippage_entry.delete(0, tk.END)
        self.slippage_entry.insert(0, "0.05")
        self.log_text.insert(tk.END, "[RESET] Default values restored.\n")
        self.log_text.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    CortexDesktopApp(root)
    root.mainloop()
