# Copyright (C) 2026 JoaStuart
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
