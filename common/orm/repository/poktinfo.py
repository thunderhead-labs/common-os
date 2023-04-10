import itertools
import typing

from sqlalchemy import and_, func, or_, true
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from .base import AbstractRepository
from ..schema import (
    CacheSet,
    CacheSetNode,
    PoktInfoBase,
    RewardsInfo,
    NodesInfo,
    ErrorsCache,
    LatencyCache,
    ServicesState,
    ServicesStateRange,
    CacheSetStateRangeEntry,
    LocationInfo,
)
from ...utils import get_param


class PoktInfoRepository(AbstractRepository):
    @staticmethod
    def get_cache_sets(session: Session) -> typing.List[CacheSet]:
        return session.query(CacheSet).all()

    @staticmethod
    def get_cache_set_by_user_id_set_name(
        session: Session,
        user_id: int,
        set_name: str,
    ) -> CacheSet:
        try:
            query = session.query(CacheSet).filter(
                and_(CacheSet.user_id == user_id, CacheSet.set_name == set_name)
            )
            return query.one()
        except NoResultFound:
            raise KeyError(
                f'Cache set with "{user_id = }", "{set_name = }" could not be found'
            )

    @staticmethod
    def get_cache_sets_by_id(
        session: Session,
        cache_set_id: int,
    ) -> CacheSet:
        try:
            query = session.query(CacheSet).filter(CacheSet.id == cache_set_id)
            return query.one()
        except NoResultFound:
            raise KeyError(f'Cache set with id "{cache_set_id}" could not be found')

    @staticmethod
    def get_cache_set_nodes_by_id(
        session: Session,
        cache_set_id: int,
        height: int = None,
    ) -> typing.List[CacheSetNode]:
        query = session.query(CacheSetNode).filter(
            and_(
                CacheSetNode.cache_set_id == cache_set_id,
                CacheSetNode.end_height.is_(None),
                CacheSetNode.start_height <= height if height else true(),
            )
        )
        return query.all()

    @staticmethod
    def get_cache_set_addresses(
        session: Session,
        cache_set_id: int,
        height: int = None,
    ) -> typing.List[str]:
        nodes = PoktInfoRepository.get_cache_set_nodes_by_id(
            session, cache_set_id, height=height
        )
        return [node.address for node in nodes]

    @staticmethod
    def get_addresses_by_domain(
        session: Session,
        domain: str,
    ) -> typing.List[str]:
        domain = domain if domain != "pokt network" else ""
        query = (
            session.query(NodesInfo.address)
            .filter(
                and_(
                    NodesInfo.domain.like(f"%{domain}%"),
                    NodesInfo.end_height.is_(None),
                    NodesInfo.is_staked.is_(True),
                )
            )
            .distinct()
        )
        return list(itertools.chain(*query.all()))

    @staticmethod
    def get_last_recorded_service_height(
        session: Session,
        service_class: typing.Type[PoktInfoBase],
        is_range: bool = False,
        cache_set_id: int = None,
        interval: int = 4,
    ) -> int:
        try:
            if is_range:
                if cache_set_id:
                    query = session.query(func.max(service_class.end_height)).filter(
                        and_(
                            service_class.cache_set_id == cache_set_id,
                            service_class.interval == interval,
                        )
                    )
                else:
                    query = session.query(func.max(service_class.end_height))
            else:
                query = session.query(func.max(service_class.height))
            return query.one()[0]
        except NoResultFound:
            raise KeyError(f'Max height of "{service_class}" could not be found')

    @staticmethod
    def get_last_recorded_reward_height(session: Session) -> int:
        return PoktInfoRepository.get_last_recorded_service_height(session, RewardsInfo)

    @staticmethod
    def get_last_recorded_node_height(session: Session) -> int:
        return PoktInfoRepository.get_last_recorded_service_height(session, NodesInfo)

    @staticmethod
    def get_last_recorded_errors_height(session: Session) -> int:
        return PoktInfoRepository.get_last_recorded_service_height(
            session, ErrorsCache, is_range=True
        )

    @staticmethod
    def get_last_recorded_latency_height(session: Session) -> int:
        return PoktInfoRepository.get_last_recorded_service_height(
            session, LatencyCache, is_range=True
        )

    @staticmethod
    def get_failed_blocks_of_service(
        session: Session, service_class: typing.Type[PoktInfoBase]
    ) -> typing.List[int]:
        query = session.query(ServicesState.height).filter(
            and_(
                ServicesStateRange.service == service_class.__tablename__,
                ServicesState.status == "fail",
            )
        )
        return list(itertools.chain(*query.all()))

    @staticmethod
    def get_failed_ranges_of_service(
        session: Session, service_class: typing.Type[PoktInfoBase]
    ) -> typing.List[int]:
        query = session.query(ServicesStateRange).filter(
            and_(
                ServicesStateRange.service == service_class.__tablename__,
                ServicesStateRange.status == "fail",
            )
        )
        return list(itertools.chain(*query.all()))

    @staticmethod
    def get_failed_ranges_of_cache_set_service(
        session: Session,
        service_class: typing.Type[PoktInfoBase],
        cache_set_id: int,
        interval: int = 4,
    ) -> typing.List[int]:
        query = session.query(CacheSetStateRangeEntry).filter(
            and_(
                CacheSetStateRangeEntry.service == service_class.__tablename__,
                CacheSetStateRangeEntry.status == "fail",
                CacheSetStateRangeEntry.cache_set_id == cache_set_id,
                CacheSetStateRangeEntry.interval == interval,
            )
        )
        return list(itertools.chain(*query.all()))

    @staticmethod
    def get_all_active_nodes(
        session: Session, prefix: typing.Optional[str] = None
    ) -> typing.List[NodesInfo]:
        query = session.query(NodesInfo).filter(
            and_(
                NodesInfo.end_height.is_(None),
                NodesInfo.address.startswith(prefix) if prefix else true(),
            ),
        )
        return query.all()

    @staticmethod
    def get_open_locations(
        session: Session,
        prefix: typing.Optional[str] = None,
        ran_from: typing.Optional[str] = None,
    ) -> typing.List[LocationInfo]:
        query = session.query(LocationInfo).filter(
            and_(
                LocationInfo.end_height.is_(None),
                LocationInfo.address.startswith(prefix) if prefix else true(),
                LocationInfo.ran_from == ran_from if ran_from else true(),
            ),
        )
        return query.all()

    @staticmethod
    def get_rewards_total(
        session: Session,
        from_height: int,
        to_height: int,
        addresses: typing.List[str],
        chain: str = None,
    ) -> float:
        try:
            query = session.query(func.sum(RewardsInfo.rewards)).filter(
                and_(
                    RewardsInfo.height > from_height,
                    RewardsInfo.height <= to_height,
                    RewardsInfo.address.in_(addresses),
                    RewardsInfo.chain == chain if chain is not None else true(),
                ),
            )
            return query.one()[0]
        except NoResultFound:
            raise KeyError(
                f'Couldnt find rewards for addresses "{addresses}" between "{from_height}" and "{to_height}"'
            )

    @staticmethod
    def get_rewards_total_per15k(
        session: Session,
        from_height: int,
        to_height: int,
        addresses: typing.List[str],
        chain: str = None,
    ) -> float:
        try:
            servicer_stake_weight_multiplier = float(
                get_param(to_height, "pos/ServicerStakeWeightMultiplier")
            )
            min_weight = 1 / servicer_stake_weight_multiplier
            query = session.query(
                func.sum(RewardsInfo.rewards / RewardsInfo.stake_weight * min_weight)
            ).filter(
                and_(
                    RewardsInfo.height > from_height,
                    RewardsInfo.height <= to_height,
                    RewardsInfo.address.in_(addresses),
                    RewardsInfo.chain == chain if chain is not None else true(),
                ),
            )
            return query.one()[0]
        except NoResultFound:
            raise KeyError(
                f'Couldnt find rewards for addresses "{addresses}" between "{from_height}" and "{to_height}"'
            )

    @staticmethod
    def get_relays_total(
        session: Session,
        from_height: int,
        to_height: int,
        addresses: typing.List[str],
        chain: str = None,
    ) -> float:
        try:
            query = session.query(func.sum(RewardsInfo.relays)).filter(
                and_(
                    RewardsInfo.height > from_height,
                    RewardsInfo.height <= to_height,
                    RewardsInfo.address.in_(addresses),
                    RewardsInfo.chain == chain if chain is not None else true(),
                ),
            )
            return query.one()[0]
        except NoResultFound:
            raise KeyError(
                f'Couldnt find relays for addresses "{addresses}" between "{from_height}" and "{to_height}"'
            )

    @staticmethod
    def get_latency_cache(
        session: Session, from_height: int, to_height: int, addresses: typing.List[str]
    ) -> typing.List[LatencyCache]:
        query = session.query(LatencyCache).filter(
            and_(
                LatencyCache.start_height >= from_height,
                LatencyCache.end_height <= to_height,
                LatencyCache.address.in_(addresses),
            ),
        )
        return query.all()

    @staticmethod
    def get_rewards_info(
        session: Session, from_height: int, to_height: int, addresses: typing.List[str]
    ) -> typing.List[RewardsInfo]:
        query = session.query(RewardsInfo).filter(
            and_(
                RewardsInfo.height > from_height,
                RewardsInfo.height <= to_height,
                RewardsInfo.address.in_(addresses),
            ),
        )
        return query.all()

    @staticmethod
    def get_locations_dict(session: Session, addresses: typing.List[str]):
        query = session.query(LocationInfo).filter(
            and_(LocationInfo.address.in_(addresses), LocationInfo.end_height.is_(None))
        )
        return query.all()

    @staticmethod
    def get_node_count(
        session: Session,
        from_height: int,
        to_height: int,
        addresses: typing.List[str],
        chain: str = None,
    ) -> int:
        return (
            session.query(NodesInfo)
            .filter(
                and_(
                    NodesInfo.start_height <= from_height,
                    or_(
                        NodesInfo.end_height >= to_height,
                        NodesInfo.end_height.is_(None),
                    ),
                    NodesInfo.address.in_(addresses),
                    NodesInfo.chains.like(f"%{chain}%")
                    if chain is not None
                    else true(),
                )
            )
            .count()
        )

    @staticmethod
    def get_errors_dict(
        session: Session, from_height: int, to_height: int, addresses: typing.List[str]
    ) -> typing.List[typing.Tuple[typing.Any, ...]]:
        query = (
            session.query(
                func.sum(ErrorsCache.errors_count), ErrorsCache.chain, ErrorsCache.msg
            )
            .filter(
                and_(
                    ErrorsCache.start_height >= from_height,
                    ErrorsCache.end_height <= to_height,
                    ErrorsCache.address.in_(addresses),
                ),
            )
            .group_by(ErrorsCache.chain, ErrorsCache.msg)
        )
        return query.all()

    @staticmethod
    def has_url_changed(session: Session, address: str, url: str) -> bool:
        """
        Check if url has changed for address since latest entry by height
        """
        try:
            subquery = (
                session.query(func.max(NodesInfo.height))
                .filter(NodesInfo.address == address)
                .scalar_subquery()
            )
            query = session.query(NodesInfo.url).filter(
                and_(NodesInfo.address == address, NodesInfo.height == subquery)
            )
            result = query.one()[0]
            return result != url
        except NoResultFound:
            return False

    @staticmethod
    def has_chain_changed(
        session: Session, address: str, chains: typing.List[str]
    ) -> bool:
        """
        Check if url has changed for address since latest entry by height
        """
        try:
            subquery = (
                session.query(func.max(NodesInfo.height))
                .filter(NodesInfo.address == address)
                .scalar_subquery()
            )
            query = session.query(NodesInfo.chains).filter(
                and_(NodesInfo.address == address, NodesInfo.height == subquery)
            )
            result = query.one()[0]
            return len(chains) != len(result) or any(
                chain not in result for chain in chains
            )
        except NoResultFound:
            return False

    @staticmethod
    def has_location_changed(
        session: Session,
        address: str,
        city: str,
        ip: str,
        isp: str,
        ran_from: typing.Optional[str] = None,
    ) -> bool:
        """
        Check if city has changed for address since latest entry by height
        """
        try:
            subquery = (
                session.query(func.max(LocationInfo.height))
                .filter(LocationInfo.address == address)
                .scalar_subquery()
            )
            query = session.query(LocationInfo).filter(
                and_(
                    LocationInfo.address == address,
                    LocationInfo.ran_from == ran_from if ran_from else true(),
                    LocationInfo.height == subquery,
                )
            )
            result = query.one()
            return result.city != city or result.ip != ip or result.isp != isp
        except NoResultFound:
            return False

    @staticmethod
    def is_node_recorded(session: Session, address: str) -> bool:
        return (
            session.query(NodesInfo)
            .filter(and_(NodesInfo.address == address, NodesInfo.is_staked.is_(True)))
            .count()
            > 0
        )

    @staticmethod
    def is_height_recorded(session: Session, service_name: str, height: int) -> bool:
        return (
            session.query(ServicesState)
            .filter(
                and_(
                    ServicesState.service == service_name,
                    ServicesState.height == height,
                    ServicesState.status == "success",
                )
            )
            .count()
            > 0
        )

    @staticmethod
    def is_height_range_recorded(
        session: Session, service_name: str, start_height: int, end_height: int
    ) -> bool:
        return (
            session.query(ServicesStateRange)
            .filter(
                and_(
                    ServicesStateRange.service == service_name,
                    ServicesStateRange.start_height == start_height,
                    ServicesStateRange.end_height == end_height,
                    ServicesStateRange.status == "success",
                )
            )
            .count()
            > 0
        )

    @staticmethod
    def is_cache_set_height_range_recorded(
        session: Session,
        service_name: str,
        start_height: int,
        end_height: int,
        cache_set_id: int,
        interval: int,
    ) -> bool:
        return (
            session.query(ServicesStateRange)
            .filter(
                and_(
                    ServicesStateRange.service == service_name,
                    ServicesStateRange.start_height == start_height,
                    ServicesStateRange.end_height == end_height,
                    ServicesStateRange.cache_set_id == cache_set_id,
                    ServicesStateRange.interval == interval,
                    ServicesStateRange.status == "success",
                )
            )
            .count()
            > 0
        )

    @staticmethod
    def is_location_recorded(
        session: Session, address: str, ran_from: typing.Optional[str] = None
    ) -> bool:
        return (
            session.query(LocationInfo)
            .filter(
                and_(
                    LocationInfo.address == address,
                    LocationInfo.end_height.is_(None),
                    LocationInfo.ran_from == ran_from if ran_from else true(),
                )
            )
            .count()
            > 0
        )

    @staticmethod
    def does_height_exist(
        session: Session, end_height: int, table: type(PoktInfoBase), is_range=False
    ) -> bool:
        return (
            session.query(table)
            .filter(
                table.end_height == end_height
                if is_range
                else table.height == end_height,
            )
            .count()
            > 0
        )

    @staticmethod
    def update_node_end_height(
        session: Session, address: str, end_height: int, is_staked: bool = True
    ) -> bool:
        """
        Update end height of latest entry by height for address
        """
        try:
            subquery = (
                session.query(func.max(NodesInfo.height))
                .filter(NodesInfo.address == address)
                .scalar_subquery()
            )
            query = session.query(NodesInfo).filter(
                and_(NodesInfo.address == address, NodesInfo.height == subquery)
            )
            query.update(
                {"end_height": end_height, "is_staked": is_staked},
                synchronize_session=False,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def update_location(
        session: Session,
        address: str,
        end_height: int,
        ran_from: typing.Optional[str] = None,
    ) -> bool:
        """
        Update end height and city of latest entry by height for address
        """
        try:
            subquery = (
                session.query(func.max(LocationInfo.height))
                .filter(LocationInfo.address == address)
                .scalar_subquery()
            )
            query = session.query(LocationInfo).filter(
                and_(
                    LocationInfo.address == address,
                    LocationInfo.height == subquery,
                    LocationInfo.ran_from == ran_from if ran_from else true(),
                )
            )
            query.update({"end_height": end_height}, synchronize_session=False)
            return True
        except Exception:
            return False

    @staticmethod
    def rename_cache_set(session: Session, cache_set_id: id, new_set_name: str) -> None:
        """
        Rename cache set
        """
        session.query(CacheSet).filter(CacheSet.id == cache_set_id).update(
            {"set_name": new_set_name}, synchronize_session=False
        )

    @staticmethod
    def update_cache_set_nodes(
        session: Session, cache_set_id: int, addresses: typing.List[str], height
    ) -> None:
        try:
            query = session.query(CacheSetNode).filter(
                and_(
                    CacheSetNode.cache_set_id == cache_set_id,
                    CacheSetNode.address.in_(addresses),
                )
            )
            query.update({"end_height": height}, synchronize_session=False)
            return True
        except Exception:
            return False
