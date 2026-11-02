import tkinter as tk
from tkinter import ttk, filedialog, simpledialog

from data.libs.gui import EmailValidatorGUI
from data.libs.file_processing import DataGather

class EmailValidatorGuiFunctions(EmailValidatorGUI):

    def __init__(self, root: tk.Tk) -> None:
        self.data = DataGather()
        super().__init__(root)
        self._fill_history_tree()  # обновляем историю


    def single_checking(self):

        email = simpledialog.askstring("Ввод email", "Введите email для проверки:")
        if email is None:
            return

        result = self.data.single_checking(email)  # получаем результат проверки, обновляем лог

        self.clear_tree(self.results_tree)  # очищаем таблицу последней проверки
        self.add_result_row(list(result.values()), self.data.MAX_LOG_LINES)  # вносим результат последней проверки
        self._fill_history_tree()  # заполняем таблицу лога



    def multiple_checking(self):

        filepath = filedialog.askopenfilename(
            title="Выберите файл с email-адресами",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not filepath:
            return  # пользователь отменил выбор

        result_list = self.data.multiple_checking(filepath)  # запускаем множественную проверку

        self.clear_tree(self.results_tree)  # очищаем таблицу последней проверки
        for row in result_list:
            if isinstance(row, list):
                self.add_result_row(row)  # добавляем каждую запись в таблицу результатов
        self._fill_history_tree()  # обновляем историю



    def _fill_history_tree(self):

        # читаем информацию из лога
        history_list = self.data.get_history()

        # очищаем таблицу лога
        self.clear_tree(self.history_tree)

        # проверяем корректность данных
        if not (isinstance(history_list, list) and len(history_list) > 0 and isinstance(history_list[0], list)):
            return

        # заполняем таблицу лога
        for row in history_list:
            self.add_history_row(row)



if __name__ == "__main__":
    root = tk.Tk()
    app = EmailValidatorGuiFunctions(root)
    root.mainloop()