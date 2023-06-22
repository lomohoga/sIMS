from mysql.connector import Error as MySQLError

# to save the file as a stream
from tempfile import NamedTemporaryFile
from os import remove

# to open the form
from openpyxl import load_workbook

# to style text in the form
from openpyxl.cell.text import InlineFont
from openpyxl.cell.rich_text import TextBlock, CellRichText

from src.blueprints.database import connect_db
from src.blueprints.exceptions import ItemNotFoundError, RequestNotFoundError

def form_58 (db, item):
    db.execute(f"SELECT * FROM item WHERE ItemID = '{item}'")
    data = db.fetchone()
    if data is None: raise ItemNotFoundError(item = item)

    db.execute(f"SELECT * FROM (SELECT RequestID, RequestDate, DeliveryStock, QuantityIssued, UPPER(CONCAT(FirstName, ' ', LastName)) as RequestedBy, ShelfLife FROM request_item INNER JOIN (SELECT ItemID, ShelfLife, COALESCE(SUM(IF(ShelfLife IS NULL OR DATEDIFF(CURDATE(), ADDDATE(DeliveryDate, ShelfLife)) <= 0, DeliveryQuantity, 0)), 0) AS DeliveryStock FROM item LEFT JOIN delivery USING (ItemID) GROUP BY ItemID) AS w USING (ItemID) INNER JOIN request USING (RequestID) INNER JOIN user ON RequestedBy = Username WHERE ItemID = '{item}' AND StatusID = 4 ORDER BY RequestID DESC LIMIT 30) AS x ORDER BY RequestID ASC")
    requests = db.fetchall()

    wb = load_workbook("./src/form_templates/template_58.xlsx", rich_text = True)
    ws = wb.active

    ws["F8"] = CellRichText(ws["F8"].value, TextBlock(InlineFont(b = True), data[0]))
    ws["A8"] = CellRichText(ws["A8"].value, TextBlock(InlineFont(b = True), data[1].upper()))
    ws["A9"] = CellRichText(ws["A9"].value, TextBlock(InlineFont(b = True), data[3]))
    ws["A10"] = CellRichText(ws["A10"].value, TextBlock(InlineFont(b = True), data[6]))

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

def form_59 (db, request):
    db.execute(f"SELECT * FROM request WHERE RequestID = {request}")
    if db.fetchone() is None: raise RequestNotFoundError(request = request)

    db.execute(f"SELECT COUNT(*) + 1 FROM request WHERE StatusID = 4 && hasPropertyApproved = 0 && RequestID < {request};")
    ics_num = db.fetchone()[0]

    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) FROM request INNER JOIN user ON RequestedBy = Username WHERE RequestID = {request}")
    (req_by,) = db.fetchone()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) FROM request INNER JOIN user ON IssuedBy = Username WHERE RequestID = {request}")
    (iss_by,) = db.fetchone()
    db.execute(f"SELECT DateReceived, DateIssued FROM request WHERE RequestID = {request}")
    (date_rec, date_iss) = db.fetchone()

    db.execute(f"SELECT QuantityIssued, Unit, Price, Price * QuantityIssued, ItemDescription, ItemID, ShelfLife FROM request_item INNER JOIN stock USING (ItemID) INNER JOIN request USING (RequestID) WHERE RequestID = '{request}';")
    items = db.fetchall()

    if len(items) == 0: return None

    wb = load_workbook("./src/form_templates/template_59.xlsx", rich_text = True)
    ws = wb.active
    ws["H7"] = ics_num

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

def form_63 (db, request):
    db.execute(f"SELECT * FROM request WHERE RequestID = {request}")
    if db.fetchone() is None: raise RequestNotFoundError(request = request)

    db.execute(f"SELECT RequestID, item.ItemID AS ItemID, item.ItemDescription AS ItemDescription, RequestQuantity, QuantityIssued, Purpose, Remarks FROM request_item INNER JOIN request USING (RequestID) INNER JOIN item USING (ItemID) INNER JOIN stock USING (ItemID) INNER JOIN user ON RequestedBy = Username WHERE RequestID = '{request}'")
    data = db.fetchall()

    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) AS RequestedBy, DateApproved FROM request INNER JOIN user ON (Username = RequestedBy) WHERE RequestID = {request}")
    req_requested = db.fetchone()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) AS ActingAdmin, DateApproved FROM request INNER JOIN user ON (Username = ActingAdmin) WHERE RequestID = {request}")
    req_approved = db.fetchone()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) AS IssuedBy, DateApproved FROM request INNER JOIN user ON (Username = IssuedBy) WHERE RequestID = {request}")
    req_issued = db.fetchone()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) AS ReceivedBy, DateApproved FROM request INNER JOIN user ON (Username = ReceivedBy) WHERE RequestID = {request}")
    req_received = db.fetchone()

    wb = load_workbook("./src/form_templates/template_63.xlsx", rich_text = True)
    ws = wb.active

    for i in range(len(data)):
        req = data[i]

        ws["G9"] = req[0]
        ws[f"A{12 + i}"] = req[1]
        ws[f"C{12 + i}"] = req[2]
        ws[f"D{12 + i}"] = req[3]
        if req[3] > 0:
            ws[f"E{12 + i}"] = "\u2714"
        else: ws[f"F{12 + i}"] = "\u2714"
        ws[f"G{12 + i}"] = req[4]
        if req[6] is not None:
            ws[f"H{12 + i}"] = req[6]
        ws["B32"] = req[5]

    ws["C37"] = req_requested[0]
    ws["C39"] = req_requested[1]
    ws["D37"] = req_approved[0]
    ws["D39"] = req_approved[1]
    ws["F37"] = req_issued[0]
    ws["F39"] = req_issued[1]
    ws["H37"] = req_received[0]
    ws["H39"] = req_received[1]

    file = NamedTemporaryFile(suffix = ".xlsx", delete = False)

    try:
        with file as f:
            wb.save(f.name)
            f.seek(0)
            return f.read()
    finally:
        remove(file.name)

