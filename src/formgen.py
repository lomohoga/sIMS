# to save the file as a stream
from tempfile import NamedTemporaryFile
from os import remove

# to get the current date & time (for the filename)
from datetime import datetime

# to access the database
import mysql.connector

# to open the form
from openpyxl import load_workbook

# to style text in the form
from openpyxl.cell.text import InlineFont
from openpyxl.cell.rich_text import TextBlock, CellRichText

def form_58 (item):
    cxn = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")

    db = cxn.cursor()
    db.execute(f"SELECT * FROM item WHERE ItemID = '{item}'")
    data = db.fetchone()

    db.execute(f"SELECT * FROM (SELECT RequestID, RequestDate, AvailableStock, RequestQuantity, UPPER(CONCAT(FirstName, ' ', LastName)) as RequestedBy, ShelfLife from request_item INNER JOIN stock USING (ItemID) INNER JOIN request USING (RequestID) INNER JOIN user ON RequestedBy = Username WHERE ItemID = '{item}' ORDER BY RequestID DESC LIMIT 30) AS x ORDER BY RequestID ASC;")
    requests = db.fetchall()

    cxn.close()

    if data == None: raise Exception(f"Item ID {item} not found.")

    wb = load_workbook("./src/form_templates/template_58.xlsx", rich_text = True)
    ws = wb.active

    ws["F8"] = CellRichText(ws["F8"].value, TextBlock(InlineFont(b = True), data[0]))
    ws["A8"] = CellRichText(ws["A8"].value, TextBlock(InlineFont(b = True), data[1].upper()))
    ws["A9"] = CellRichText(ws["A9"].value, TextBlock(InlineFont(b = True), data[2]))
    ws["A10"] = CellRichText(ws["A10"].value, TextBlock(InlineFont(b = True), data[5]))

    for i in range(len(requests)):
        req = requests[i]

        ws[f"A{13 + i}"] = req[1]
        if i == 0: ws[f"C{13 + i}"] = req[2]
        ws[f"D{13 + i}"] = req[3]
        ws[f"E{13 + i}"] = req[4]
        ws[f"F{13 + i}"] = ws[f"C{13 + i}"].value - ws[f"D{13 + i}"].value if i == 0 else ws[f"F{12 + i}"].value - ws[f"D{13 + i}"].value
        if i == 0: ws[f"G{13 + i}"] = req[5]

    file = NamedTemporaryFile(suffix = ".xlsx", delete = False)

    try:
        with file as f:
            wb.save(f.name)
            f.seek(0)
            return f.read()
    finally:
        remove(file.name)

def form_69 (item):
    cxn = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")

    db = cxn.cursor()
    db.execute(f"SELECT * FROM item WHERE ItemID = '{item}'")
    data = db.fetchone()

    db.execute(f"SELECT * FROM (SELECT RequestID, RequestDate, AvailableStock, RequestQuantity, UPPER(CONCAT(FirstName, ' ', LastName)) as RequestedBy, Price from request_item INNER JOIN stock USING (ItemID) INNER JOIN request USING (RequestID) INNER JOIN user ON RequestedBy = Username WHERE ItemID = '{item}' ORDER BY RequestID DESC LIMIT 30) AS x ORDER BY RequestID ASC;")
    requests = db.fetchall()

    cxn.close()

    if data == None: raise Exception(f"Item ID {item} not found.")

    wb = load_workbook("./src/form_templates/template_69.xlsx", rich_text = True)
    ws = wb.active

    ws["B8"] = CellRichText(ws["B8"].value, TextBlock(InlineFont(b = True), data[1].upper()))
    ws["B10"] = CellRichText(ws["B10"].value, TextBlock(InlineFont(b = True), data[2]))
    ws["I9"] = CellRichText(ws["I9"].value, TextBlock(InlineFont(b = True), data[0]))

    for i in range(len(requests)):
        req = requests[i]

        ws[f"B{13 + i}"] = req[1]
        if i == 0: ws[f"D{13 + i}"] = req[2]
        ws[f"E{13 + i}"] = req[3]
        ws[f"F{13 + i}"] = req[4]
        ws[f"H{13 + i}"] = ws[f"D{13 + i}"].value - ws[f"E{13 + i}"].value if i == 0 else ws[f"H{12 + i}"].value - ws[f"E{13 + i}"].value
        if i == 0: ws[f"I{13 + i}"] = req[5]

    file = NamedTemporaryFile(suffix = ".xlsx", delete = False)

    try:
        with file as f:
            wb.save(f.name)
            f.seek(0)
            return f.read()
    finally:
        remove(file.name)
