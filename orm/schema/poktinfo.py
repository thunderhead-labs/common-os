from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    TEXT,
    TIMESTAMP,
    Boolean,
    func,
)
from sqlalchemy.orm import as_declarative

from common.orm.schema.base import Base


@as_declarative()
class PoktInfoBase(Base):
    pass


class CacheSet(PoktInfoBase):
    __tablename__ = "cache_set"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, default=0)
    set_name = Column(String(255), nullable=False, index=True)
    is_public = Column(Boolean, nullable=False, default=True)
    is_internal = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    def __str__(self):
        return f"{self.set_name = }, {self.is_public = }, {self.is_internal = }, {self.is_active = }"


class CacheSetNode(PoktInfoBase):
    __tablename__ = "cache_set_node"

    cache_set_id = Column(Integer, ForeignKey(CacheSet.id), primary_key=True)
    address = Column(String(255), nullable=False, primary_key=True)
    start_height = Column(Integer, nullable=False)
    end_height = Column(Integer, nullable=True)

    def __str__(self):
        return f"{self.cache_set_id = }, {self.address = }"


class CacheSetStateRangeEntry(PoktInfoBase):
    __tablename__ = "cache_set_state_range_entry"

    cache_set_id = Column(
        Integer, ForeignKey(CacheSet.id), primary_key=True, index=True
    )
    service = Column(String(255), primary_key=True, nullable=False)
    start_height = Column(Integer, primary_key=True, nullable=False)
    end_height = Column(Integer, primary_key=True, nullable=False)
    status = Column(String(255), nullable=False, index=True)
    interval = Column(Integer, primary_key=True, nullable=False)

    def __str__(self):
        return f"{self.cache_set_id = }, {self.service = }, {self.start_height = }, {self.end_height = }, {self.status = }, {self.interval = }"


class CoinPrices(PoktInfoBase):
    __tablename__ = "coin_prices"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    coin = Column(String(255), nullable=False, index=True)
    vs_currency = Column(String(255), nullable=False, index=True)
    price = Column(Float, nullable=False)
    height = Column(Integer, nullable=False, index=True)

    def __str__(self):
        return (
            f"{self.coin = }, {self.vs_currency = }, {self.price = }, {self.height = }"
        )


class ErrorsCache(PoktInfoBase):
    __tablename__ = "errors_cache"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=False, index=True)
    address = Column(String(255), nullable=False, index=True)
    chain = Column(String(255), nullable=False, index=True)
    errors_count = Column(Integer, nullable=False)
    error_type = Column(String(255), nullable=False, index=True)
    msg = Column(TEXT, nullable=False, index=True)
    date_created = Column(TIMESTAMP, nullable=False, default=func.now())

    def __str__(self):
        return f"{self.start_height = }, {self.end_height = }, {self.address = }, {self.chain = }, {self.errors_count = }, {self.error_type = }, {self.msg = }, {self.date_created = }"


class ErrorsCacheSet(PoktInfoBase):
    __tablename__ = "errors_cache_set"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    cache_set_id = Column(Integer, ForeignKey(CacheSet.id), index=True)
    chain = Column(String(255), nullable=False, index=True)
    errors_count = Column(Integer, nullable=False)
    msg = Column(TEXT, nullable=False, index=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=False, index=True)
    interval = Column(Integer, nullable=False, index=True)

    def __str__(self):
        return f"{self.cache_set_id = }, {self.chain = }, {self.errors_count = }, {self.msg = }, {self.start_height = }, {self.end_height = }, {self.interval = }"


class LatencyCache(PoktInfoBase):
    __tablename__ = "latency_cache"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    address = Column(String(255), nullable=False, index=True)
    chain = Column(String(255), nullable=False, index=True)
    total_relays = Column(Integer, nullable=False)
    region = Column(String(255), nullable=False, index=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=False, index=True)
    avg_latency = Column(Float, nullable=False)
    avg_p90_latency = Column(Float, nullable=False)
    avg_weighted_latency = Column(Float, nullable=False)

    def __str__(self):
        return f"{self.address = }, {self.chain = }, {self.total_relays = }, {self.region = }, {self.start_height = }, {self.end_height = }, {self.avg_latency = }, {self.avg_p90_latency = }, {self.avg_weighted_latency = }"


class LatencyCacheSet(PoktInfoBase):
    __tablename__ = "latency_cache_set"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    cache_set_id = Column(Integer, ForeignKey(CacheSet.id), index=True)
    chain = Column(String(255), nullable=False, index=True)
    total_relays = Column(Integer, nullable=False)
    region = Column(String(255), nullable=False, index=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=False, index=True)
    avg_latency = Column(Float, nullable=False)
    avg_p90_latency = Column(Float, nullable=False)
    avg_weighted_latency = Column(Float, nullable=False)
    interval = Column(Integer, nullable=False, index=True)

    def __str__(self):
        return f"{self.cache_set_id = }, {self.chain = }, {self.total_relays = }, {self.region = }, {self.start_height = }, {self.end_height = }, {self.avg_latency = }, {self.avg_p90_latency = }, {self.avg_weighted_latency = }, {self.interval = }"


