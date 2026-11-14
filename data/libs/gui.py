import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog


class EmailValidatorGUI:

    _WIDTH = 750
    _HEIGHT = 450

    # Минимальные размеры
    _MIN_WIDTH = 500
    _MIN_HEIGHT = 300


    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Email Validator")
        self.root.geometry(f"{self._WIDTH}x{self._HEIGHT}")
        self.root.minsize(self._MIN_WIDTH, self._MIN_HEIGHT)
        self.root.rowconfigure(1, weight=1)   # Вкладки растягиваются
        self.root.columnconfigure(0, weight=1)

        # КОНТЕЙНЕР ПРОВЕРОК
        checking_frame = ttk.LabelFrame(root, text="Выбор типа проверки email", padding=10)
        checking_frame.grid(row=0, column=0, sticky=tk.EW, padx=10, pady=(10, 5))
        checking_frame.columnconfigure(0, weight=1)
        checking_frame.columnconfigure(1, weight=1)

        ttk.Button(
            checking_frame,
            text="Одиночная проверка",
            command=self.single_checking
        ).grid(row=0, column=0, padx=5, pady=2, sticky=tk.EW)

        ttk.Button(
            checking_frame,
            text="Множественная проверка",
            command=self.multiple_checking
        ).grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)

        # КОНТЕЙНЕР РЕГУЛЯРНОГО ВЫРАЖЕНИЯ
        re_frame = ttk.LabelFrame(root, text="Контрольное регулярное выражение", padding=10)
        re_frame.grid(row=1, column=0, sticky=tk.EW, padx=10, pady=(10, 5))
        re_frame.columnconfigure(0, weight=1)

        self.pattern_entry = ttk.Entry(re_frame)
        self.pattern_entry.grid(row=0, column=0, padx=5, pady=2, sticky=tk.EW)

        # ВКЛАДКИ РЕЗУЛЬТАТОВ И ИСТОРИИ
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=2, column=0, sticky=tk.NSEW, padx=10, pady=5)
        root.rowconfigure(2, weight=1)

        # Вкладка последнего результата
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text=" Последний результат ")

        # Вкладка истории
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text=" История проверок ")

        # Свойства (инициализируются в _setup_tab)
        self.results_tree = None
        self.history_tree = None

        self._setup_tab(self.results_tab, "results_tree")
        self._setup_tab(self.history_tab, "history_tree")

    def single_checking(self):
        messagebox.showinfo(
            "Не реализовано",
            "Переписать в дочернем классе метод проверки одиночного email"
        )

    def multiple_checking(self):
        messagebox.showinfo(
            "Не реализовано",
            "Переписать в дочернем классе метод множественной проверки email"
        )

    def add_result_row(self, values: list, max_rows: int = 0) -> None:
        self._add_row_to_tree(self.results_tree, values, max_rows)

    def add_history_row(self, values: list, max_rows: int = 0) -> None:
        self._add_row_to_tree(self.history_tree, values, max_rows)

    @staticmethod
    def clear_tree(tree: ttk.Treeview) -> None:
        tree.delete(*tree.get_children())

    @staticmethod
    def _add_row_to_tree(tree: ttk.Treeview, values: list, max_rows: int = 0) -> None:
        column_count = len(tree["columns"])
        trimmed_values = values[:column_count]
        tree.insert("", tk.END, values=trimmed_values)

        if max_rows > 0:
            all_items = tree.get_children()
            if len(all_items) > max_rows:
                tree.delete(all_items[0])

    def _setup_tab(self, tab: ttk.Frame, name: str) -> None:
        columns = ("Дата / время", "Email", "Результат", "Причина")
        proportions = (2, 3, 2, 5)
        total_width = self._WIDTH

        # Создаем контейнер для дерева и скроллбаров
        container = ttk.Frame(tab)
        container.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(container, columns=columns, show="headings")

        for column, proportion in zip(columns, proportions):
            width = (proportion * total_width) // sum(proportions)
            minwidth = width // 2
            tree.heading(column, text=column.capitalize())
            tree.column(column, width=width, minwidth=minwidth, anchor=tk.W, stretch=tk.YES)

        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=tree.xview)

        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Правильный порядок и расположение элементов
        tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)

        # Настройка весов для контейнера
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        setattr(self, name, tree)

