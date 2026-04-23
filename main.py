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
from PIL import Image, ImageTk
import time

def main() -> None:
    root: tk.Tk = tk.Tk()
    root.title("ffpyplayer sample")
    setSize(root, 640, 480)

    cnv: tk.Canvas = tk.Canvas(root, bg="black", width=640, height=480)
    cnv.place(x=0, y=0)

    player: MediaPlayer = MediaPlayer("hoge.mp4")

    img_on_cnv = None
    cnv_size = (640, 480)
    sws_to_rgb = None
    sws_src_fmt = ""
    sws_src_size = (0, 0)

    while True:
        frame, val = player.get_frame()
        if val == "eof":
            break
        if frame is None:
            # フレーム未準備時もイベントを処理してウィンドウを固めない
            root.update_idletasks()
            root.update()
            continue

        img, video_pts = frame

        while True:
            audio_pts = player.get_pts()
            if video_pts > audio_pts:
                time.sleep(video_pts - audio_pts)
                continue
            break

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
        pil_img = Image.frombytes("RGB", src_size, bytes(plane))

        tk_img = ImageTk.PhotoImage(image=pil_img)
        cnv.image = tk_img  # 参照を保持してGCで消えないようにする

        if img_on_cnv is None:
            w, h = pil_img.size
            setSize(root, w, h)
            cnv.config(width=w, height=h)
            cnv_size = (w, h)
            img_on_cnv = cnv.create_image(0, 0, anchor='nw', image=tk_img)
        else:
            w, h = pil_img.size
            if cnv_size != (w, h):
                setSize(root, w, h)
                cnv.config(width=w, height=h)
                cnv_size = (w, h)
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
