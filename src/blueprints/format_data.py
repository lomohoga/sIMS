from flask import session
import locale

locale.setlocale(locale.LC_ALL, 'en_PH.utf8')

def format_items (items):
    return [
        {
            "ItemID": item[0],
            "ItemName": item[1],
            "Category": item[2] if item[2] is not None else "\u2014",
            "ItemDescription": item[3],
            "ShelfLife": locale.format_string("%d", item[4], grouping = True) if item[4] != None else "\u2014",
            "Price": locale.currency(item[5], grouping = True),
            "AvailableStock": locale.format_string("%d", item[6], grouping = True) if session["user"]["RoleID"] != 2 else None,
            "Unit": item[7]
        } for item in items
    ]

def format_requests (requests, custodian = True):
    grouped = []

    for req in requests:
        if len(list(filter(lambda x: x['RequestID'] == req[0], grouped))) == 0:
            grouped.append({
                "RequestID": req[0],
                "RequestedBy": req[1],
                "RequestDate": req[2],
                "Status": req[3],
                "Purpose": req[4],
                "Items": []
            })
            
        z = list(filter(lambda x: x['RequestID'] == req[0], grouped))[0]
        o = {
            "ItemID": req[5],
            "ItemName": req[6],
            "Category": req[7] if req[7] is not None else '\u2014',
            "ItemDescription": req[8],
            "RequestQuantity": locale.format_string("%d", req[9], grouping = True),
            "QuantityIssued": locale.format_string("%d", req[10], grouping = True) if req[10] is not None else '\u2014',
            "AvailableStock": locale.format_string("%d", req[11], grouping = True) if session["user"]["RoleID"] != 2 else None,
            "Unit": req[12],
            "Remarks": req[13],
        }

        z['Items'].append(o)

    if not custodian:
        for g in grouped: g.pop("RequestedBy")

    return grouped

def format_deliveries (deliveries):
    return [
        {
            "DeliveryID": d[0],
            "ItemID": d[1],
            "ItemName": d[2],
            "ItemDescription": d[3],
            "DeliveryQuantity": locale.format_string("%d", d[4], grouping = True),
            "Unit": d[5],
            "ShelfLife": locale.format_string("%d", d[6], grouping = True) if d[6] is not None else "\u2014",
            "DeliveryDate": d[7],
            "Source": d[8],
            "ReceivedBy": d[9],
            "IsExpired": bool(d[10]),
            "Supplier": d[11]
        } for d in deliveries
    ]

def format_categories (categories):
    return [
        {
            "CategoryName": d[0],
            "CategoryDescription": d[1]
        } for d in categories
    ]
