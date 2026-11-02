import tkinter as tk
from tkinter import ttk, messagebox


class EmailValidatorGUI:

    _WIDTH = 650
    _HEIGHT = 400

    def __init__(self, root: tk.Tk) -> None:

        # ОКНО
        self.root = root
        self.root.title("Email Validator")
        self.root.geometry(f"{self._WIDTH}x{self._HEIGHT}")

        # КОНТЕЙНЕР ПРОВЕРОК
        checking_frame = ttk.LabelFrame(root, text="Выбор типа проверки email", padding=10)
        checking_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # кнопки
        ttk.Button(
            checking_frame,
            text="Одиночная проверка",
            command=self.single_checking).grid(row=0, column=0, padx=5, pady=2, sticky=tk.EW)
        ttk.Button(
            checking_frame,
            text="Множественная проверка",
            command=self.multiple_checking).grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)

        # растяжение содержимого контейнера проверок
        checking_frame.columnconfigure(0, weight=1)
        checking_frame.columnconfigure(1, weight=1)

        # КОНТЕЙНЕР РЕГУЛЯРНОГО ВЫРАЖЕНИЯ
        re_frame = ttk.LabelFrame(root, text="Контрольное регулярное выражение", padding=10)
        re_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # поле для регулярного выражения — занимает всю ширину
        self.pattern_entry = ttk.Entry(re_frame)
        self.pattern_entry.grid(row=0, column=0, padx=5, pady=2, sticky=tk.EW)

        # растяжение содержимого контейнера регулярных выражений
        re_frame.columnconfigure(0, weight=1)

        # ВКЛАДКИ РЕЗУЛЬТАТОВ И ИСТОРИИ
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # вкладка последнего результата
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text=" Последний результат ")

        # вкладка истории
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text=" История проверок ")

        # свойства
        self.results_tree = None  # сделал для того, чтобы в IDE всплывали подсказки с именем свйоства
        self.history_tree = None  # сделал для того, чтобы в IDE всплывали подсказки с именем свйоства
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
        # Ограничиваем список количеством столбцов в Treeview
        column_count = len(tree["columns"])
        trimmed_values = values[:column_count]
        tree.insert("", tk.END, values=trimmed_values)

        # удалем лишние строки если есть огранчиения
        if max_rows > 0:
            # все элементы в порядке добавления
            all_items = tree.get_children()
            if len(all_items) > max_rows:
                # удаляем самый старый элемент
                tree.delete(all_items[0])




    def _setup_tab(self, tab: ttk.Frame, name: str) -> None:
        columns = ("Дата / время", "Email", "Результат", "Причина")
        proportions = (4, 4, 4, 6)  # сумма = 18
        total_width = self._WIDTH

        tree = ttk.Treeview(tab, columns=columns, show="headings", height=10)

        for col, prop in zip(columns, proportions):
            width = (prop * total_width) // sum(proportions)
            tree.heading(col, text=col.capitalize())
            tree.column(col, width=width, anchor=tk.W, stretch=tk.YES)

        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # сохраняем ссылку на дерево как атрибут экземпляра
        setattr(self, name, tree)
















if __name__ == "__main__":
    root = tk.Tk()
    app = EmailValidatorGUI(root)
    root.mainloop()