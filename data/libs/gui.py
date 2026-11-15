import tkinter as tk
from tkinter import ttk, messagebox

class EmailValidatorGUI:
    """
    Базовый GUI-каркас приложения для проверки email-адресов (tkinter/ttk).

    Строит окно с тремя зонами:
    - панель выбора типа проверки (кнопки «Одиночная проверка» и «Множественная проверка»);
    - поле ввода контрольного регулярного выражения;
    - вкладки «Результат текущей проверки» и «История проверок» с таблицами (Treeview),
      включающими колонки: дата/время, email, результат, причина.

    Класс не выполняет проверки сам: методы single_checking и multiple_checking —
    заглушки и предназначены для переопределения в дочерних классах, которые
    подключают логику валидации (например, DataGather).

    Для вывода результатов дочерние классы используют методы add_result_row,
    add_history_row и clear_tree.

    Class Attributes:
        _WIDTH (int): начальная ширина окна в пикселях.
        _HEIGHT (int): начальная высота окна в пикселях.
        _MIN_WIDTH (int): минимальная ширина окна.
        _MIN_HEIGHT (int): минимальная высота окна.
    """

    _WIDTH = 750
    _HEIGHT = 450

    # Минимальные размеры
    _MIN_WIDTH = 500
    _MIN_HEIGHT = 300


    def __init__(self, root: tk.Tk) -> None:
        """
        Строит интерфейс в переданном корневом окне.

        Настраивает размеры и минимальные размеры окна, размещает сверху вниз:
        панель кнопок выбора типа проверки, поле ввода регулярного выражения
        и вкладку-контейнер (Notebook) с таблицами результатов и истории.
        Создаёт и настраивает таблицы через _setup_tab.

        Args:
            root (tk.Tk): корневое окно tkinter, в котором строится интерфейс.
        """
        
        self.root = root
        self.root.title("Email Validator")
        self.root.geometry(f"{self._WIDTH}x{self._HEIGHT}")
        self.root.minsize(self._MIN_WIDTH, self._MIN_HEIGHT)
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
        self.notebook.add(self.results_tab, text=" Результат текущей проверки ")

        # Вкладка истории
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text=" История проверок ")

        # Свойства (инициализируются в _setup_tab)
        self.results_tree = None
        self.history_tree = None

        self._setup_tab(self.results_tab, "results_tree")
        self._setup_tab(self.history_tab, "history_tree")

    def single_checking(self):
        """
        Заглушка: проверка одиночного email.

        В базовом классе не реализована и показывает информационное сообщение.
        Предназначена для переопределения в дочернем классе, где реализуется
        логика проверки одного email-адреса (например, через DataGather)
        с выводом результата в таблицу через add_result_row.
        """
        
        messagebox.showinfo(
            "Не реализовано",
            "Переписать в дочернем классе метод проверки одиночного email"
        )

    def multiple_checking(self):
        """
        Заглушка: множественная проверка email из файла.

        В базовом классе не реализована и показывает информационное сообщение.
        Предназначена для переопределения в дочернем классе, где реализуется
        чтение файла с email-адресами и их пакетная проверка (например, через
        DataGather) с выводом результатов в таблицу через add_result_row
        и в историю через add_history_row.
        """

        messagebox.showinfo(
            "Не реализовано",
            "Переписать в дочернем классе метод множественной проверки email"
        )

    def add_result_row(self, values: list, max_rows: int = 0) -> None:
        """
        Добавляет строку в таблицу «Результат текущей проверки».

        Делегирует добавление в _add_row_to_tree.

        Args:
            values (list): значения строки; лишние элементы сверх числа колонок обрезаются.
            max_rows (int): максимальное число строк в таблице; 0 — без ограничения.
                При превышении самая старая (верхняя) строка удаляется.
        """
        self._add_row_to_tree(self.results_tree, values, max_rows)

    def add_history_row(self, values: list, max_rows: int = 0) -> None:
        """
        Добавляет строку в таблицу «История проверок».

        Делегирует добавление в _add_row_to_tree.

        Args:
            values (list): значения строки; лишние элементы сверх числа колонок обрезаются.
            max_rows (int): максимальное число строк в таблице; 0 — без ограничения.
                При превышении самая старая (верхняя) строка удаляется.
        """
        self._add_row_to_tree(self.history_tree, values, max_rows)

    @staticmethod
    def clear_tree(tree: ttk.Treeview) -> None:
        """
        Полностью очищает таблицу от всех строк.

        Args:
            tree (ttk.Treeview): таблица, которую нужно очистить.
        """
        tree.delete(*tree.get_children())

    @staticmethod
    def _add_row_to_tree(tree: ttk.Treeview, values: list, max_rows: int = 0) -> None:
        """
        Добавляет строку значений в конец таблицы и при необходимости ограничивает их число.

        Строка вставляется последней (внизу таблицы). Значения values обрезаются
        до числа колонок дерева. Если задан max_rows и после вставки строк стало
        больше, удаляется самая старая (первая сверху) строка.

        Args:
            tree (ttk.Treeview): целевая таблица.
            values (list): значения новой строки (колонки «Дата / время», «Email»,
                «Результат», «Причина»).
            max_rows (int): максимальное число строк в таблице; 0 — без ограничения.
        """
        column_count = len(tree["columns"])
        trimmed_values = values[:column_count]
        tree.insert("", tk.END, values=trimmed_values)

        if max_rows > 0:
            all_items = tree.get_children()
            if len(all_items) > max_rows:
                tree.delete(all_items[0])

    def _setup_tab(self, tab: ttk.Frame, name: str) -> None:
        """
        Создаёт внутри вкладки таблицу (Treeview) со скроллбарами и сохраняет её в атрибуте.

        Формирует таблицу с четырьмя колонками («Дата / время», «Email», «Результат»,
        «Причина»), задаёт заголовки и ширины колонок, пропорциональные соотношению
        (2, 3, 2, 5) от _WIDTH, подключает вертикальный и горизонтальный скроллбары
        и настраивает растягивание таблицы внутри вкладки.

        Перетаскивание разделителей колонок и отпускание кнопки мыши принудительно
        обновляют горизонтальный скроллбар (ограничение стандартного поведения Tk);
        двойной клик по ячейке открывает полную запись через _show_record.

        Args:
            tab (ttk.Frame): контейнер вкладки, в который помещается таблица.
            name (str): имя атрибута экземпляра, в который сохраняется созданное дерево
                (например, "results_tree" или "history_tree").
        """
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

        # Форсируем обновление горизонтального скроллбара при перетаскивании
        # разделителей колонок: Tk сам не оповещает xscrollcommand об этом
        tree.bind(
            "<B1-Motion>",
            lambda event: event.widget.xview_moveto(event.widget.xview()[0])
        )
        tree.bind(
            "<ButtonRelease-1>",
            lambda event: event.widget.xview_moveto(event.widget.xview()[0])
        )
        tree.bind("<Double-1>", self._show_record)

        # Настройка весов для контейнера
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        setattr(self, name, tree)


    def _show_record(self, event) -> None:
        """
        Показывает полную запись таблицы в окне сообщения (по двойному клику).

        Args:
            event: событие tkinter; widget события — таблица, в которой кликнули.
        """
        tree = event.widget
        if tree.identify("region", event.x, event.y) != "cell":
            return
        item_id = tree.focus()
        if not item_id:
            return
        values = tree.item(item_id, "values")
        text = "\n".join(f"{col}: {val}" for col, val in zip(tree["columns"], values))
        messagebox.showinfo("Полная запись", text)
