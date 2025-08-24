from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, ForeignKey, insert, select
from sqlalchemy.orm import Session, DeclarativeBase
from typing import List
from typing import Optional
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import aliased
from sqlalchemy import func, desc, cast, literal_column, type_coerce, and_, or_, union_all, JSON
from sqlalchemy.dialects import postgresql, oracle, mysql
import json

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

with engine.connect() as conn:
    result = conn.execute(text("select 'hello world'"))
    print(result.all())

    conn.execute(text("CREATE TABLE some_table (x int, y int)"))
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 1, "y": 1}, {"x": 2, "y": 4}],
    )
    conn.commit()

with engine.begin() as conn2:  # cria a conexão e executa o commit automaticamente
    result = conn2.execute(text("SELECT x, y FROM some_table"))
    for row in result:
        print(f"x: {row.x}  y: {row.y}")

with engine.connect() as conn3:
    result = conn3.execute(text("SELECT x, y FROM some_table WHERE y > :y"), {"y": 2})
    for row in result:
        print(f"x: {row.x}  y: {row.y}")

stmt = text("SELECT x, y FROM some_table WHERE y > :y ORDER BY x, y")
with Session(engine) as session:
    result = session.execute(stmt, {"y": 3})
    for row in result:
        print(f"x: {row.x}  y: {row.y}")

with Session(engine) as session:
    result = session.execute(
        text("UPDATE some_table SET y=:y WHERE x=:x"),
        [{"x": 9, "y": 11}, {"x": 13, "y": 15}],
    )
    session.commit()


metadata_obj = MetaData()

user_table = Table(
    "user_account",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("name", String(30)),
    Column("fullname", String),
)

print(user_table.c.name)

print(user_table.c.keys())

print(user_table.primary_key)

address_table = Table(
    "address",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("user_account.id"), nullable=False),
    Column("email_address", String, nullable=False),
)

metadata_obj.create_all(engine)


class Base(DeclarativeBase):
    pass


print(Base.metadata)

print(Base.registry)


