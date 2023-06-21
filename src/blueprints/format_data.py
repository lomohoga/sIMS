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
            "AvailableStock": locale.format_string("%d", item[6], grouping = True),
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
                "Remarks": req[5],
                "Items": []
            })
        
        z = list(filter(lambda x: x['RequestID'] == req[0], grouped))[0]
        o = {
            "ItemID": req[6],
            "ItemName": req[7],
            "Category": req[8] if req[8] is not None else '\u2014',
            "ItemDescription": req[9],
            "RequestQuantity": locale.format_string("%d", req[10], grouping = True),
            "QuantityIssued": locale.format_string("%d", req[11], grouping = True) if req[11] is not None else '\u2014',
            "AvailableStock": locale.format_string("%d", req[12], grouping = True),
            "Unit": req[13],
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
            "ReceivedBy": d[8],
            "IsExpired": bool(d[9])
        } for d in deliveries
    ]

def format_categories (categories):
    return [
        {
            "CategoryName": d[0],
            "CategoryDescription": d[1]
        } for d in categories
    ]
