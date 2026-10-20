import csv
import calendar
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class BudgetApp:
    EXPENSE_CATEGORIES = ["식비", "교통", "취미", "기타"]
    INCOME_CATEGORIES = ["용돈", "월급"]
    TYPES = ["지출", "수입"]

    def __init__(self, root):
        self.root = root
        self.root.title("하루결산 | 가계부 & 소비 분석")
        self.root.geometry("1180x780")
        self.root.minsize(760, 650)
        self.root.configure(bg="#f4f6f8")
        self.records = []
        self.next_id = 1
        today = datetime.now()
        self.calendar_year = today.year
        self.calendar_month = today.month
        self.selected_calendar_date = today.strftime("%Y-%m-%d")
        self.calendar_cells = {}
        self.compact_layout = None

        self.setup_style()
        self.build_header()
        self.build_input_panel()
        self.build_filter_panel()
        self.build_content()
        self.root.bind("<Configure>", self.handle_resize)
        self.update_view()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6f8")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f4f6f8", foreground="#24313d", font=("맑은 고딕", 10))
        style.configure("Title.TLabel", background="#f4f6f8", foreground="#17232e", font=("맑은 고딕", 24, "bold"))
        style.configure("SubTitle.TLabel", background="#f4f6f8", foreground="#697783", font=("맑은 고딕", 10))
        style.configure("Section.TLabel", background="#ffffff", foreground="#17232e", font=("맑은 고딕", 12, "bold"))
        style.configure("CardValue.TLabel", background="#ffffff", foreground="#17232e", font=("맑은 고딕", 18, "bold"))
        style.configure("TButton", font=("맑은 고딕", 10), padding=(12, 7))
        style.configure("Accent.TButton", background="#1f7a6b", foreground="#ffffff", borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#176355")])
        style.configure("Treeview", rowheight=31, font=("맑은 고딕", 10), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("맑은 고딕", 10, "bold"), background="#e9eef0", foreground="#34444f")
        style.map("Treeview", background=[("selected", "#d9eee9")], foreground=[("selected", "#17232e")])
        style.configure("TCombobox", padding=5)
        style.configure("TEntry", padding=5)

    def build_header(self):
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=28, pady=(24, 10))
        ttk.Label(header, text="하루결산", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="날짜와 숫자로 보는 나의 소비 습관", style="SubTitle.TLabel").pack(side="left", padx=(14, 0), pady=(9, 0))
        actions = ttk.Frame(header)
        actions.pack(side="right")
        ttk.Button(actions, text="CSV 불러오기", command=self.load_csv).pack(side="left", padx=4)
        ttk.Button(actions, text="CSV 저장", command=self.save_csv).pack(side="left", padx=4)

    def build_input_panel(self):
        panel = ttk.Frame(self.root, style="Card.TFrame", padding=18)
        panel.pack(fill="x", padx=28, pady=8)
        ttk.Label(panel, text="새 내역 기록", style="Section.TLabel").grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 12))

        ttk.Label(panel, text="날짜 (YYYY-MM-DD)", background="#ffffff").grid(row=1, column=0, sticky="w")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(panel, textvariable=self.date_var, width=17)
        self.date_entry.grid(row=2, column=0, padx=(0, 14), pady=(5, 0), sticky="w")

        ttk.Label(panel, text="구분", background="#ffffff").grid(row=1, column=1, sticky="w")
        self.type_var = tk.StringVar(value="지출")
        self.type_combo = ttk.Combobox(panel, textvariable=self.type_var, values=self.TYPES, state="readonly", width=10)
        self.type_combo.grid(row=2, column=1, padx=(0, 14), pady=(5, 0), sticky="w")
        self.type_combo.bind("<<ComboboxSelected>>", self.update_category_options)

        ttk.Label(panel, text="카테고리", background="#ffffff").grid(row=1, column=2, sticky="w")
        self.category_var = tk.StringVar(value=self.EXPENSE_CATEGORIES[0])
        self.category_combo = ttk.Combobox(panel, textvariable=self.category_var, state="readonly", width=13)
        self.category_combo.grid(row=2, column=2, padx=(0, 14), pady=(5, 0), sticky="w")
        self.update_category_options()

        ttk.Label(panel, text="내용", background="#ffffff").grid(row=1, column=3, sticky="w")
        self.memo_var = tk.StringVar()
        self.memo_entry = ttk.Entry(panel, textvariable=self.memo_var, width=28)
        self.memo_entry.grid(row=2, column=3, padx=(0, 14), pady=(5, 0), sticky="ew")

        ttk.Label(panel, text="금액 (원)", background="#ffffff").grid(row=1, column=4, sticky="w")
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(panel, textvariable=self.amount_var, width=16)
        self.amount_entry.grid(row=2, column=4, padx=(0, 14), pady=(5, 0), sticky="w")
        self.amount_entry.bind("<Return>", lambda _event: self.add_record())

        ttk.Button(panel, text="+ 내역 추가", style="Accent.TButton", command=self.add_record).grid(row=2, column=5, padx=(4, 0), pady=(5, 0))
        panel.columnconfigure(3, weight=1)

    def update_category_options(self, _event=None):
        categories = self.EXPENSE_CATEGORIES if self.type_var.get() == "지출" else self.INCOME_CATEGORIES
        self.category_combo.configure(values=categories)
        if self.category_var.get() not in categories:
            self.category_var.set(categories[0])

    def build_filter_panel(self):
        panel = ttk.Frame(self.root, style="Card.TFrame", padding=(18, 12))
        panel.pack(fill="x", padx=28, pady=8)
        ttk.Label(panel, text="분석 범위", style="Section.TLabel").pack(side="left", padx=(0, 18))
        ttk.Label(panel, text="시작일", background="#ffffff").pack(side="left")
        self.start_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.start_var, width=13).pack(side="left", padx=(6, 14))
        ttk.Label(panel, text="종료일", background="#ffffff").pack(side="left")
        self.end_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.end_var, width=13).pack(side="left", padx=(6, 14))
        ttk.Label(panel, text="월별 보기", background="#ffffff").pack(side="left")
        self.month_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.month_var, width=10).pack(side="left", padx=(6, 14))
        ttk.Button(panel, text="필터 적용", command=self.update_view).pack(side="left", padx=3)
        ttk.Button(panel, text="전체 보기", command=self.clear_filters).pack(side="left", padx=3)
        ttk.Label(panel, text="그래프", background="#ffffff").pack(side="right", padx=(12, 5))
        self.chart_var = tk.StringVar(value="일별 지출")
        chart_menu = ttk.Combobox(panel, textvariable=self.chart_var, values=["일별 지출", "카테고리별 지출"], state="readonly", width=15)
        chart_menu.pack(side="right")
        chart_menu.bind("<<ComboboxSelected>>", lambda _event: self.draw_chart())

    def build_content(self):
        content = ttk.Frame(self.root)
        content.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        left = ttk.Frame(content, style="Card.TFrame", padding=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = ttk.Frame(content, style="Card.TFrame", padding=16)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        calendar_header = ttk.Frame(left, style="Card.TFrame")
        calendar_header.pack(fill="x", pady=(0, 8))
        ttk.Label(calendar_header, text="월별 거래 내역", style="Section.TLabel").pack(side="left")
        ttk.Button(calendar_header, text="다음 달 ▶", command=self.next_calendar_month).pack(side="right")
        ttk.Button(calendar_header, text="◀ 이전 달", command=self.previous_calendar_month).pack(side="right", padx=4)
        self.calendar_title = ttk.Label(calendar_header, text="", style="Section.TLabel")
        self.calendar_title.pack(side="right", padx=12)

        self.calendar_frame = ttk.Frame(left, style="Card.TFrame")
        self.calendar_frame.pack(fill="both", expand=True)
        for column, day_name in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
            label = tk.Label(self.calendar_frame, text=day_name, bg="#e9eef0", fg="#52616b", font=("맑은 고딕", 9, "bold"), pady=5)
            label.grid(row=0, column=column, sticky="nsew", padx=1, pady=(0, 2))
            self.calendar_frame.columnconfigure(column, weight=1, uniform="calendar")
        for row in range(1, 7):
            self.calendar_frame.rowconfigure(row, weight=1, uniform="calendar")

        ttk.Label(left, text="선택한 날짜의 상세 내역", style="Section.TLabel").pack(anchor="w", pady=(12, 6))
        detail_frame = ttk.Frame(left)
        detail_frame.pack(fill="x")
        detail_columns = ("type", "category", "memo", "amount")
        self.tree = ttk.Treeview(detail_frame, columns=detail_columns, show="headings", height=3, selectmode="browse")
        detail_headings = {"type": "구분", "category": "카테고리", "memo": "내용", "amount": "금액"}
        detail_widths = {"type": 58, "category": 92, "memo": 150, "amount": 110}
        for column in detail_columns:
            self.tree.heading(column, text=detail_headings[column])
            self.tree.column(column, width=detail_widths[column], anchor="e" if column == "amount" else "w")
        self.tree.pack(side="left", fill="x", expand=True)
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient="vertical", command=self.tree.yview)
        detail_scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=detail_scrollbar.set)
        self.tree.bind("<Delete>", lambda _event: self.delete_selected())
        ttk.Button(left, text="선택한 내역 삭제", command=self.delete_selected).pack(anchor="e", pady=(10, 0))

        report_header = ttk.Frame(right, style="Card.TFrame")
        report_header.pack(fill="x", pady=(0, 10))
        ttk.Label(report_header, text="소비 리포트", style="Section.TLabel").pack(side="left")
        ttk.Label(report_header, text="보기", background="#ffffff").pack(side="right", padx=(8, 5))
        self.report_view_var = tk.StringVar(value="그래프")
        self.report_view_menu = ttk.Combobox(report_header, textvariable=self.report_view_var, values=["그래프", "상세 내역"], state="readonly", width=12)
        self.report_view_menu.pack(side="right")
        self.report_view_menu.bind("<<ComboboxSelected>>", lambda _event: self.switch_report_view())
        cards = ttk.Frame(right, style="Card.TFrame")
        cards.pack(fill="x")
        self.card_labels = {}
        for index, (key, label, color) in enumerate([
            ("expense", "총 지출", "#c65b54"),
            ("income", "총 수입", "#287c70"),
            ("balance", "잔액", "#365f9b"),
        ]):
            card = tk.Frame(cards, bg="#f4f6f8", padx=14, pady=10)
            card.grid(row=0, column=index, sticky="ew", padx=(0, 8 if index < 2 else 0))
            tk.Label(card, text=label, bg="#f4f6f8", fg="#697783", font=("맑은 고딕", 9)).pack(anchor="w")
            value = tk.Label(card, text="0원", bg="#f4f6f8", fg=color, font=("맑은 고딕", 15, "bold"))
            value.pack(anchor="w", pady=(3, 0))
            self.card_labels[key] = value
        for index in range(3):
            cards.columnconfigure(index, weight=1)

        self.summary_label = ttk.Label(right, text="표시 중인 내역 0건", background="#ffffff", foreground="#697783")
        self.summary_label.pack(anchor="w", pady=(16, 4))
        self.report_content = ttk.Frame(right, style="Card.TFrame")
        self.report_content.pack(fill="both", expand=True)
        self.chart = tk.Canvas(self.report_content, height=245, bg="#ffffff", highlightthickness=0)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda _event: self.draw_chart())

        detail_columns = ("date", "type", "category", "memo", "amount")
        detail_frame = ttk.Frame(self.report_content)
        self.report_detail_tree = ttk.Treeview(detail_frame, columns=detail_columns, show="headings", selectmode="browse")
        detail_headings = {"date": "날짜", "type": "구분", "category": "카테고리", "memo": "내용", "amount": "금액"}
        detail_widths = {"date": 88, "type": 55, "category": 80, "memo": 130, "amount": 100}
        for column in detail_columns:
            self.report_detail_tree.heading(column, text=detail_headings[column])
            self.report_detail_tree.column(column, width=detail_widths[column], anchor="e" if column == "amount" else "w")
        report_scrollbar = ttk.Scrollbar(detail_frame, orient="vertical", command=self.report_detail_tree.yview)
        self.report_detail_tree.configure(yscrollcommand=report_scrollbar.set)
        self.report_detail_tree.pack(side="left", fill="both", expand=True)
        report_scrollbar.pack(side="right", fill="y")
        self.report_detail_frame = detail_frame

        self.content = content
        self.left_panel = left
        self.right_panel = right

    def switch_report_view(self):
        if self.report_view_var.get() == "상세 내역":
            self.chart.pack_forget()
            self.report_detail_frame.pack(fill="both", expand=True)
            self.show_report_details(self.get_filtered_records())
        else:
            self.report_detail_frame.pack_forget()
            self.chart.pack(fill="both", expand=True)
            self.draw_chart()

    def show_report_details(self, records):
        for item in self.report_detail_tree.get_children():
            self.report_detail_tree.delete(item)
        for record in records:
            self.report_detail_tree.insert(
                "", "end", iid=str(record["id"]),
                values=(record["date"], record["type"], record["category"], record["memo"], f"{record['amount']:,}원"),
            )

    def handle_resize(self, _event=None):
        width = self.root.winfo_width()
        compact = width < 1000
        if compact == self.compact_layout or width <= 1:
            return
        self.compact_layout = compact
        self.left_panel.pack_forget()
        self.right_panel.pack_forget()
        if compact:
            self.left_panel.pack(fill="x", expand=False, pady=(0, 10))
            self.right_panel.pack(fill="both", expand=True)
            self.date_entry.configure(width=12)
            self.type_combo.configure(width=8)
            self.category_combo.configure(width=9)
            self.memo_entry.configure(width=16)
            self.amount_entry.configure(width=11)
        else:
            self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
            self.right_panel.pack(side="right", fill="both", expand=True, padx=(8, 0))
            self.date_entry.configure(width=17)
            self.type_combo.configure(width=10)
            self.category_combo.configure(width=13)
            self.memo_entry.configure(width=28)
            self.amount_entry.configure(width=16)

    def previous_calendar_month(self):
        if self.calendar_month == 1:
            self.calendar_year -= 1
            self.calendar_month = 12
        else:
            self.calendar_month -= 1
        self.update_calendar_only()

    def next_calendar_month(self):
        if self.calendar_month == 12:
            self.calendar_year += 1
            self.calendar_month = 1
        else:
            self.calendar_month += 1
        self.update_calendar_only()

    def update_calendar_only(self):
        self.render_calendar(self.get_filtered_records())
        self.show_selected_date_records()

    def render_calendar(self, records):
        for cell in self.calendar_cells.values():
            cell.destroy()
        self.calendar_cells.clear()
        self.calendar_title.configure(text=f"{self.calendar_year}년 {self.calendar_month}월")
        monthly_records = defaultdict(lambda: {"수입": 0, "지출": 0})
        for record in records:
            if record["date"].startswith(f"{self.calendar_year:04d}-{self.calendar_month:02d}"):
                monthly_records[record["date"]][record["type"]] += record["amount"]

        month_days = calendar.monthcalendar(self.calendar_year, self.calendar_month)
        for week_index, week in enumerate(month_days, start=1):
            for day_index, day in enumerate(week):
                if day == 0:
                    continue
                date_text = f"{self.calendar_year:04d}-{self.calendar_month:02d}-{day:02d}"
                summary = monthly_records[date_text]
                cell = tk.Frame(self.calendar_frame, bg="#ffffff", highlightthickness=1, highlightbackground="#e1e7e9", cursor="hand2")
                cell.grid(row=week_index, column=day_index, sticky="nsew", padx=1, pady=1)
                cell.bind("<Button-1>", lambda _event, selected=date_text: self.select_calendar_date(selected))
                day_color = "#c65b54" if day_index == 6 else "#34444f"
                day_label = tk.Label(cell, text=str(day), bg="#ffffff", fg=day_color, font=("맑은 고딕", 10, "bold"))
                day_label.pack(anchor="nw", padx=5, pady=(4, 1))
                day_label.bind("<Button-1>", lambda _event, selected=date_text: self.select_calendar_date(selected))
                income_label = tk.Label(cell, text=self.calendar_amount_text("수입", summary["수입"]), bg="#ffffff", fg="#287c70", font=("맑은 고딕", 8), anchor="w")
                income_label.pack(fill="x", padx=5)
                income_label.bind("<Button-1>", lambda _event, selected=date_text: self.select_calendar_date(selected))
                expense_label = tk.Label(cell, text=self.calendar_amount_text("지출", summary["지출"]), bg="#ffffff", fg="#c65b54", font=("맑은 고딕", 8), anchor="w")
                expense_label.pack(fill="x", padx=5)
                expense_label.bind("<Button-1>", lambda _event, selected=date_text: self.select_calendar_date(selected))
                self.calendar_cells[date_text] = cell
        self.highlight_selected_calendar_date()

    @staticmethod
    def calendar_amount_text(record_type, amount):
        if not amount:
            return f"{record_type} -"
        return f"{record_type} {amount:,}원"

    def select_calendar_date(self, date_text):
        self.selected_calendar_date = date_text
        self.show_selected_date_records()
        self.highlight_selected_calendar_date()

    def highlight_selected_calendar_date(self):
        for date_text, cell in self.calendar_cells.items():
            background = "#e4f3ef" if date_text == self.selected_calendar_date else "#ffffff"
            cell.configure(bg=background)
            for child in cell.winfo_children():
                child.configure(bg=background)

    def show_selected_date_records(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        selected_records = [record for record in self.records if record["date"] == self.selected_calendar_date]
        for record in selected_records:
            self.tree.insert("", "end", iid=str(record["id"]), values=(record["type"], record["category"], record["memo"], f"{record['amount']:,}원"))

    def add_record(self):
        date_text = self.date_var.get().strip()
        memo = self.memo_var.get().strip()
        amount_text = self.amount_var.get().replace(",", "").strip()
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
            amount = int(amount_text)
            if amount <= 0:
                raise ValueError
            if not memo:
                raise ValueError
        except ValueError:
            messagebox.showwarning("입력 확인", "날짜는 YYYY-MM-DD 형식, 금액은 양의 정수로 입력하고 내용을 작성해 주세요.")
            return

        self.records.append({
            "id": self.next_id,
            "date": date_text,
            "type": self.type_var.get(),
            "category": self.category_var.get(),
            "memo": memo,
            "amount": amount,
        })
        self.next_id += 1
        self.memo_var.set("")
        self.amount_var.set("")
        self.update_view()

    def get_filtered_records(self):
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        month = self.month_var.get().strip()
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d") if start else None
            end_date = datetime.strptime(end, "%Y-%m-%d") if end else None
        except ValueError:
            messagebox.showwarning("필터 확인", "시작일과 종료일은 YYYY-MM-DD 형식으로 입력해 주세요.")
            return []
        if month and (len(month) != 7 or month[4] != "-"):
            messagebox.showwarning("필터 확인", "월별 보기는 YYYY-MM 형식으로 입력해 주세요.")
            return []

        filtered = []
        for record in self.records:
            record_date = datetime.strptime(record["date"], "%Y-%m-%d")
            if start_date and record_date < start_date:
                continue
            if end_date and record_date > end_date:
                continue
            if month and not record["date"].startswith(month):
                continue
            filtered.append(record)
        return sorted(filtered, key=lambda item: (item["date"], item["id"]), reverse=True)

    def update_view(self):
        filtered = self.get_filtered_records()
        month = self.month_var.get().strip()
        if len(month) == 7 and month[4] == "-":
            try:
                selected_month = datetime.strptime(month, "%Y-%m")
                self.calendar_year = selected_month.year
                self.calendar_month = selected_month.month
            except ValueError:
                pass
        self.render_calendar(filtered)
        self.show_selected_date_records()

        expense = sum(item["amount"] for item in filtered if item["type"] == "지출")
        income = sum(item["amount"] for item in filtered if item["type"] == "수입")
        self.card_labels["expense"].configure(text=f"{expense:,}원")
        self.card_labels["income"].configure(text=f"{income:,}원")
        self.card_labels["balance"].configure(text=f"{income - expense:,}원")
        self.summary_label.configure(text=f"표시 중인 내역 {len(filtered)}건  |  평균 지출 {self.average_expense(filtered):,}원")
        self.draw_chart(filtered)
        if self.report_view_var.get() == "상세 내역":
            self.show_report_details(filtered)

    @staticmethod
    def average_expense(records):
        expenses = [item["amount"] for item in records if item["type"] == "지출"]
        return round(sum(expenses) / len(expenses)) if expenses else 0

    def draw_chart(self, records=None):
        if records is None:
            records = self.get_filtered_records()
        self.chart.delete("all")
        width = max(self.chart.winfo_width(), 300)
        height = max(self.chart.winfo_height(), 220)
        expenses = [item for item in records if item["type"] == "지출"]
        if not expenses:
            self.chart.create_text(width / 2, height / 2, text="지출 데이터가 있으면 그래프가 표시됩니다", fill="#97a3aa", font=("맑은 고딕", 10))
            return

        grouped = defaultdict(int)
        if self.chart_var.get() == "카테고리별 지출":
            for item in expenses:
                grouped[item["category"]] += item["amount"]
        else:
            for item in expenses:
                grouped[item["date"]] += item["amount"]
            grouped = dict(sorted(grouped.items())[-10:])

        labels = list(grouped.keys())
        values = list(grouped.values())
        max_value = max(values)
        chart_left, chart_right = 42, width - 14
        chart_top, chart_bottom = 18, height - 42
        self.chart.create_line(chart_left, chart_bottom, chart_right, chart_bottom, fill="#cfd8dc")
        slot = (chart_right - chart_left) / max(len(values), 1)
        bar_width = min(42, slot * 0.62)
        for index, (label, value) in enumerate(zip(labels, values)):
            x_center = chart_left + slot * (index + 0.5)
            bar_height = (value / max_value) * (chart_bottom - chart_top - 12)
            x1, x2 = x_center - bar_width / 2, x_center + bar_width / 2
            y1, y2 = chart_bottom - bar_height, chart_bottom
            self.chart.create_rectangle(x1, y1, x2, y2, fill="#2b8a78", outline="")
            short_label = label[5:] if self.chart_var.get() == "일별 지출" and len(label) > 5 else label
            if len(short_label) > 7:
                short_label = short_label[:6] + "…"
            self.chart.create_text(x_center, chart_bottom + 16, text=short_label, fill="#697783", font=("맑은 고딕", 8))
            self.chart.create_text(x_center, y1 - 8, text=f"{value:,}", fill="#36534e", font=("맑은 고딕", 8))

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("삭제", "삭제할 내역을 먼저 선택해 주세요.")
            return
        selected_id = int(selected[0])
        self.records = [record for record in self.records if record["id"] != selected_id]
        self.update_view()

    def clear_filters(self):
        self.start_var.set("")
        self.end_var.set("")
        self.month_var.set("")
        self.update_view()

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")])
        if not path:
            return
        try:
            loaded = []
            with open(path, "r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                required = {"date", "type", "category", "memo", "amount"}
                if not reader.fieldnames or not required.issubset(reader.fieldnames):
                    raise ValueError("필수 열이 없습니다.")
                for row in reader:
                    datetime.strptime(row["date"], "%Y-%m-%d")
                    loaded.append({
                        "id": self.next_id,
                        "date": row["date"],
                        "type": row["type"],
                        "category": row["category"],
                        "memo": row["memo"],
                        "amount": int(row["amount"]),
                    })
                    self.next_id += 1
            self.records.extend(loaded)
            self.update_view()
            messagebox.showinfo("불러오기 완료", f"{len(loaded)}건의 내역을 불러왔습니다.")
        except (OSError, ValueError, KeyError) as error:
            messagebox.showerror("불러오기 실패", f"CSV 파일을 읽지 못했습니다.\n{error}")

    def save_csv(self):
        if not self.records:
            messagebox.showinfo("저장", "저장할 내역이 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"가계부_{datetime.now().strftime('%Y%m%d')}.csv",
            filetypes=[("CSV 파일", "*.csv")],
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(file, fieldnames=["date", "type", "category", "memo", "amount"])
                writer.writeheader()
                writer.writerows({key: record[key] for key in writer.fieldnames} for record in self.records)
            messagebox.showinfo("저장 완료", f"{Path(path).name} 파일로 저장했습니다.")
        except OSError as error:
            messagebox.showerror("저장 실패", str(error))


def main():
    root = tk.Tk()
    BudgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
