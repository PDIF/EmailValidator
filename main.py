import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

from data.libs.gui import EmailValidatorGUI
from data.libs.file_processing import DataGather


class EmailValidatorGuiFunctions(EmailValidatorGUI):
    """
    Функциональный наследник GUI-каркаса: подключает реальную валидацию через DataGather.

    Переопределяет заглушки single_checking и multiple_checking:
    - single_checking применяет контрольное регулярное выражение из поля pattern_entry,
      запрашивает email через диалог ввода и выводит результат в таблицу
      «Результат текущей проверки», после чего обновляет вкладку «История проверок»;
    - multiple_checking применяет регулярное выражение из поля pattern_entry,
      запрашивает файл с email-адресами через диалог выбора файла, проверяет все
      адреса пакетно и выводит результаты (до MAX_LOG_LINES записей) в таблицу
      «Результат текущей проверки», затем обновляет историю.

    Подготовку паттерна оба метода выполняют через _apply_pattern: она считывает
    выражение из поля pattern_entry, при пустом поле предлагает паттерн по умолчанию
    (отказ прерывает проверку), при некорректном паттерне показывает сообщение
    об ошибке. В multiple_checking дополнительно перехватываются ошибки чтения файла.

    При ошибке инициализации DataGather показывает сообщение, уничтожает окно
    и пробрасывает исключение дальше. История отображается из slow-лога
    DataGather: в таблицу попадают только записи-списки ровно из четырёх
    значений [timestamp, email, status, reason].

    Attributes:
        data (DataGather): объект логики валидации и ведения истории проверок.
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Инициализирует интерфейс базового класса и подключает логику проверок.

        Порядок действий: строит интерфейс родительского класса (кнопки, поле паттерна,
        вкладки с таблицами), затем создаёт DataGather. Если подготовить лог-файлы
        не удалось, показывает сообщение об ошибке, уничтожает корневое окно
        и пробрасывает исключение — приложение не запускается без рабочей истории.
        Далее подставляет стандартный паттерн в поле ввода регулярного выражения
        и заполняет таблицу истории из slow-лога.

        Args:
            root (tk.Tk): корневое окно tkinter.

        Raises:
            FileNotFoundError: если DataGather не смог определить директории лог-файлов;
                перед пробросом корневое окно уничтожается.
        """
        super().__init__(root)
        try:
            self.data = DataGather()
        except FileNotFoundError as e:
            messagebox.showerror("Ошибка инициализации", f"Не удалось подготовить лог-файлы: {e}")
            root.destroy()
            raise
        self.pattern_entry.insert(0, self.data.email_validator.DEFAULT_PATTERN)
        self._fill_history_tree()
        

    def single_checking(self) -> None:
        """
        Проверяет одиночный email, введённый пользователем в диалоговом окне.

        Порядок действий:
        1. Применяет контрольное регулярное выражение из поля pattern_entry через
        _apply_pattern; если пользователь отказался от паттерна по умолчанию
        или паттерн некорректен, выходит без проверки.
        2. Запрашивает email через диалог ввода (simpledialog); при отмене — выход.
        3. Выполняет проверку через DataGather.single_checking (результат попадает
        в оба лога).
        4. Очищает таблицу «Результат текущей проверки» и добавляет одну строку
        результата; обновляет таблицу истории.

        Returns:
            None
        """
        if not self._apply_pattern():
            return

        email = simpledialog.askstring("Ввод email", "Введите email для проверки:")
        if email is None:
            return
        result = self.data.single_checking(email)
        self.clear_tree(self.results_tree)
        self.add_result_row(list(result.values()), self.data.MAX_LOG_LINES)
        self._fill_history_tree()


    def multiple_checking(self) -> None:
        """
        Выполняет пакетную проверку email-адресов из файла, выбранного пользователем.

        Порядок действий:
        1. Применяет контрольное регулярное выражение из поля pattern_entry через
        _apply_pattern; если пользователь отказался от паттерна по умолчанию
        или паттерн некорректен, выходит без проверки.
        2. Открывает диалог выбора текстового файла; при отмене (пустой путь) — выход.
        3. Выполняет пакетную проверку через DataGather.multiple_checking (все результаты
        записываются в логи); при ошибке доступа к файлу показывает сообщение
        об ошибке и выходит, не затрагивая таблицы.
        4. Очищает таблицу «Результат текущей проверки» и добавляет строки результатов
        (не более MAX_LOG_LINES, ограничение уже применено в DataGather);
        обновляет таблицу истории.

        Returns:
            None
        """
        if not self._apply_pattern():
            return

        filepath = filedialog.askopenfilename(
            title="Выберите файл с email-адресами",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not filepath:
            return

        try:
            result_list = self.data.multiple_checking(filepath)
        except (FileNotFoundError, OSError) as e:
            messagebox.showerror(
                "Ошибка чтения файла",
                f"Не удалось прочитать файл с email-адресами: {e}"
            )
            return

        self.clear_tree(self.results_tree)
        for row in result_list:
            self.add_result_row(list(row.values()))

        self._fill_history_tree()

            
    def _apply_pattern(self) -> bool:
        """
        Применяет контрольное регулярное выражение из поля pattern_entry к валидатору.

        Считывает содержимое поля и выполняет одно из действий:
        - если поле пусто или состоит из пробелов, показывает запрос с паттерном
          по умолчанию: при отказе метод возвращает False; при подтверждении
          паттерн по умолчанию полностью записывается в поле и применяется;
        - если поле заполнено, паттерн применяется как есть.

        При некорректном паттерне показывает сообщение об ошибке и возвращает False.

        Returns:
            bool: True, если валидатор получил рабочий паттерн и проверку можно
                выполнять; False, если пользователь отказался или паттерн
                некорректен.
        """
        pattern = self.pattern_entry.get()

        if not pattern.strip():
            proceed = messagebox.askyesno(
                "Пустой паттерн",
                (
                    "Поле для контрольного регулярного выражения не заполнено, "
                    "поэтому проверка будет выполнена с паттерном по умолчанию:\n\n"
                    f"{self.data.email_validator.DEFAULT_PATTERN}"
                )
            )
            if not proceed:
                return False
            pattern = self.data.email_validator.DEFAULT_PATTERN
            self.pattern_entry.delete(0, tk.END)
            self.pattern_entry.insert(0, pattern)

        try:
            self.data.email_validator.set_pattern(pattern)
        except (ValueError, re.error) as e:
            messagebox.showerror(
                "Некорректное контрольное регулярное выражение",
                f"Не удалось применить паттерн: {e}"
            )
            return False

        return True


    def _fill_history_tree(self) -> None:
        """
        Обновляет таблицу «История проверок» данными из slow-лога DataGather.

        Полностью очищает таблицу истории, затем читает get_history и заполняет
        её построчно. Если история пуста или недоступна — таблица остаётся очищенной.
        Формат каждой записи проверяется индивидуально: в таблицу попадают только
        записи-списки длиной ровно четыре значения; записи иных форматов
        (словари, строки, некорректные элементы) пропускаются, не ломая вывод
        остальных записей.

        Каждая корректная запись — список вида [timestamp, email, status, reason],
        порядок значений совпадает с колонками таблицы.

        Returns:
            None
        """
        history_list = self.data.get_history()

        self.clear_tree(self.history_tree)

        for row in history_list:
            if isinstance(row, list) and len(row) == 4:
                self.add_history_row(row)


if __name__ == "__main__":
    root = tk.Tk()
    app = EmailValidatorGuiFunctions(root)
    root.mainloop()
