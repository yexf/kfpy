"""
Event type string used in the trading platform.
"""

from src.event import  Event, EventEngine, EVENT_TIMER  # noqa

EVENT_TICK = "eTick."
EVENT_TRADE = "eTrade."
EVENT_ORDER = "eOrder."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_QUOTE = "eQuote."
EVENT_CONTRACT = "eContract."
EVENT_LOG = "eLog"

