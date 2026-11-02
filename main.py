import tkinter as tk

from data.libs.gui import EmailValidatorGUI
from data.libs.file_processing import DataGather

class EmailValidatorGuiFunctions(EmailValidatorGUI):
    def __init__(self, root: tk.Tk):

        self.data = DataGather()

        super().__init__()




if __name__ == "__main__":



    root = tk.Tk()
    app = EmailValidatorGuiFunctions(root)
    root.mainloop()