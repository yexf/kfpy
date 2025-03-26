from src.gateway.qmt import QmtGateway
from src.util.utility import get_qmt_config, thread_hold
from src.event import EventEngine
from src.trader.constant import Exchange
from src.trader.event import EVENT_TICK
from src.trader.object import SubscribeRequest

if __name__ == '__main__':
    event_engine = EventEngine()
    qmt = QmtGateway(event_engine)
    # qmt.md.get_contract()
    qmt.subscribe(SubscribeRequest(symbol='000001', exchange=Exchange.SZSE))
    qmt.td.connect(get_qmt_config())
    # event_engine.register(EVENT_LOG, lambda event: print(event.data.level, event.data.msg))
    event_engine.register(EVENT_TICK, lambda event: print(event.data))
    event_engine.start()

    # qmt.send_order(OrderRequest(symbol='123115',
    #                             exchange=Exchange.SZSE,
    #                             direction=Direction.SHORT,
    #                             type=OrderType.LIMIT,
    #                             price=121.3,
    #                             volume=14800))

    thread_hold()
