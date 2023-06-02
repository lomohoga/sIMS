# To save the file as a stream
from tempfile import NamedTemporaryFile
from os import remove

# To get the current date & time (for the filename)
from datetime import datetime

# To access the database
import mysql.connector

# To open the form
from openpyxl import load_workbook

# To style text in the form
from openpyxl.cell.text import InlineFont
from openpyxl.cell.rich_text import TextBlock, CellRichText

def formgen (form, item):
    if str(form) == '58':
        cxn = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")
        db = cxn.cursor()
        db.execute(f"SELECT * FROM item WHERE ItemID = '{item}'")
        data = db.fetchone()
        cxn.close()

        if data == None: raise Exception(f"Item ID {item} not found.")

        wb = load_workbook("./src/form_templates/template_58.xlsx", rich_text = True)
        ws = wb.active

        ws["F8"] = CellRichText(ws["F8"].value, TextBlock(InlineFont(b = True), data[0]))
        ws["A8"] = CellRichText(ws["A8"].value, TextBlock(InlineFont(b = True), data[1].upper()))
        ws["A9"] = CellRichText(ws["A9"].value, TextBlock(InlineFont(b = True), data[2]))
        ws["A10"] = CellRichText(ws["A10"].value, TextBlock(InlineFont(b = True), data[5]))

        file = NamedTemporaryFile(suffix = ".xlsx", delete = False)

        try:
            with file as f:
                wb.save(f.name)
                f.seek(0)
                return f.read()
        finally:
            remove(file.name)
