from re import sub

def decode_keyword (k):
    return sub(r'%[0-9A-F]{2}', lambda x: chr(int(x.group(0)[1:3], base = 16)), k).replace("'", "\\'")


def escape (s):
    return sub(r'[\u2018\u2019\u201c\u201d]', lambda x: "\\'" if x.group(0) in ['\u201c', '\u201d'] else "\"", s)
