def smart_levels(price, side):
    if side == "BUY":
        sl = price * 0.985
        tp = price * 1.03
    else:
        sl = price * 1.015
        tp = price * 0.97

    return round(sl, 4), round(tp, 4)
