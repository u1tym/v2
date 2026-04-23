from typing import Self
from typing import Tuple
from typing import Optional
from typing import Union
from typing import Literal
import numpy as np
from numpy.typing import NDArray

VideoFrame = Tuple[NDArray[np.uint8], float]
AudioFrame = Tuple[bytes, float]

FrameType = Optional[Union[VideoFrame, AudioFrame]]
ValType = Optional[Literal["video", "audio", "eof"]]

class MediaPlayer:
    def __init__(self: Self, filename: str) -> None: ...
    def get_frame(self: Self) -> Union[Tuple[VideoFrame, Literal["video"]], Tuple[AudioFrame, Literal["audio"]], Tuple[None, Literal["eof"]]]:...
    def get_pts(self: Self) -> float: ...
