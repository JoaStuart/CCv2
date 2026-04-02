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

import subprocess

from .. import logger


def ffmpeg_call(*args: str) -> int:
    proc = subprocess.Popen(
        " ".join(("ffmpeg", *args)),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    ret = proc.wait()

    if ret != 0:
        assert proc.stderr is not None

        logger.error(
            "FFmpeg finished with return code %d, stderr buffer:\n%s",
            ret,
            proc.stderr.read().decode(),
        )

    return ret
