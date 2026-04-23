# -*- coding: utf-8 -*-

import sys
import warnings

#------------------------------------------------------------------------------
# SYSTEM設定
#
# - バイナリコード出力抑止
# - 実行時警告の出力抑止
#------------------------------------------------------------------------------

sys.dont_write_bytecode = True
warnings.filterwarnings( 'ignore' )

import tkinter as tk
from ffpyplayer.player import MediaPlayer
from PIL import Image, ImageTk
import time
import numpy as np
from numpy.typing import NDArray
from typing import cast

def main() -> None:
    root: tk.Tk = tk.Tk()
    setSize(root, 640, 480)

    cnv: tk.Canvas = tk.Canvas(root, bg="black", width=640, height=480)
    cnv.place(x=0, y=0)

    player: MediaPlayer = MediaPlayer("hoge.mp4")

    while True:
        frame, val = player.get_frame()
        if val == "eof":
            break
        if frame == None:
            continue
        if val != "video":
            continue

        img, video_pts = frame
        img = cast(NDArray[np.uint8], img)

        while True:
            audio_pts = player.get_pts()
            if video_pts > audio_pts:
                time.sleep(video_pts - audio_pts)
                continue
            break

        # 表示

        pil_img: Image = Image.fromarray(img)

        tk_img = ImageTk.PhotoImage(image=pil_img)

    return

def setSize(rt: tk.Tk, w: int, h: int) -> None:
    rt.geometry(str(w) + "x" + str(h))
    rt.minsize(w, h)
    rt.maxsize(w, h)


if __name__ == '__main__':

    main()
