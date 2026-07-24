def cap(v):
    return None if v is None else ('10+' if v>10 else v)
def cap_str(v,d=0):
    if v is None:return 'unavailable'
    return '10+' if v>10 else f'{v:.{d}f}'
