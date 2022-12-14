from openpyxl import Workbook
from utils import *

def write_excel(img_dict, excel_path = './result.xlsx'):

    wb = Workbook()
    ws = wb.active

    for key, val in img_dict.items():
        
        try:
            ws.merge_cells(start_row=key[0], end_row=key[1], start_column=key[2], end_column=key[3])
            ws.cell(key[0], key[2], img2text(val))
        except AttributeError:
            print(f'merge conflict at {key}')
            continue

    wb.save(excel_path)