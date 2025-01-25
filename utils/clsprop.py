from collections.abc import Callable


class classproperty[T]:  # noqa: N801
    def __init__(self, fget: Callable[[], T]):
        self.fget = fget
        self.result = None

    def __get__(self, obj, owner):
        return self.fget()
