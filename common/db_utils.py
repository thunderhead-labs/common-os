import enum
import json
from contextlib import contextmanager
from itertools import chain
from os import environ
from typing import List

import psycopg2
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


# Basic


class PostgresInterface(enum.Enum):
    SQLALCHEMY_ENGINE = 0
    PSYCOPG2_DRIVER = 1


INTERFACE: PostgresInterface = PostgresInterface.SQLALCHEMY_ENGINE


class ConnFactory:
    """
    You need to setup a directory with all your creds to dbs
    and add this directory to path with name creds_dir
    Functions get the file name but it has a default that
    you can see at method signature.
    """

    env: str = environ.get("env") if environ.get("env") is not None else "dev"
    creds_directory: str = (
        f"{environ.get('creds_dir')}/{env}/"
        if environ.get("creds_dir") is not None
        else f"/{env}/"
    )

    @staticmethod
    def switch_env(env: str):
        ConnFactory.env = env
        ConnFactory.creds_directory = f"{environ.get('creds_dir')}/{env}/"

    @staticmethod
    def get_file_path(file_name: str = "db_creds.json") -> str:
        return f"{ConnFactory.creds_directory}{file_name}"

    @staticmethod
    def get_engine(content: dict) -> sqlalchemy.engine.Engine:
        engine = create_engine(
            f"postgresql://{content['user']}:{content['password']}@{content['host']}:{content['port']}/{content['database']}",
            pool_size=10,
            max_overflow=10,
            # The combination of lifo connection picking and pre-ping options should increase
            # the re-use of already-open connections while disconnecting stale connections gracefully
            pool_pre_ping=True,
            pool_use_lifo=True,
        )
        return engine

    @staticmethod
    def get_session(content: dict) -> sqlalchemy.orm.session.Session:
        engine = ConnFactory.get_engine(content)
        session = Session(engine, autocommit=True)
        return session

    @staticmethod
    def connect(
        file_path: str = "db_creds.json",
        interface_type: PostgresInterface = PostgresInterface.SQLALCHEMY_ENGINE,
    ):
        """
        Retrieves credentials from file_path and connects to db
        :param file_path:
        :return: conn to db
        """
        content = json.load(open(file_path))
        # establishing the connection
        if interface_type == PostgresInterface.SQLALCHEMY_ENGINE:
            engine = ConnFactory.get_engine(content)
            session = Session(engine, autocommit=True)
            session.begin()
            return session
        elif interface_type == PostgresInterface.PSYCOPG2_DRIVER:
            conn = psycopg2.connect(
                database=content["database"],
                user=content["user"],
                password=content["password"],
                host=content["host"],
                port=content["port"],
            )
            # auto commits to avoid calling commit every time
            conn.autocommit = True
            return conn
        return None

    @staticmethod
    def _yield_conn(
        file_name: str,
        interface_type: PostgresInterface = None,
    ):
        conn = None
        file_path = f"{ConnFactory.creds_directory}{file_name}"
        try:
            conn = ConnFactory.connect(
                file_path=file_path,
                interface_type=INTERFACE if interface_type is None else interface_type,
            )
            yield conn
        finally:
            if conn is not None:
                try:
                    conn.commit()
                except Exception:
                    conn.rollback()
                conn.close()

    @staticmethod
    @contextmanager
    def db_conn(file_name="db_creds.json", interface_type: PostgresInterface = None):
        yield from ConnFactory._yield_conn(file_name, interface_type=interface_type)

    @staticmethod
    @contextmanager
    def poktinfo_conn(
        file_name="poktinfo_creds.json", interface_type: PostgresInterface = None
    ):
        yield from ConnFactory._yield_conn(file_name, interface_type=interface_type)

    @staticmethod
    @contextmanager
    def latency_conn(
        file_name="latency_creds.json", interface_type: PostgresInterface = None
    ):
        yield from ConnFactory._yield_conn(file_name, interface_type=interface_type)

    @staticmethod
    @contextmanager
    def errors_conn(
        file_name="errors_creds.json", interface_type: PostgresInterface = None
    ):
        yield from ConnFactory._yield_conn(file_name, interface_type=interface_type)

    # Used to choose what interface to use for the connection
    @staticmethod
    def use_sqlalchemy():
        global INTERFACE
        INTERFACE = PostgresInterface.SQLALCHEMY_ENGINE

    @staticmethod
    def use_psycopg2():
        global INTERFACE
        INTERFACE = PostgresInterface.PSYCOPG2_DRIVER

    @staticmethod
    def get_interface():
        return INTERFACE


def execute_stmt(conn, stmt: str):
    cursor = conn.cursor()
    try:
        cursor.execute(stmt)
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        cursor.close()


def add_price_entry(conn, coin, currency, price, height):
    delete_stmt = f"""DELETE FROM public.coin_prices WHERE
 coin = '{coin}' AND height = {height}"""
    execute_stmt(conn, delete_stmt)
    insert_stmt = f"""INSERT INTO public.coin_prices(coin, vs_currency, price, height)
 VALUES ('{coin}', '{currency}', {price}, {height})"""
    return execute_stmt(conn, insert_stmt)


def fetch_all(conn, select_stmt: str):
    cursor = conn.cursor()
    try:
        cursor.execute(select_stmt)
        result = cursor.fetchall()
        return list(chain.from_iterable(result))
    except Exception as e:
        print(e)
        return []
    finally:
        cursor.close()


def fetch_all_raw(conn, select_stmt: str):
    cursor = conn.cursor()
    try:
        cursor.execute(select_stmt)
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(e)
        return []
    finally:
        cursor.close()


def get_latency_dict(conn, from_height: int, to_height: int):
    select_stmt = f"""SELECT * FROM public.cherry_picker_session_region
 WHERE session_height > {from_height} AND session_height <= {to_height}"""
    return fetch_all_raw(conn, select_stmt)


def get_latency_cache_dict(
    conn, from_height: int, to_height: int, addresses: List[str]
):
    if len(addresses):
        addresses_stmt = (
            f"IN {tuple(addresses)}" if len(addresses) > 1 else f"= '{addresses[0]}'"
        )
        select_stmt = f"""SELECT * FROM public.latency_cache
     WHERE start_height >= {from_height} AND end_height <= {to_height}
     AND address {addresses_stmt}"""
        return fetch_all_raw(conn, select_stmt)
