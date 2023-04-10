import ast
import hashlib
import json
import random
import typing
from multiprocessing import Pool

import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
import hexbytes
import pandas as pd
import requests
from cryptography.hazmat.primitives import serialization
from tenacity import retry, stop_after_attempt

POKT_MULTIPLIER = 1000000
MAINNET_URL = ""
VALID_URLS = []
USERNAME, PASSWORD = "", ""
AUTH = (USERNAME, PASSWORD)


def get_url(main=False):
    if main:
        return f"{MAINNET_URL}v1/query/"
    rand_int = random.randint(0, len(VALID_URLS) - 1)
    return f"{VALID_URLS[rand_int]}v1/query/"


def get_valid_urls():
    return VALID_URLS


def set_valid_urls(urls: typing.List[str]):
    global VALID_URLS
    VALID_URLS = urls


def validate_url(i, last_height):
    base_url = f"http://node{i}.thunderstake.io/"
    try:
        height = get_last_block_height(f"{base_url}v1/query/")
        if last_height >= height and last_height - height < 3:
            return base_url
    except Exception as e:
        print(e)
    return None


def generate_valid_urls(from_node: int = 1700, to_node: int = 1995):
    """
    Get all urls of nodes that are within 3 blocks of
    the latest height that we get from portal api
    """
    global VALID_URLS
    url = get_url(True)
    last_height = get_last_block_height(url)
    with Pool(processes=8) as tp:
        node_range = range(from_node, to_node)
        result = tp.starmap_async(validate_url, [(i, last_height) for i in node_range])
        for value in result.get():
            if value:
                VALID_URLS.append(value)


@retry(stop=stop_after_attempt(5))
def get_supply(height):
    url = get_url()
    supply_req = requests.post(
        url=url + "supply/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"height": height}),
        timeout=15,
        auth=AUTH,
    )
    supply = supply_req.json()
    total_supply = int(supply["total"])

    return total_supply


@retry(stop=stop_after_attempt(5))
def balance(address, height):
    url = get_url()
    account_txs = requests.post(
        url=url + "balance/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"address": address, "height": height}),
        timeout=15,
        auth=AUTH,
    )
    bal = account_txs.json()
    bal = int(bal["balance"])

    return bal


def node_balance(address, height):
    node_info = get_node_info(address, height)

    if "code" in node_info.keys():
        return 0
    t = int(node_info["tokens"])
    return t


def get_output_address(address, height):
    node_info = get_node_info(address, height)

    if "code" in node_info.keys():
        return address
    output_address = (
        node_info["output_address"]
        if "output_address" in node_info.keys() and node_info["output_address"] != ""
        else address
    )
    return output_address


@retry(stop=stop_after_attempt(5))
def get_node_info(address: str, height: int):
    url = get_url()
    req = requests.post(
        url=url + "node/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"address": address, "height": height}),
        timeout=15,
        auth=AUTH,
    )
    resp = req.json()
    return resp


@retry(stop=stop_after_attempt(5))
def get_block(height: int):
    """
    :param height:
    :return: dict, information at block height
    """
    url = get_url()
    block_req = requests.post(
        url=url + "block/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"height": height}),
        timeout=15,
        auth=AUTH,
    )
    return block_req.json()


@retry(stop=stop_after_attempt(5))
def get_last_block(url=None):
    """
    :return: dict, last POKT block information
    """
    if url is None:
        url = get_url()
    last_block_req = requests.post(
        url=url + "height/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        timeout=15,
        auth=AUTH,
    )
    return last_block_req.json()


def get_block_height(height: int):
    block = get_block(height)
    return block["block_height"]


def get_block_ts(height: int):
    """
    Returns timestamp of block height
    :param height:
    :return: pd.Timestamp
    """
    block = get_block(height)
    return pd.Timestamp(block["block"]["header"]["time"], tz="utc")


def get_last_block_height(url=None):
    last_block = get_last_block(url=url)
    return last_block["height"]


def get_block_height_at_timestamp(ts: pd.Timestamp):
    """
    Binary searches for closest height to ts
    :param ts:
    :return: int
    """
    last = get_last_block_height()
    first = 42052
    mid = 0
    while first <= last:
        mid = (last + first) // 2
        block_ts = get_block_ts(mid)
        if ts > block_ts:
            first = mid + 1
        else:
            last = mid - 1
        if block_ts == ts:
            return mid
    return mid


def get_date_to_height_map(dates: pd.DatetimeIndex) -> typing.MutableMapping[str, int]:
    date_to_height_map = {}
    for date in dates:
        date_to_height_map[str(date)[:10]] = get_block_height_at_timestamp(date)
    return date_to_height_map


@retry(stop=stop_after_attempt(5))
def get_all_params(height: int):
    """
    Returns the relay to token multiplier
    :param height:
    :return: float
    """
    url = get_url()
    param_req = requests.post(
        url=url + "allparams/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"height": height}),
        auth=AUTH,
    )

    return param_req.json()


@retry(stop=stop_after_attempt(5))
def get_param(height: int, key: str):
    url = get_url()
    param_req = requests.post(
        url=url + "param/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"height": height, "key": key}),
        auth=AUTH,
    )
    return param_req.json()["param_value"]


