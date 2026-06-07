from database.settings import settings

CURRENCY_SYMBOL = settings.currency_symbol()
DATE_FORMAT = settings.date_format()


def curr(amount, decimals=2):
    if amount is None:
        amount = 0
    if decimals == 0:
        return f"{CURRENCY_SYMBOL}{amount:,.0f}"
    return f"{CURRENCY_SYMBOL}{amount:,.{decimals}f}"


def curr_label(text, amount=0, decimals=2):
    return f"{text}: {curr(amount, decimals)}"


CURRENCY_SYMBOL_RAW = CURRENCY_SYMBOL
