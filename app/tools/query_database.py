"""

@Time :  
@Author : 4ever
@File : .py

"""
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql.expression import select

from app.model.user import User

async def get_user_by_name(db: AsyncSession, username: str):
    """按用户名模糊匹配。

    参数名用 username 而不是 name：和 DATABASE_TOOL 里声明的 properties
    保持一致，模型传来的关键字才能对上号
    （否则就是 unexpected keyword argument 'username'）。
    没有匹配时返回空列表而不是 None —— 接口用 response_model=List[...] 时
    返回 None 会校验失败，交给模型时 None 也不如 [] 好理解。
    """
    stmt = select(User).where(User.name.like("%" + username + "%"))
    # 返回的是一个 ScalarResult,不需要await
    result = await db.scalars(stmt)
    return result.all()