def form_69 (db, item):
    db.execute(f"SELECT * FROM item WHERE ItemID = '{item}'")
    data = db.fetchone()
    if data is None: raise ItemNotFoundError(item = item)

    db.execute(f"SELECT * FROM (SELECT RequestID, RequestDate, DeliveryStock, QuantityIssued, UPPER(CONCAT(FirstName, ' ', LastName)) as RequestedBy, Price FROM request_item INNER JOIN (SELECT ItemID, Price, COALESCE(SUM(IF(ShelfLife IS NULL OR DATEDIFF(CURDATE(), ADDDATE(DeliveryDate, ShelfLife)) <= 0, DeliveryQuantity, 0)), 0) AS DeliveryStock FROM item LEFT JOIN delivery USING (ItemID) GROUP BY ItemID) AS w USING (ItemID) INNER JOIN request USING (RequestID) INNER JOIN user ON RequestedBy = Username WHERE ItemID = '{item}' AND StatusID = 4 ORDER BY RequestID DESC LIMIT 30) AS x ORDER BY RequestID ASC")
    requests = db.fetchall()

    wb = load_workbook("./src/form_templates/template_69.xlsx", rich_text = True)
    ws = wb.active

    ws["B8"] = CellRichText(ws["B8"].value, TextBlock(InlineFont(b = True), data[1].upper()))
    ws["B10"] = CellRichText(ws["B10"].value, TextBlock(InlineFont(b = True), data[3]))
    ws["I9"] = CellRichText(ws["I9"].value, TextBlock(InlineFont(b = True), data[0]))

    for i in range(len(requests)):
        req = requests[i]

        ws[f"B{13 + i}"] = req[1]
        if i == 0: ws[f"D{13 + i}"] = req[2]
        ws[f"E{13 + i}"] = req[3]
        ws[f"F{13 + i}"] = req[4]
        ws[f"H{13 + i}"] = ws[f"D{13 + i}"].value - ws[f"E{13 + i}"].value if i == 0 else ws[f"H{12 + i}"].value - ws[f"E{13 + i}"].value
        ws[f"I{13 + i}"] = req[5]

    file = NamedTemporaryFile(suffix = ".xlsx", delete = False)

    try:
        with file as f:
            wb.save(f.name)
            f.seek(0)
            return f.read()
    finally:
        remove(file.name)

def form_71 (db, request):
    db.execute(f"SELECT * FROM request WHERE RequestID = {request}")
    if db.fetchone() is None: raise RequestNotFoundError(request = request)

    db.execute(f"SELECT COUNT(*) + 1 FROM request WHERE StatusID = 4 && hasPropertyApproved = 1 && RequestID < {request};")
    par_num = db.fetchone()[0]

    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) FROM request INNER JOIN user ON RequestedBy = Username WHERE RequestID = {request}")
    (req_by,) = db.fetchone()
    db.execute(f"SELECT UPPER(CONCAT(FirstName, ' ', LastName)) FROM request INNER JOIN user ON IssuedBy = Username WHERE RequestID = {request}")
    (iss_by,) = db.fetchone()
    db.execute(f"SELECT DateReceived, DateIssued FROM request WHERE RequestID = {request}")
    (date_rec, date_iss) = db.fetchone()

    db.execute(f"SELECT QuantityIssued, Unit, ItemDescription, ItemID, Price * QuantityIssued FROM request_item INNER JOIN stock USING (ItemID) INNER JOIN request USING (RequestID) WHERE RequestID = '{request}';")
    items = db.fetchall()

    if len(items) == 0: return None

    wb = load_workbook("./src/form_templates/template_71.xlsx", rich_text = True)
    ws = wb.active
    ws["F7"] = par_num

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
