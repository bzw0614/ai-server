"""

@Time :  
@Author : 4ever
@File : .py

"""
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column


class Base(DeclarativeBase):
    pass

class User(Base):
    # 这里的变量名称要和数据库完全一致，一个都不能错，要不然报错
    __tablename__ = "user"
    id :Mapped[int] = mapped_column(primary_key=True)
    name :Mapped[str] = mapped_column(index = True)
    age :Mapped[int] = mapped_column()
    email :Mapped[str] = mapped_column()
    create_time:Mapped[datetime] = mapped_column(server_default=func.now())