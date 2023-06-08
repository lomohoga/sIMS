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

    db.execute(f"SELECT * FROM (SELECT RequestID, RequestDate, AvailableStock, RequestQuantity, UPPER(CONCAT(FirstName, ' ', LastName)) as RequestedBy, ShelfLife from request_item INNER JOIN stock USING (ItemID) INNER JOIN request USING (RequestID) INNER JOIN user ON RequestedBy = Username WHERE ItemID = '{item}' ORDER BY RequestID DESC LIMIT 30) AS x ORDER BY RequestID ASC")
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

def form_59 (request):
    cxn = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")

    db = cxn.cursor()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) FROM request INNER JOIN user ON RequestedBy = Username WHERE RequestID = {request}")
    (req_by,) = db.fetchone()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) FROM request INNER JOIN user ON IssuedBy = Username WHERE RequestID = {request}")
    (iss_by,) = db.fetchone()
    db.execute(f"SELECT DateReceived, DateIssued FROM request WHERE RequestID = {request}")
    (date_rec, date_iss) = db.fetchone()

    db.execute(f"SELECT RequestQuantity, Unit, Price, Price * RequestQuantity, ItemDescription, ItemID, ShelfLife FROM request_item INNER JOIN stock USING (ItemID) INNER JOIN request USING (RequestID) WHERE RequestID = '{request}' AND Price < 15000")
    items = db.fetchall()

    cxn.close()

    if len(items) == 0: return None

    wb = load_workbook("./src/form_templates/template_59.xlsx", rich_text = True)
    ws = wb.active

    for i in range(len(items)):
        row = items[i]

        ws[f"A{12 + i}"] = row[0]
        ws[f"B{12 + i}"] = row[1]
        ws[f"C{12 + i}"] = row[2]
        ws[f"D{12 + i}"] = row[3]
        ws[f"E{12 + i}"] = row[4]
        ws[f"G{12 + i}"] = row[5]
        ws[f"H{12 + i}"] = row[6] if row[6] is not None else "\u2014"

        ws["F46"] = req_by
        ws["F50"] = date_rec
        ws["A46"] = iss_by
        ws["A50"] = date_iss

    file = NamedTemporaryFile(suffix = ".xlsx", delete = False)

    try:
        with file as f:
            wb.save(f.name)
            f.seek(0)
            return f.read()
    finally:
        remove(file.name)

def form_63 (request):
    cxn = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")

    db = cxn.cursor()
    db.execute(f"SELECT RequestID, UPPER(CONCAT(FirstName, ' ', LastName)) as RequestedBy, item.ItemID as ItemID, item.ItemDescription as ItemDescription, RequestQuantity, QuantityIssued FROM request_item INNER JOIN request USING (RequestID) INNER JOIN item USING (ItemID) INNER JOIN stock USING (ItemID) INNER JOIN user ON RequestedBy = Username WHERE RequestID = '{request}'")
    data = db.fetchall()

    cxn.close()

    wb = load_workbook("./src/form_templates/template_63.xlsx", rich_text = True)
    ws = wb.active

    # ws["A9"] = CellRichText(ws["A9"].value, TextBlock(InlineFont(b = True), data[1]))

    for i in range(len(data)):
        req = data[i]

        ws[f"A{12 + i}"] = req[2]
        ws[f"C{12 + i}"] = req[3]
        ws[f"D{12 + i}"] = req[4]
        if req[5] > 0:
            ws[f"E{12 + i}"] = "\u2714"
            ws[f"G{12 + i}"] = req[5]
        else: ws[f"F{12 + i}"] = "\u2714"

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

    db.execute(f"SELECT * FROM (SELECT RequestID, RequestDate, AvailableStock, RequestQuantity, UPPER(CONCAT(FirstName, ' ', LastName)) as RequestedBy, Price from request_item INNER JOIN stock USING (ItemID) INNER JOIN request USING (RequestID) INNER JOIN user ON RequestedBy = Username WHERE ItemID = '{item}' ORDER BY RequestID DESC LIMIT 30) AS x ORDER BY RequestID ASC")
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

def form_71 (request):
    cxn = mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")

    db = cxn.cursor()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) FROM request INNER JOIN user ON RequestedBy = Username WHERE RequestID = {request}")
    (req_by,) = db.fetchone()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) FROM request INNER JOIN user ON IssuedBy = Username WHERE RequestID = {request}")
    (iss_by,) = db.fetchone()
    db.execute(f"SELECT DateReceived, DateIssued FROM request WHERE RequestID = {request}")
    (date_rec, date_iss) = db.fetchone()

    db.execute(f"SELECT RequestQuantity, Unit, ItemDescription, ItemID, Price * RequestQuantity FROM request_item INNER JOIN stock USING (ItemID) INNER JOIN request USING (RequestID) WHERE RequestID = '{request}' AND Price >= 15000")
    items = db.fetchall()

    cxn.close()

    if len(items) == 0: return None

    wb = load_workbook("./src/form_templates/template_71.xlsx", rich_text = True)
    ws = wb.active

    for i in range(len(items)):
        row = items[i]

        ws[f"A{11 + i}"] = row[0]
        ws[f"B{11 + i}"] = row[1]
        ws[f"C{11 + i}"] = row[2]
        ws[f"D{11 + i}"] = row[3]
        ws[f"E{11 + i}"] = date_rec
        ws[f"F{11 + i}"] = row[4]

        ws["A45"] = req_by
        ws["A49"] = date_rec
        ws["D45"] = iss_by
        ws["D49"] = date_iss

    file = NamedTemporaryFile(suffix = ".xlsx", delete = False)

    try:
        with file as f:
            wb.save(f.name)
            f.seek(0)
            return f.read()
    finally:
        remove(file.name)