class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]
    addresses: Mapped[List["Address"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"


class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id = mapped_column(ForeignKey("user_account.id"))
    user: Mapped[User] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"


Base.metadata.create_all(engine)

stmt = insert(user_table).values(name="spongebob", fullname="Spongebob Squarepants")
print(stmt)
compiled = stmt.compile()
print(compiled.params)

with engine.connect() as conn:
    result = conn.execute(stmt)
    conn.commit()

    print(result.inserted_primary_key)

print(insert(user_table))

with engine.connect() as conn:
    result = conn.execute(
        insert(user_table),
        [
            {"name": "sandy", "fullname": "Sandy Cheeks"},
            {"name": "patrick", "fullname": "Patrick Star"},
        ],
    )
    conn.commit()

print(insert(user_table).values().compile(engine))


stmt = select(user_table).where(user_table.c.name == "spongebob")
print(stmt)

with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(row)

stmt = select(User).where(User.name == "spongebob")
print(stmt)

with Session(engine) as session:
    for row in session.execute(stmt):
        print(row)

print(select(user_table))

print(select(user_table.c.name, user_table.c.fullname))
print(select(user_table.c["name", "fullname"]))

print(select(User))
row = session.execute(select(User)).first()
print(row)

session.execute(
    select(User.name, Address).where(User.id == Address.user_id).order_by(Address.id)
).all()

stmt = select(
    ("Username: " + user_table.c.name).label("username"),
).order_by(user_table.c.name)
with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(f"{row.username}")

stmt = select(literal_column("'some phrase'").label("p"), user_table.c.name).order_by(
    user_table.c.name
)
with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(f"{row.p}, {row.name}")

print(user_table.c.name == "squidward")

print(address_table.c.user_id > 10)

print(select(user_table).where(user_table.c.name == "squidward"))

print(
    select(address_table.c.email_address)
    .where(user_table.c.name == "squidward")
    .where(address_table.c.user_id == user_table.c.id)
)

print(
    select(address_table.c.email_address).where(
        user_table.c.name == "squidward",
        address_table.c.user_id == user_table.c.id,
    )
)

print(
    select(Address.email_address).where(
        and_(
            or_(User.name == "squidward", User.name == "sandy"),
            Address.user_id == User.id,
        )
    )
)

print(
    select(Address.email_address).where(
        or_(
            User.name == "squidward",
            and_(Address.user_id == User.id, User.name == "sandy"),
        )
    )
)

print(select(User).filter_by(name="spongebob", fullname="Spongebob Squarepants"))

print(select(user_table.c.name, address_table.c.email_address))

print(
    select(user_table.c.name, address_table.c.email_address).join_from(
        user_table, address_table
    )
)

print(select(user_table.c.name, address_table.c.email_address).join(address_table))

print(select(address_table.c.email_address).select_from(user_table).join(address_table))


print(select(func.count("*")).select_from(user_table))

print(
    select(address_table.c.email_address)
    .select_from(user_table)
    .join(address_table, user_table.c.id == address_table.c.user_id)
)

print(select(user_table).join(address_table, isouter=True))
print(select(user_table).join(address_table, full=True))

print(select(user_table).order_by(user_table.c.name))
print(select(User).order_by(User.fullname.desc()))

with engine.connect() as conn:
    result = conn.execute(
        select(User.name, func.count(Address.id).label("count"))
        .join(Address)
        .group_by(User.name)
        .having(func.count(Address.id) > 1)
    )
    print(result.all())

stmt = (
    select(Address.user_id, func.count(Address.id).label("num_addresses"))
    .group_by("user_id")
    .order_by("user_id", desc("num_addresses"))
)
print(stmt)

user_alias_1 = user_table.alias()
user_alias_2 = user_table.alias()
print(
    select(user_alias_1.c.name, user_alias_2.c.name).join_from(
        user_alias_1, user_alias_2, user_alias_1.c.id > user_alias_2.c.id
    )
)

address_alias_1 = aliased(Address)
address_alias_2 = aliased(Address)
print(
    select(User)
    .join_from(User, address_alias_1)
    .where(address_alias_1.email_address == "patrick@aol.com")
    .join_from(User, address_alias_2)
    .where(address_alias_2.email_address == "patrick@gmail.com")
)

subq = (
    select(func.count(address_table.c.id).label("count"), address_table.c.user_id)
    .group_by(address_table.c.user_id)
    .subquery()
)

print(subq)

print(select(subq.c.user_id, subq.c.count))

stmt = select(user_table.c.name, user_table.c.fullname, subq.c.count).join_from(
    user_table, subq
)

print(stmt)

subq = (
    select(func.count(address_table.c.id).label("count"), address_table.c.user_id)
    .group_by(address_table.c.user_id)
    .cte()
)

stmt = select(user_table.c.name, user_table.c.fullname, subq.c.count).join_from(
    user_table, subq
)

print(stmt)

subq = select(Address).where(~Address.email_address.like("%@aol.com")).subquery()
address_subq = aliased(Address, subq)
stmt = (
    select(User, address_subq)
    .join_from(User, address_subq)
    .order_by(User.id, address_subq.id)
)
with Session(engine) as session:
    for user, address in session.execute(stmt):
        print(f"{user} {address}")

cte_obj = select(Address).where(~Address.email_address.like("%@aol.com")).cte()
address_cte = aliased(Address, cte_obj)
stmt = (
    select(User, address_cte)
    .join_from(User, address_cte)
    .order_by(User.id, address_cte.id)
)
with Session(engine) as session:
    for user, address in session.execute(stmt):
        print(f"{user} {address}")

subq = (
    select(func.count(address_table.c.id))
    .where(user_table.c.id == address_table.c.user_id)
    .scalar_subquery()
)
print(subq)
print(subq == 5)

subq = (
    select(func.count(address_table.c.id))
    .where(user_table.c.id == address_table.c.user_id)
    .scalar_subquery()
    .correlate(user_table)
)

with engine.connect() as conn:
    result = conn.execute(
        select(
            user_table.c.name,
            address_table.c.email_address,
            subq.label("address_count"),
        )
        .join_from(user_table, address_table)
        .order_by(user_table.c.id, address_table.c.id)
    )
    print(result.all())

subq = (
    select(
        func.count(address_table.c.id).label("address_count"),
        address_table.c.email_address,
        address_table.c.user_id,
    )
    .where(user_table.c.id == address_table.c.user_id)
    .lateral()
)
stmt = (
    select(user_table.c.name, subq.c.address_count, subq.c.email_address)
    .join_from(user_table, subq)
    .order_by(user_table.c.id, subq.c.email_address)
)
print(stmt)


stmt1 = select(user_table).where(user_table.c.name == "sandy")
stmt2 = select(user_table).where(user_table.c.name == "spongebob")
u = union_all(stmt1, stmt2)
with engine.connect() as conn:
    result = conn.execute(u)
    print(result.all())

u_subq = u.subquery()
stmt = (
    select(u_subq.c.name, address_table.c.email_address)
    .join_from(address_table, u_subq)
    .order_by(u_subq.c.name, address_table.c.email_address)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

stmt1 = select(User).where(User.name == "sandy")
stmt2 = select(User).where(User.name == "spongebob")
u = union_all(stmt1, stmt2)

orm_stmt = select(User).from_statement(u)
with Session(engine) as session:
    for obj in session.execute(orm_stmt).scalars():
        print(obj)

user_alias = aliased(User, u.subquery())
orm_stmt = select(user_alias).order_by(user_alias.id)
with Session(engine) as session:
    for obj in session.execute(orm_stmt).scalars():
        print(obj)

subq = (
    select(func.count(address_table.c.id))
    .where(user_table.c.id == address_table.c.user_id)
    .group_by(address_table.c.user_id)
    .having(func.count(address_table.c.id) > 1)
).exists()
with engine.connect() as conn:
    result = conn.execute(select(user_table.c.name).where(subq))
    print(result.all())

subq = (
    select(address_table.c.id).where(user_table.c.id == address_table.c.user_id)
).exists()
with engine.connect() as conn:
    result = conn.execute(select(user_table.c.name).where(~subq))
    print(result.all())

print(select(func.now()).compile(dialect=postgresql.dialect()))

print(select(func.now()).compile(dialect=oracle.dialect()))

# pre-configured SQL function (only a few dozen of these)
print(func.now().type)

# arbitrary SQL function (all other SQL functions)
print(func.run_some_calculation().type)

function_expr = func.json_object('{a, 1, b, "def", c, 3.5}', type_=JSON)
stmt = select(function_expr["def"])
print(stmt)

m1 = func.max(Column("some_int", Integer))
print(m1.type)

m2 = func.max(Column("some_str", String))
print(m2.type)

print(func.now().type)
print(func.current_date().type)

stmt = (
    select(
        func.row_number().over(partition_by=user_table.c.name),
        user_table.c.name,
        address_table.c.email_address,
    )
    .select_from(user_table)
    .join(address_table)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

stmt = (
    select(
        func.count().over(order_by=user_table.c.name),
        user_table.c.name,
        address_table.c.email_address,
    )
    .select_from(user_table)
    .join(address_table)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

print(
    func.unnest(
        func.percentile_disc([0.25, 0.5, 0.75, 1]).within_group(user_table.c.name)
    )
)

stmt = (
    select(
        func.count(address_table.c.email_address).filter(user_table.c.name == "sandy"),
        func.count(address_table.c.email_address).filter(
            user_table.c.name == "spongebob"
        ),
    )
    .select_from(user_table)
    .join(address_table)
)
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.all())

onetwothree = func.json_each('["one", "two", "three"]').table_valued("value")
stmt = select(onetwothree).where(onetwothree.c.value.in_(["two", "three"]))
with engine.connect() as conn:
    result = conn.execute(stmt)
    result.all()

stmt = select(func.scalar_strings(5).column_valued("s"))
print(stmt.compile(dialect=oracle.dialect()))

stmt = select(cast(user_table.c.id, String))
with engine.connect() as conn:
    result = conn.execute(stmt)
    result.all()

s = select(type_coerce({"some_key": {"foo": "bar"}}, JSON)["some_key"])
print(s.compile(dialect=mysql.dialect()))
