import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

from data.libs.gui import EmailValidatorGUI
from data.libs.file_processing import DataGather


class EmailValidatorGuiFunctions(EmailValidatorGUI):

    def __init__(self, root: tk.Tk) -> None:
        """
        Инициализирует интерфейс базового класса и подключает логику проверок.

        Порядок действий: строит интерфейс родительского класса (кнопки, поле паттерна,
        вкладки с таблицами), затем создаёт DataGather, подставляет стандартный паттерн
        в поле ввода регулярного выражения и заполняет таблицу истории из slow-лога.

        Args:
            root (tk.Tk): корневое окно tkinter.
        """
        
        super().__init__(root)
        try:
            self.data = DataGather()
        except (FileNotFoundError, RuntimeError) as e:
            messagebox.showerror("Ошибка инициализации", f"Не удалось подготовить лог-файлы: {e}")
            root.destroy()
            raise
        self.pattern_entry.insert(0, self.data.email_validator.DEFAULT_PATTERN)
        self._fill_history_tree()
        

    def single_checking(self):
        """
        Проверяет одиночный email, введённый пользователем в диалоговом окне.

        Порядок действий:
        1. Запрашивает email через диалог ввода (simpledialog); при отмене — выход.
        2. Применяет к валидатору регулярное выражение из поля pattern_entry;
        при некорректном паттерне показывает сообщение об ошибке и выход,
        не выполняя проверку.
        3. Выполняет проверку через DataGather.single_checking (результат попадает
        в оба лога).
        4. Очищает таблицу «Последний результат» и добавляет одну строку результата;
        обновляет таблицу истории.

        Returns:
            None
        """
        
        pattern = self.pattern_entry.get()
        try:
            self.data.email_validator.set_pattern(pattern)
        except (ValueError, re.error) as e:
            messagebox.showerror(
                "Некорректное регулярное выражение", 
                f"Не удалось применить паттерн: {e}"
            )
            return

        email = simpledialog.askstring("Ввод email", "Введите email для проверки:")
        if email is None:
            return

        result = self.data.single_checking(email)

        self.clear_tree(self.results_tree)
        self.add_result_row(list(result.values()), self.data.MAX_LOG_LINES)
        self._fill_history_tree()


    def multiple_checking(self):
        filepath = filedialog.askopenfilename(
            title="Выберите файл с email-адресами",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not filepath:
            return

        pattern = self.pattern_entry.get()
        self.data.email_validator.set_pattern(pattern)

        result_list = self.data.multiple_checking(filepath)

        self.clear_tree(self.results_tree)
        for row in result_list:
            if isinstance(row, dict):
                added_row = list(row.values())
                self.add_result_row(added_row)

        self._fill_history_tree()

    def _fill_history_tree(self):
        history_list = self.data.get_history()

        self.clear_tree(self.history_tree)

        if not (isinstance(history_list, list) and len(history_list) > 0 and isinstance(history_list[0], list)):
            return

        for row in history_list:
            self.add_history_row(row)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Email Validator")
    # root.minsize(700, 400)
    # root.geometry(f"{EmailValidatorGUI._WIDTH}x{EmailValidatorGUI._HEIGHT}")
    # root.rowconfigure(2, weight=1)
    # root.columnconfigure(0, weight=1)
    app = EmailValidatorGuiFunctions(root)
    root.mainloop()