class LocationInfo(PoktInfoBase):
    __tablename__ = "location_info"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    address = Column(String(255), nullable=False, index=True)
    ip = Column(String(255), nullable=False, index=True)
    height = Column(Integer, nullable=False, index=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=True, index=True)
    city = Column(String(255), nullable=False, index=True)
    continent = Column(String(255), nullable=False)
    country = Column(String(255), nullable=False)
    region = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    isp = Column(String(255), nullable=False)
    org = Column(String(255), nullable=False)
    as_ = Column(String(255), nullable=False)
    date_created = Column(TIMESTAMP, nullable=False, default=func.now())
    ran_from = Column(String(255), nullable=True)

    def __str__(self):
        return f"{self.address = }, {self.ip = }, {self.height = }, {self.start_height = }, {self.end_height = }, {self.city = }, {self.continent = }, {self.country = }, {self.region = }, {self.lat = }, {self.lon = }, {self.isp = }, {self.org = }, {self.as_ = }, {self.date_created = }"


class LocationCacheSet(PoktInfoBase):
    __tablename__ = "location_cache_set"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    cache_set_id = Column(Integer, ForeignKey(CacheSet.id), index=True)
    node_count = Column(Integer, nullable=False)
    continent = Column(String(255), nullable=False, index=True)
    country = Column(String(255), nullable=False, index=True)
    city = Column(String(255), nullable=False, index=True)
    ip = Column(String(255), nullable=False, index=True)
    isp = Column(String(255), nullable=False, index=True)
    lat = Column(Float, nullable=False, index=True)
    lon = Column(Float, nullable=False, index=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=False, index=True)
    interval = Column(Integer, nullable=False, index=True)

    def __str__(self):
        return f"{self.cache_set_id = }, {self.node_count = }, {self.region = }, {self.start_height = }, {self.end_height = }, {self.interval = }"


class NodeCountCacheSet(PoktInfoBase):
    __tablename__ = "node_count_cache_set"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    cache_set_id = Column(Integer, ForeignKey(CacheSet.id), index=True)
    node_count = Column(Integer, nullable=False)
    chain = Column(String(255), nullable=True, index=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=False, index=True)
    interval = Column(Integer, nullable=False, index=True)

    def __str__(self):
        return f"{self.cache_set_id = }, {self.node_count = }, {self.start_height = }, {self.end_height = }, {self.interval = }"


class NodesInfo(PoktInfoBase):
    __tablename__ = "nodes_info"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    address = Column(String(255), nullable=False, index=True)
    url = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    subdomain = Column(String(255), nullable=False)
    chains = Column(String(510), nullable=False, index=True)
    height = Column(Integer, nullable=False, index=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=True, index=True)
    is_staked = Column(Boolean, nullable=False)
    date_created = Column(TIMESTAMP, nullable=False, default=func.now())

    def __str__(self):
        return f"{self.address = }, {self.url = }, {self.domain = }, {self.subdomain = }, {self.height = }, {self.start_height = }, {self.end_height = }, {self.is_staked = }, {self.date_created = }"


class RewardsInfo(PoktInfoBase):
    __tablename__ = "rewards_info"

    tx_hash = Column(String(255), primary_key=True, unique=True)
    height = Column(Integer, nullable=False, index=True)
    address = Column(String(255), nullable=False, index=True)
    rewards = Column(Float, nullable=False)
    chain = Column(String(255), nullable=False, index=True)
    relays = Column(Integer, nullable=False)
    token_multiplier = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    stake_weight = Column(Float, nullable=False)

    def __str__(self):
        return f"{self.tx_hash = }, {self.height = }, {self.address = }, {self.rewards = }, {self.chain = }, {self.relays = }, {self.token_multiplier = }, {self.percentage = }, {self.stake_weight = }"


class RewardsCacheSet(PoktInfoBase):
    __tablename__ = "rewards_cache_set"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    cache_set_id = Column(Integer, ForeignKey(CacheSet.id), index=True)
    rewards_total = Column(Float, nullable=False)
    normalized_rewards_total = Column(Float, nullable=True)
    relays_total = Column(Integer, nullable=False)
    chain = Column(String(255), nullable=False, index=True)
    start_height = Column(Integer, nullable=False, index=True)
    end_height = Column(Integer, nullable=False, index=True)
    interval = Column(Integer, nullable=False, index=True)

    def __str__(self):
        return f"{self.cache_set_id = }, {self.rewards_total = }, {self.relays_total = }, {self.chain = }, {self.start_height = }, {self.end_height = }, {self.interval = }"


class ServicesState(PoktInfoBase):
    __tablename__ = "services_state"

    service = Column(String(255), primary_key=True, nullable=False)
    height = Column(Integer, primary_key=True, nullable=False)
    status = Column(String(255), nullable=False, index=True)

    def __str__(self):
        return f"{self.service = }, {self.height = }, {self.status = }"


class ServicesStateRange(PoktInfoBase):
    __tablename__ = "services_state_range"

    service = Column(String(255), primary_key=True, nullable=False)
    start_height = Column(Integer, primary_key=True, nullable=False)
    end_height = Column(Integer, primary_key=True, nullable=False)
    status = Column(String(255), nullable=False, index=True)

    def __str__(self):
        return f"{self.service = }, {self.start_height = }, {self.end_height = }, {self.status = }"
