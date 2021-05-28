# import tkinter as tk
# # from tkinter import filedialog
# # import pandas as pd
# #
# # root = tk.Tk()
# #
# # canvas1 = tk.Canvas(root, width=300, height=300, bg='lightsteelblue2', relief='raised')
# # canvas1.pack()
# #
# #
# # def getCSV():
# #     global df
# #
# #     import_file_path = filedialog.askopenfilename()
# #     df = pd.read_csv(import_file_path)
# #     print(df)
# #
# #
# # browseButton_CSV = tk.Button(text="      Import CSV File     ", command=getCSV, bg='green', fg='white',
# #                              font=('helvetica', 12, 'bold'))
# # canvas1.create_window(150, 150, window=browseButton_CSV)
# #
# # root.mainloop()

def ch_list_from_list(is_req, *argv):
    req_txt = "?" if is_req == 1 else ""
    txt = ""
    for items in argv:
        txt = f'{txt}{items},'
    txt = txt[:-1]
    txt = f'{req_txt} (@{txt})'
    return txt


print(ch_list_from_list(1, 301, 302, 303))
print(ch_list_from_list(1, 301))