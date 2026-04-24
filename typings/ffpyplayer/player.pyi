from typing import Self
from typing import Tuple
from typing import Optional
from typing import Union

from ffpyplayer.pic import Image
#import numpy as np
#from numpy.typing import NDArray

#VideoFrame = Tuple[NDArray[np.uint8], float]
VideoFrame = Tuple[Image, float]
AudioFrame = Tuple[bytes, float]

FrameType = Optional[Union[VideoFrame, AudioFrame]]
ValType = Optional[float]

class MediaPlayer:
    def __init__(self: Self, filename: str) -> None: ...
    def get_frame(self: Self) -> Tuple[FrameType, ValType]:...
    def get_pts(self: Self) -> float: ...
