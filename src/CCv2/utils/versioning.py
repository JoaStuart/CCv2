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

import abc
import math
import types
from typing import Any, overload


class VersionException(RuntimeError):
    pass


class VersionLoader[_T](abc.ABC):
    @staticmethod
    def register_all() -> None:
        # Import files only needed for versioning
        from ..project import loader

    @overload
    @staticmethod
    def load_best(result: type[_T], data: bytes, *args: Any) -> _T: ...

    @overload
    @staticmethod
    def load_best(result: types.GenericAlias, data: bytes, *args: Any) -> Any: ...

    @staticmethod
    def load_best(
        result: type[_T] | types.GenericAlias, data: bytes, *args: Any
    ) -> _T | Any:
        fbver: VersionLoader[_T] | None = None

        for sclass in VersionLoader.__subclasses__():
            if (s := sclass()).result() == result:
                if math.isnan(s.version()):
                    if fbver is None:
                        fbver = s
                    continue

                if s.check(data):
                    return s.load(data, *args)

        # Fallback to versions which cant check
        if fbver:
            return fbver.load(data, *args)

        raise VersionException(
            f"No version found for {str(result)} with data {data[:5].hex(":", 1)}..."
        )

    @staticmethod
    def dump_best(result: type[_T] | types.GenericAlias, data: _T, *args: Any) -> bytes:
        versions: list[VersionLoader[_T]] = []

        for sclass in VersionLoader.__subclasses__():
            if (s := sclass()).result() == result:
                versions.append(s)

        versions.sort(key=lambda k: -math.inf if math.isnan(v := k.version()) else v)

        if len(versions) > 0:
            return versions[-1].dump(data, *args)

        raise VersionException(f"No versions found for {str(result)}!")

    @abc.abstractmethod
    def version(self) -> float:
        pass

    @abc.abstractmethod
    def result(self) -> type[_T] | types.GenericAlias:
        pass

    @abc.abstractmethod
    def check(self, data: bytes) -> bool:
        pass

    @abc.abstractmethod
    def load(self, data: bytes, *args: Any) -> _T:
        pass

    @abc.abstractmethod
    def dump(self, obj: _T, *args: Any) -> bytes:
        pass
