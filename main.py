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
    control_h = 100
    setSize(root, 640, 480 + control_h)

    cnv: tk.Canvas = tk.Canvas(root, bg="black", width=640, height=480)
    cnv.pack(side="top")

    ctrl_frame = tk.Frame(root)
    ctrl_frame.pack(side="top", fill="x", padx=8, pady=6)

    player: MediaPlayer = MediaPlayer("hoge.mp4")

    img_on_cnv = None
    sws_to_rgb = None
    sws_src_fmt = ""
    sws_src_size = (0, 0)
    duration_sec = 0.0
    paused = False
    slider_dragging = False

    current_sec_var = tk.StringVar(value="再生位置: 0.00 秒")
    pause_btn_txt = tk.StringVar(value="一時停止")

    btn_frame = tk.Frame(ctrl_frame)
    btn_frame.pack(side="top", fill="x")

    pause_btn = tk.Button(btn_frame, textvariable=pause_btn_txt, width=10)
    back_btn = tk.Button(btn_frame, text="15秒戻る", width=10)
    forward_btn = tk.Button(btn_frame, text="15秒進む", width=10)
    current_lbl = tk.Label(btn_frame, textvariable=current_sec_var, anchor="w")

    pause_btn.pack(side="left")
    back_btn.pack(side="left", padx=(8, 0))
    forward_btn.pack(side="left", padx=(8, 0))
    current_lbl.pack(side="left", padx=(12, 0))

    seek_var = tk.DoubleVar(value=0.0)
    seek_scale = tk.Scale(
        ctrl_frame,
        variable=seek_var,
        orient="horizontal",
        from_=0.0,
        to=100.0,
        resolution=0.1,
        showvalue=False,
        length=620
    )
    seek_scale.pack(side="top", fill="x", pady=(8, 0))

    def clamp_seek_target(target: float) -> float:
        if duration_sec > 0:
            return max(0.0, min(target, duration_sec))
        return max(0.0, target)

    def do_relative_seek(delta: float) -> None:
        base_sec = player.get_pts()
        if base_sec is None:
            base_sec = 0.0
        target = clamp_seek_target(base_sec + delta)
        if duration_sec > 0:
            player.seek(target, relative=False)
        else:
            player.seek(delta, relative=True)

    def on_pause_toggle() -> None:
        nonlocal paused
        paused = not paused
        player.set_pause(paused)
        pause_btn_txt.set("再開" if paused else "一時停止")

    def on_seek_press(_event) -> None:
        nonlocal slider_dragging
        slider_dragging = True

    def on_seek_release(_event) -> None:
        nonlocal slider_dragging
        slider_dragging = False
        player.seek(clamp_seek_target(seek_var.get()), relative=False)

    pause_btn.config(command=on_pause_toggle)
    back_btn.config(command=lambda: do_relative_seek(-15.0))
    forward_btn.config(command=lambda: do_relative_seek(15.0))
    seek_scale.bind("<ButtonPress-1>", on_seek_press)
    seek_scale.bind("<ButtonRelease-1>", on_seek_release)

    while True:
        meta = player.get_metadata()
        if meta and isinstance(meta.get("duration"), (int, float)):
            duration_sec = float(meta["duration"])
            if duration_sec > 0:
                seek_scale.config(to=duration_sec)

        frame, val = player.get_frame()

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
                    time.sleep(video_pts - audio_pts)

                if img_on_cnv is None:
                    setSize(root, w, h + control_h)
                    cnv.config(width=w, height=h)
                    seek_scale.config(length=max(200, w - 20))
                    img_on_cnv = cnv.create_image(0, 0, anchor='nw', image=tk_img)
                else:
                    cnv.itemconfig(img_on_cnv, image=tk_img)

        now_sec = player.get_pts()
        if now_sec is None:
            now_sec = 0.0
        current_sec_var.set(f"再生位置: {now_sec:.2f} 秒")
        if not slider_dragging:
            seek_var.set(clamp_seek_target(now_sec))

        root.update_idletasks()
        root.update()

    return

def setSize(rt: tk.Tk, w: int, h: int) -> None:
    rt.geometry(str(w) + "x" + str(h))
    rt.minsize(w, h)
    rt.maxsize(w, h)


if __name__ == '__main__':

    main()
