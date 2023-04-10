# Installation

To install the package

    pip install git+https://github.com/thunderhead-labs/common-os

If you get an error while installing the package, try doing this first.

    sudo apt install python3-dev libpq-dev


Create a folder named creds_dir that contains a folder for each env (eg: prod, stg),
and each folder contains config.json files such as poktinfo_creds.json that contain credentials to a db in this format:

    {
      "database": "name",
      "user": "user",
      "password": "password",
      "host": "host",
      "port": port
    }

As a rule of thumb each func by default will look for file with same name that ends in creds:
poktinfo_conn -> poktinfo_creds.json but can be overriden by passing a different file name to the function.

    from common.db import ConnFactory

    with ConnFactory.db_conn(file_name="db_creds.json") as conn:
        # do stuff with conn

db_conn is a non specific function that will look for a file with the name of the db passed in.

### Linux/Mac
Set env variables for env, creds_dir in .bashrc file for each user so its easier to segregate envs
### Windows
Set env variables for env, creds_dir in system env variables for each user so its easier to segregate envs

## Optional

#### Utils
In `common/utils.py` you need to update the next params:<br />
`MAINNET_URL` - Valid mainnet node or a default node of your choosing<br />
`VALID_URLS` - List of default nodes to use<br />
`USERNAME`, `PASSWORD` - If your nodes require authentication update these as well

#### IP API
In `common/ip_api_utils.py` please specify your api key in `API_KEY=<api_key>`


# Usage

Import the package you need, for example:

#### ORM package -
Contains schema and models for the poktinfo db as well as queries interacting with the db.

Used for retrieving and saving data to the db using ORM (SQLAlchemy),
makes interacting with data layer simpler more organized and manageable from code.

    from common.db_utils import ConnFactory
    from common.orm.repository import PoktInfoRepository
    from common.orm.schema.poktinfo import *

    # Create schema
    engine = ConnFactory.get_engine(json.load(open(f'{ConnFactory.creds_directory}poktinfo_creds.json')))
    PoktInfoBase.metadata.create_all(engine)

    # Use orm.repository to interact with the db with predefined queries from PoktinfoRepository.

    with ConnFactory.poktinfo_conn() as session:
        node_count = PoktInfoRepository.get_node_count(
            session, from_height, to_height, addresses
        )

    # or use the session directly and create any query you like

    with Session() as session:
        session.query(<model>).all()

    # or

    with Session() as session:
        session.query(<model>).filter(<model>.<column> == <value>).all()

    # or

    with Session() as session:
        session.query(<model>).filter(<model>.<column> == <value>).filter(<model>.<column> == <value>).all()

    # or

    with Session() as session:
        session.query(<model>).filter(<model>.<column> == <value>).filter(<model>.<column> == <value>).filter(<model>.<column> == <value>).all()

    # or

    with Session() as session:
        session.query(<model>).filter(<model>.<column> == <value>).filter(<model>.<column> == <value>).filter(<model>.<column> == <value>).filter(<model>.<column> == <value>).all()

#### db_utils.py -
Contains utility to connect and interact with dbs

    from common.db_utils import ConnFactory

    # Get connection to db
    with ConnFactory.poktinfo_conn() as session:
        session.query(<model>).all()

You can switch envs with `ConnFactory.switch_env('stg')` or `ConnFactory.switch_env('prod')`<br />
And you can switch between SQLAlchemy and Postgres with `ConnFactory.use_sqlalchemy()` or `ConnFactory.use_psycopg2()`<br />
Additionally, there are predefined functions to connect to various dbs like `ConnFactory.poktinfo_conn()` or `ConnFactory.latency_conn()` as well as custom connections with `ConnFactory.db_conn()`<br />

#### utils.py -
Contains utility functions to interact with the pokt api

        from common.utils import get_node_info

        # Get node info
        node_info = get_node_info(address)

#### ip_api_utils.py -
Contains utility functions to interact with ip-api.com

        from common.ip_api_utils import get_location_info

        # Get location info
        location_info = get_location_info('google.com')

#### price_utils.py -
Contains utility functions to interact with the coinmarketcap api

Define available cryptocurrencies in `COINS_MAP` and use `get_price` to get the price of a currency now against a different currency.

    from common.price_utils import get_price

    # Get price of POKT in USD
    price = get_price('pokt', 'usd')

You can also get historical prices with `get_historical_price`

    from common.price_utils import get_historical_price

    # Get price of POKT in USD on 2020-01-01
    price = get_historical_price('pokt', 'usd', '2020-01-01')


#### loggers.py -
Contains utility functions to interact with the loggers

Loggers are standardized with environment and service separation

    from common.loggers import get_logger

    # Get logger
    path = os.path.dirname(os.path.realpath(__file__))
    service_name = "poktinfo"
    logger = get_logger(path, service_name, f"{service_name}_{get_blocks_interval()}")

# Context Managers

@contextmanager decorator.

    Typical usage:

        @contextmanager
        def some_generator(<arguments>):
            <setup>
            try:
                yield <value>
            finally:
                <cleanup>

    This makes this:

        with some_generator(<arguments>) as <variable>:
            <body>

    equivalent to this:

        <setup>
        try:
            <variable> = <value>
            <body>
        finally:
            <cleanup>

# ConnFactory
Context manager for creating and closing connections.

    Typical usage:

        with ConnFactory.conntype() as conn:
            <body>

    To make this work, you need to add 2 env vars:
    env (dev/stg/prod) and creds_dir (path to credentials dir).
