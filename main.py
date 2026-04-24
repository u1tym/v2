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
from ffpyplayer.pic import SWScale
from PIL import Image as PILImage, ImageTk
import time

def main() -> None:
    root: tk.Tk = tk.Tk()
    root.title("ffpyplayer sample")
    setSize(root, 640, 480)

    cnv: tk.Canvas = tk.Canvas(root, bg="black", width=640, height=480)
    cnv.place(x=0, y=0)

    player: MediaPlayer = MediaPlayer("hoge.mp4")

    img_on_cnv = None
    sws_to_rgb = None
    sws_src_fmt = ""
    sws_src_size = (0, 0)

    while True:
        frame, val = player.get_frame()

        if val == "eof":
            break

        if frame is None:
            print("")
        else:
            data, frame_pts = frame
            # ffpyplayer の映像フレーム(Image)のみ処理する
            # 音声フレームはこれらのメソッドを持たないため除外できる
            if all(hasattr(data, attr) for attr in ("get_size", "get_pixel_format", "to_bytearray")):
                # 映像
                img = data
                video_pts = frame_pts

                # 表示

                src_size = img.get_size()
                src_fmt = img.get_pixel_format()
                if src_fmt != "rgb24":
                    # PILで扱いやすいRGBに揃える
                    if sws_to_rgb is None or sws_src_fmt != src_fmt or sws_src_size != src_size:
                        sws_to_rgb = SWScale(src_size[0], src_size[1], src_fmt, ofmt="rgb24")
                        sws_src_fmt = src_fmt
                        sws_src_size = src_size
                    img = sws_to_rgb.scale(img)
                    src_size = img.get_size()

                plane = img.to_bytearray()[0]
                pil_img = PILImage.frombytes("RGB", src_size, bytes(plane))

                tk_img = ImageTk.PhotoImage(image=pil_img)
                cnv.image = tk_img  # 参照を保持してGCで消えないようにする

                w, h = pil_img.size

                audio_pts = player.get_pts()
                if video_pts > audio_pts:
                    print(video_pts - audio_pts)
                    time.sleep(video_pts - audio_pts + 0.015)

                if img_on_cnv is None:
                    setSize(root, w, h)
                    cnv.config(width=w, height=h)
                    img_on_cnv = cnv.create_image(0, 0, anchor='nw', image=tk_img)
                else:
                    cnv.itemconfig(img_on_cnv, image=tk_img)

        root.update_idletasks()
        root.update()

    return

def setSize(rt: tk.Tk, w: int, h: int) -> None:
    rt.geometry(str(w) + "x" + str(h))
    rt.minsize(w, h)
    rt.maxsize(w, h)


if __name__ == '__main__':

    main()
