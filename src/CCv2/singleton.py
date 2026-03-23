from typing import Callable, TypeVar, cast


_T = TypeVar("_T")


def singleton(cls: type[_T]) -> type[_T]:
    """A singleton decorator for classes

    Args:
        cls (Type[_T]): The class being decorated

    Returns:
        Callable[..., _T]: The callable for initializing the class
    """

    # Store the instances of the class
    instances: dict[type, _T] = {}

    # The function that will be called to get the instance
    def get_instance(*args, **kwargs) -> _T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return cast(type[_T], get_instance)
