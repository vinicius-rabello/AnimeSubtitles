import os
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine


def sqlite_connector(db_name: str) -> Engine:
    if ".db" not in db_name:
        db_name += ".db"
    db_path = os.path.realpath(f'database/{db_name}')
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    # print(type(engine))
    return engine
