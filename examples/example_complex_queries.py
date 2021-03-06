import asyncio
import aioodbc

from functools import partial


dsn = 'Driver=SQLite3;Database=sqlite.db'


# Sometimes you may want to reuse same connection parameters multiple times.
# This can be accomplished in a way below using partial function
connect = partial(aioodbc.connect, dsn=dsn, echo=True, autocommit=True)


async def test_init_database(loop=None):
    """
    Initialize test database with sample schema/data to reuse in other tests.
    Make sure that in real applications you have database initialization
    file as separate *.sql script or rely on autogenerated code provided
    by your ORM.
    """
    async with connect(loop=loop) as conn:
        async with conn.cursor() as cur:
            sql = 'CREATE TABLE IF NOT EXISTS t1(n INTEGER, v TEXT);'
            await cur.execute(sql)


async def test_error_without_context_managers(loop=None):
    """
    When not using context manager you may end up having unclosed connections
    in case of any error which lead to resource leakage. To avoid
    `Unclosed connection` errors in your code always close after yourself.
    """
    conn = await aioodbc.connect(dsn=dsn, loop=loop)
    cur = await conn.cursor()

    try:
        await cur.execute("SELECT 42 AS;")
        rows = await cur.fetchall()
        print(rows)
    except:
        pass
    finally:
        await cur.close()
        await conn.close()


async def test_insert_with_values(loop=None):
    """
    When providing data to your SQL statement make sure to parametrize it with
    question marks placeholders. Do not use string formatting or make sure
    your data is escaped to prevent sql injections.

    NOTE: pyodbc does not support named placeholders syntax.
    """
    async with connect(loop=loop) as conn:
        async with conn.cursor() as cur:
            # Substitute sql markers with variables
            await cur.execute('INSERT INTO t1(n, v) VALUES(?, ?);',
                              ('2', 'test 2'))
            # NOTE: make sure to pass variables as tuple of strings even if
            # your data types are different to prevent
            # pyodbc.ProgrammingError errors. You can even do like this
            values = (3, 'test 3')
            await cur.execute('INSERT INTO t1(n, v) VALUES(?, ?);',
                              *map(str, values))

            # Retrieve id of last inserted row
            await cur.execute('SELECT last_insert_rowid();')
            result = await cur.fetchone()
            print(result[0])


async def test_commit(loop=None):
    """
    When not using `autocommit` parameter do not forget to explicitly call
    this method for your changes to persist within database.
    """
    async with aioodbc.connect(dsn=dsn, loop=loop) as conn:
        async with conn.cursor() as cur:
            sql = 'INSERT INTO t1 VALUES(1, "test");'
            await cur.execute(sql)
            # Make sure your changes will be actually saved into database
            await cur.commit()

    async with aioodbc.connect(dsn=dsn, loop=loop) as conn:
        async with conn.cursor() as cur:
            sql_select = 'SELECT * FROM t1;'
            await cur.execute(sql_select)
            # At this point without autocommiting you will not see
            # the data inserted above
            print(await cur.fetchone())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_init_database(loop))
    loop.run_until_complete(test_commit(loop))
    loop.run_until_complete(test_insert_with_values(loop))
    loop.run_until_complete(test_error_without_context_managers(loop))