@retry(stop=stop_after_attempt(5))
def get_pip22_height(height: int):
    try:
        url = get_url()
        param_req = requests.post(
            url=url + "param/",
            headers={
                "Content-Type": "application/json",
                "Accept": "Accept: application/json",
            },
            data=json.dumps({"height": height, "key": "gov/upgrade"}),
            auth=AUTH,
        )
        features = ast.literal_eval(param_req.json()["param_value"])["value"][
            "Features"
        ]
        for feature in features:
            if "RSCAL" in feature:
                return int(feature.split(":")[1])
    except Exception:
        return 69232
    finally:
        return 69232


@retry(stop=stop_after_attempt(5))
def get_dao_allocation(height: int):
    url = get_url()
    param_req = requests.post(
        url=url + "param/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"height": height, "key": "pos/DAOAllocation"}),
        auth=AUTH,
    )
    return float(param_req.json()["param_value"])


@retry(stop=stop_after_attempt(5))
def get_proposer_percentage(height: int):
    url = get_url()
    param_req = requests.post(
        url=url + "param/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"height": height, "key": "pos/ProposerPercentage"}),
        auth=AUTH,
    )
    return float(param_req.json()["param_value"])


def get_reward_percentage(height: int):
    dao_allocation = get_dao_allocation(height)
    proposer_percentage = get_proposer_percentage(height)
    return 1 - (dao_allocation + proposer_percentage) / 100


@retry(stop=stop_after_attempt(5))
def get_relay_to_tokens_multiplier(height: int):
    """
    Returns the relay to token multiplier
    :param height:
    :return: float
    """
    url = get_url()
    param_req = requests.post(
        url=url + "param/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps({"height": height, "key": "pos/RelaysToTokensMultiplier"}),
        auth=AUTH,
    )
    return float(param_req.json()["param_value"])


@retry(stop=stop_after_attempt(5))
def get_txs(height: int):
    txs, new_txs = [], []
    i = 1
    while (new_txs is not None and len(new_txs)) or i == 1:
        url = get_url()
        txs_req = requests.post(
            url=url + "blocktxs/",
            headers={
                "Content-Type": "application/json",
                "Accept": "Accept: application/json",
            },
            data=json.dumps({"height": height, "page": i, "per_page": 50000}),
            auth=AUTH,
        )
        new_txs = txs_req.json()["txs"]
        if new_txs is not None and len(new_txs):
            txs += new_txs
        i += 1
    return txs


@retry(stop=stop_after_attempt(5))
def get_claims(height: int, address: str = ""):
    url = get_url()
    claims_req = requests.post(
        url=url + "nodeclaims/",
        headers={
            "Content-Type": "application/json",
            "Accept": "Accept: application/json",
        },
        data=json.dumps(
            {"height": height, "page": 1, "per_page": 50000, "address": address}
        ),
        auth=AUTH,
    )
    total_pages = claims_req.json()["total_pages"]
    claims = claims_req.json()["result"]
    for i in range(2, total_pages + 1):
        url = get_url()
        claims_req = requests.post(
            url=url + "nodeclaims/",
            headers={
                "Content-Type": "application/json",
                "Accept": "Accept: application/json",
            },
            data=json.dumps(
                {"height": height, "page": i, "per_page": 50000, "address": address}
            ),
            auth=AUTH,
        )
        new_claims = claims_req.json()["result"]
        if new_claims is not None and len(new_claims):
            claims += new_claims
    return claims


@retry(stop=stop_after_attempt(5))
def get_account_txs(height: int, address: str = ""):
    txs, new_txs = [], []
    i = 1
    while (new_txs is not None and len(new_txs)) or i == 1:
        url = get_url()
        txs_req = requests.post(
            url=url + "accounttxs/",
            headers={
                "Content-Type": "application/json",
                "Accept": "Accept: application/json",
            },
            data=json.dumps(
                {"address": address, "height": height, "page": i, "per_page": 50000}
            ),
            auth=AUTH,
        )
        new_txs = txs_req.json()["txs"]
        if new_txs is not None and len(new_txs):
            txs += new_txs
        i += 1
    return txs


@retry(stop=stop_after_attempt(5))
def get_nodes(height: int):
    nodes, new_nodes = [], []
    i = 1
    while (new_nodes is not None and len(new_nodes)) or i == 1:
        url = get_url()
        nodes_req = requests.post(
            url=url + "nodes/",
            headers={
                "Content-Type": "application/json",
                "Accept": "Accept: application/json",
            },
            data=json.dumps({"height": height, "opts": {"page": i, "per_page": 50000}}),
            auth=AUTH,
        )
        new_nodes = nodes_req.json()["result"]
        if new_nodes is not None and len(new_nodes):
            nodes += new_nodes
        i += 1
    return nodes


def get_inflation(height: int):
    return get_supply(height) - get_supply(height - 1)


def get_address_from_pubkey(pubkey: str):
    """
    Converts public key to address
    :param pubkey: public key of address
    :return: str
    """
    return hashlib.sha256(bytes.fromhex(pubkey)).hexdigest().lower()[:40]


def validate_private_key(private_key: str, address: str):
    priv_key = hexbytes.HexBytes(private_key)
    b = ed25519.Ed25519PrivateKey.from_private_bytes(priv_key[:32])
    p = b.public_key()
    hex_public_key = p.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    ).hex()
    from_pk_address = get_address_from_pubkey(hex_public_key)
    return address == from_pk_address
