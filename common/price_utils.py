import typing
from time import sleep

import pandas as pd
import pycoingecko

from common.db_utils import ConnFactory, add_price_entry
from common.orm.repository import PoktInfoRepository
from common.orm.schema import CoinPrices
from common.utils import get_block_height_at_timestamp

cg = pycoingecko.CoinGeckoAPI()

COINS_MAP = {
    "eth": "ethereum",
    "pokt": "pocket-network",
}


def get_price(coin: str, currency: str) -> float:
    price = cg.get_price(ids=coin, vs_currencies=currency)
    return price[coin][currency]


def get_historical_price(coin: str, currency: str, date: str) -> float:
    """date format is dd-mm-yyyy"""
    price = cg.get_coin_history_by_id(id=coin, date=date, vs_currencies=currency)
    if "market_data" in price:
        return price["market_data"]["current_price"][currency]
    return -1


def get_historical_prices(
    coin: str, currency: str, from_date: str, to_date: str
) -> typing.MutableMapping[str, float]:
    prices_dict = {}

    dates = pd.Series(pd.date_range(from_date, to_date)).dt.strftime("%d-%m-%Y")
    for date in dates:
        try:
            price = get_historical_price(coin, currency, date)
            if price > 0:
                prices_dict[date] = price
            print(date, price)
        except Exception as e:
            print(f"Failed getting price for {coin} at {date}, {e}")
        sleep(3)
    return prices_dict


def record_pocket_price(coin: str, currency: str, height: int) -> bool:
    price = get_price(COINS_MAP[coin], currency)
    with ConnFactory.poktinfo_conn() as session:
        return PoktInfoRepository.save(
            session,
            CoinPrices(coin=coin, vs_currency=currency, price=price, height=height),
        )


def record_historical_pocket_prices(
    coin: str, currency: str, from_date: str, to_date: str
) -> None:
    prices_dict = get_historical_prices(COINS_MAP[coin], currency, from_date, to_date)

    with ConnFactory.poktinfo_conn() as conn:
        for date in prices_dict:
            price = prices_dict[date]
            height = get_block_height_at_timestamp(pd.Timestamp(date, tz="UTC"))
            has_added = add_price_entry(conn, coin, currency, price, height)
            if not has_added:
                print(f"Failed adding price entry for {coin} at {date}")
