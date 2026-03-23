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
