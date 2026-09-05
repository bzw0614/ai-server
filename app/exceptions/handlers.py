
"""自定义业务异常。"""


class ServiceError(Exception):
    """业务错误基类，message 可直接返回给客户端。"""


class ValidationError(ServiceError):
    """参数校验失败。"""


class UserNotFoundError(ServiceError):
    """用户不存在。"""


class AuthenticationError(ServiceError):
    """鉴权失败。"""