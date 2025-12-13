def calc_position(balance, risk_percent=1):
    risk_amount = balance * (risk_percent / 100)
    price = 30000  # временно, потом возьмём реальную цену
    qty = round(risk_amount / price, 3)
    return max(qty, 0.001)
