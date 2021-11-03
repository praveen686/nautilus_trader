# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2021 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

from decimal import Decimal
from typing import Dict, List, Tuple

from nautilus_trader.adapters.binance.common import BINANCE_VENUE
from nautilus_trader.adapters.binance.data_types import BinanceBar
from nautilus_trader.adapters.binance.data_types import BinanceTicker
from nautilus_trader.core.datetime import millis_to_nanos
from nautilus_trader.model.data.bar import BarSpecification
from nautilus_trader.model.data.bar import BarType
from nautilus_trader.model.data.tick import QuoteTick
from nautilus_trader.model.data.tick import TradeTick
from nautilus_trader.model.enums import AggregationSource
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.enums import BarAggregation
from nautilus_trader.model.enums import BookAction
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orderbook.data import Order
from nautilus_trader.model.orderbook.data import OrderBookDelta
from nautilus_trader.model.orderbook.data import OrderBookDeltas


def parse_diff_depth_stream_ws(msg: Dict, symbol: Symbol, ts_init: int) -> OrderBookDeltas:
    inst_id = InstrumentId(symbol, venue=BINANCE_VENUE)
    ts_event: int = millis_to_nanos(msg["E"])

    bid_deltas = [
        parse_order_book_delta_ws(inst_id, OrderSide.BUY, d, ts_event, ts_init)
        for d in msg.get("b")
    ]
    ask_deltas = [
        parse_order_book_delta_ws(inst_id, OrderSide.SELL, d, ts_event, ts_init)
        for d in msg.get("a")
    ]

    return OrderBookDeltas(
        instrument_id=inst_id,
        book_type=BookType.L2_MBP,
        deltas=bid_deltas + ask_deltas,
        ts_event=ts_event,
        ts_init=ts_init,
    )


def parse_order_book_delta_ws(
    instrument_id: InstrumentId,
    side: OrderSide,
    delta: Tuple[str, str],
    ts_event: int,
    ts_init: int,
) -> OrderBookDelta:
    price = float(delta[0])
    size = float(delta[1])

    order = Order(
        price=price,
        size=size,
        side=side,
    )

    return OrderBookDelta(
        instrument_id=instrument_id,
        book_type=BookType.L2_MBP,
        action=BookAction.UPDATE if size > 0.0 else BookAction.DELETE,
        order=order,
        ts_event=ts_event,
        ts_init=ts_init,
    )


def parse_ticker_ws(msg: Dict, symbol: Symbol, ts_init: int):
    return BinanceTicker(
        instrument_id=InstrumentId(symbol, venue=BINANCE_VENUE),
        price_change=Decimal(msg["p"]),
        price_change_percent=Decimal(msg["P"]),
        weighted_avg_price=Decimal(msg["w"]),
        prev_close_price=Decimal(msg["x"]),
        last_price=Decimal(msg["c"]),
        last_qty=Decimal(msg["Q"]),
        bid_price=Decimal(msg["b"]),
        ask_price=Decimal(msg["a"]),
        open_price=Decimal(msg["o"]),
        high_price=Decimal(msg["h"]),
        low_price=Decimal(msg["l"]),
        volume=Decimal(msg["v"]),
        quote_volume=Decimal(msg["q"]),
        open_time_ms=msg["O"],
        close_time_ms=msg["C"],
        first_id=msg["F"],
        last_id=msg["L"],
        count=msg["n"],
        ts_event=millis_to_nanos(msg["E"]),
        ts_init=ts_init,
    )


def parse_quote_tick_ws(msg: Dict, symbol: Symbol, ts_init: int):
    return QuoteTick(
        instrument_id=InstrumentId(symbol, venue=BINANCE_VENUE),
        bid=Price.from_str(msg["b"]),
        ask=Price.from_str(msg["a"]),
        bid_size=Quantity.from_str(msg["B"]),
        ask_size=Quantity.from_str(msg["B"]),
        ts_event=ts_init,
        ts_init=ts_init,
    )


def parse_trade_tick(msg: Dict, instrument_id: InstrumentId, ts_init: int):
    return TradeTick(
        instrument_id=instrument_id,
        price=Price.from_str(msg["price"]),
        size=Quantity.from_str(msg["qty"]),
        aggressor_side=AggressorSide.SELL if msg["isBuyerMaker"] else AggressorSide.BUY,
        match_id=str(msg["id"]),
        ts_event=millis_to_nanos(msg["time"]),
        ts_init=ts_init,
    )


def parse_trade_tick_ws(msg: Dict, symbol: Symbol, ts_init: int):
    return TradeTick(
        instrument_id=InstrumentId(symbol, venue=BINANCE_VENUE),
        price=Price.from_str(msg["p"]),
        size=Quantity.from_str(msg["q"]),
        aggressor_side=AggressorSide.SELL if msg["m"] else AggressorSide.BUY,
        match_id=str(msg["t"]),
        ts_event=millis_to_nanos(msg["T"]),
        ts_init=ts_init,
    )


def parse_bar(bar_type: BarType, values: List, ts_init: int):
    return BinanceBar(
        bar_type=bar_type,
        open=Price.from_str(values[1]),
        high=Price.from_str(values[2]),
        low=Price.from_str(values[3]),
        close=Price.from_str(values[4]),
        volume=Quantity.from_str(values[5]),
        quote_volume=Quantity.from_str(values[7]),
        count=values[8],
        taker_buy_base_volume=Quantity.from_str(values[9]),
        taker_buy_quote_volume=Quantity.from_str(values[10]),
        ts_event=millis_to_nanos(values[0]),
        ts_init=ts_init,
    )


def parse_bar_ws(msg: Dict, kline: Dict, ts_init: int):
    interval = kline["i"]
    resolution = interval[1]
    if resolution == "m":
        aggregation = BarAggregation.MINUTE
    elif resolution == "h":
        aggregation = BarAggregation.HOUR
    elif resolution == "d":
        aggregation = BarAggregation.DAY
    else:  # pragma: no cover (design-time error)
        raise RuntimeError(f"unsupported time aggregation resolution, was {resolution}")

    bar_spec = BarSpecification(
        step=int(interval[0]),
        aggregation=aggregation,
        price_type=PriceType.LAST,
    )

    bar_type = BarType(
        instrument_id=InstrumentId(Symbol(kline["s"]), venue=BINANCE_VENUE),
        bar_spec=bar_spec,
        aggregation_source=AggregationSource.EXTERNAL,
    )

    return BinanceBar(
        bar_type=bar_type,
        open=Price.from_str(kline["o"]),
        high=Price.from_str(kline["h"]),
        low=Price.from_str(kline["l"]),
        close=Price.from_str(kline["c"]),
        volume=Quantity.from_str(kline["v"]),
        quote_volume=Quantity.from_str(kline["q"]),
        count=kline["n"],
        taker_buy_base_volume=Quantity.from_str(kline["V"]),
        taker_buy_quote_volume=Quantity.from_str(kline["Q"]),
        ts_event=millis_to_nanos(msg["E"]),
        ts_init=ts_init,
    )
