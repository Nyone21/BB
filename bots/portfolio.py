def select_symbols(balance):
    symbols = []

    if balance >= 5:
        symbols.append("BTCUSDT")

    if balance >= 10:
        symbols.append("ETHUSDT")

    if balance >= 15:
        symbols.append("SOLUSDT")

    if balance >= 20:
        symbols.append("BNBUSDT")

    return symbols
