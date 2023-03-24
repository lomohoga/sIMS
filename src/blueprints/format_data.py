import locale

locale.setlocale(locale.LC_ALL, 'en_PH.utf8')

def format_items (items):
    return [
        {
            "ItemID": item[0],
            "ItemName": item[1],
            "ItemDescription": item[2],
            "ShelfLife": locale.format("%s", item[3], grouping = True) if item[3] != None else "\u2014",
            "Price": locale.currency(item[4], grouping = True),
            "AvailableStock": locale.format("%s", item[5], grouping = True),
            "Unit": item[6]
        } for item in items
    ]

def format_requests (requests, custodian = True):
    print(requests)
    return [
        {
            "RequestID": req[0],
            "ItemID": req[1],
            "ItemName": req[2],
            "ItemDescription": req[3],
            "RequestedBy": req[4],
            "RequestQuantity": locale.format("%s", req[5], grouping = True),
            "Unit": req[6],
            "RequestDate": req[7],
            "Status": req[8]
        } if custodian
        else {
            "RequestID": req[0],
            "ItemID": req[1],
            "ItemName": req[2],
            "ItemDescription": req[3],
            "RequestQuantity": locale.format("%s", req[5], grouping = True),
            "Unit": req[6],
            "RequestDate": req[7],
            "Status": req[8]
        } for req in requests
    ]


def format_deliveries (deliveries):
    return [
        {
            "DeliveryID": d[0],
            "ItemID": d[1],
            "ItemName": d[2],
            "ItemDescription": d[3],
            "DeliveryQuantity": locale.format("%s", d[4], grouping = True),
            "Unit": d[5],
            "ShelfLife": locale.format("%s", d[6], grouping = True) if d[6] is not None else "\u2014",
            "DeliveryDate": d[7],
            "ReceivedBy": d[8],
            "IsExpired": bool(d[9])
        } for d in deliveries
    ]
