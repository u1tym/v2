# -*- coding: utf-8 -*-

import sys
import warnings
import os
import re

#------------------------------------------------------------------------------
# SYSTEM設定
#
# - バイナリコード出力抑止
# - 実行時警告の出力抑止
#------------------------------------------------------------------------------

sys.dont_write_bytecode = True
warnings.filterwarnings( 'ignore' )

import tkinter as tk
from tkinter import filedialog, messagebox
from ffpyplayer.player import MediaPlayer
from ffpyplayer.pic import SWScale
from PIL import Image as PILImage, ImageTk
import time

def seconds_to_hms(sec: float) -> str:
    total = max(0, int(sec))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h}:{m:02d}:{s:02d}"

def hms_to_seconds(hms: str):
    if not re.fullmatch(r"\d+:[0-5]\d:[0-5]\d", hms):
        return None
    hh, mm, ss = hms.split(":")
    return int(hh) * 3600 + int(mm) * 60 + int(ss)

def main() -> None:
    root: tk.Tk = tk.Tk()
    root.title("ffpyplayer sample")
    control_h = 120
    side_w = 360
    setSize(root, 640 + side_w, 480 + control_h)

    root_frame = tk.Frame(root)
    root_frame.pack(side="top", fill="both", expand=True)

    left_frame = tk.Frame(root_frame)
    left_frame.pack(side="left", fill="both", expand=True)

    right_frame = tk.Frame(root_frame, width=side_w)
    right_frame.pack(side="right", fill="y", padx=8, pady=8)
    right_frame.pack_propagate(False)

    cnv: tk.Canvas = tk.Canvas(left_frame, bg="black", width=640, height=480)
    cnv.pack(side="top")

    ctrl_frame = tk.Frame(left_frame)
    ctrl_frame.pack(side="top", fill="x", padx=8, pady=6)

    current_file = os.path.abspath("hoge.mp4")
    player: MediaPlayer = MediaPlayer(current_file)

    img_on_cnv = None
    sws_to_rgb = None
    sws_src_fmt = ""
    sws_src_size = (0, 0)
    duration_sec = 0.0
    paused = False
    slider_dragging = False
    chapters = []
    chapter_index = 1
    last_video_pts = 0.0
    skip_av_sync_until = 0.0

    current_sec_var = tk.StringVar(value="再生位置: 0.00 秒")
    pause_btn_txt = tk.StringVar(value="一時停止")
    file_var = tk.StringVar(value=f"ファイル: {current_file}")
    chapter_name_var = tk.StringVar(value="")

    btn_frame = tk.Frame(ctrl_frame)
    btn_frame.pack(side="top", fill="x")

    pause_btn = tk.Button(btn_frame, textvariable=pause_btn_txt, width=10)
    back_btn = tk.Button(btn_frame, text="15秒戻る", width=10)
    forward_btn = tk.Button(btn_frame, text="15秒進む", width=10)
    add_chapter_btn = tk.Button(btn_frame, text="チャプター登録", width=12)
    current_lbl = tk.Label(btn_frame, textvariable=current_sec_var, anchor="w")

    pause_btn.pack(side="left")
    back_btn.pack(side="left", padx=(8, 0))
    forward_btn.pack(side="left", padx=(8, 0))
    add_chapter_btn.pack(side="left", padx=(8, 0))
    current_lbl.pack(side="left", padx=(8, 0))

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

    file_label = tk.Label(right_frame, textvariable=file_var, justify="left", anchor="w", wraplength=330)
    file_label.pack(side="top", fill="x", pady=(0, 8))

    file_btn_frame = tk.Frame(right_frame)
    file_btn_frame.pack(side="top", fill="x", pady=(0, 8))

    select_file_btn = tk.Button(file_btn_frame, text="ファイル選択", width=12)
    load_chapter_btn = tk.Button(file_btn_frame, text="チャプター読込", width=12)
    save_chapter_btn = tk.Button(file_btn_frame, text="チャプター保存", width=12)
    select_file_btn.pack(side="left")
    load_chapter_btn.pack(side="left", padx=(8, 0))
    save_chapter_btn.pack(side="left", padx=(8, 0))

    chapter_listbox = tk.Listbox(right_frame, height=18)
    chapter_listbox.pack(side="top", fill="both", expand=True)

    chapter_edit_frame = tk.Frame(right_frame)
    chapter_edit_frame.pack(side="top", fill="x", pady=(8, 0))
    chapter_name_entry = tk.Entry(chapter_edit_frame, textvariable=chapter_name_var)
    chapter_name_entry.pack(side="left", fill="x", expand=True)
    rename_btn = tk.Button(chapter_edit_frame, text="名称更新", width=10)
    rename_btn.pack(side="left", padx=(8, 0))
    delete_btn = tk.Button(chapter_edit_frame, text="削除", width=8)
    delete_btn.pack(side="left", padx=(8, 0))

    def clamp_seek_target(target: float) -> float:
        if duration_sec > 0:
            return max(0.0, min(target, duration_sec))
        return max(0.0, target)

    def do_relative_seek(delta: float) -> None:
        nonlocal skip_av_sync_until
        base_sec = player.get_pts()
        if base_sec is None:
            base_sec = 0.0
        target = clamp_seek_target(base_sec + delta)
        if duration_sec > 0:
            player.seek(target, relative=False)
        else:
            player.seek(delta, relative=True)
        skip_av_sync_until = time.time() + 0.4

    def on_pause_toggle() -> None:
        nonlocal paused
        paused = not paused
        player.set_pause(paused)
        pause_btn_txt.set("再開" if paused else "一時停止")

    def refresh_chapter_list() -> None:
        chapter_listbox.delete(0, tk.END)
        for ch in sorted(chapters, key=lambda x: x["sec"]):
            chapter_listbox.insert(tk.END, f"({ch['sec']:.2f}) {seconds_to_hms(ch['sec'])} {ch['name']}")

    def reset_player(video_path: str) -> None:
        nonlocal player, current_file, img_on_cnv, sws_to_rgb, sws_src_fmt, sws_src_size
        nonlocal duration_sec, paused, slider_dragging
        try:
            player.close_player()
        except Exception:
            pass
        player = MediaPlayer(video_path)
        current_file = video_path
        file_var.set(f"ファイル: {current_file}")
        img_on_cnv = None
        sws_to_rgb = None
        sws_src_fmt = ""
        sws_src_size = (0, 0)
        duration_sec = 0.0
        paused = False
        slider_dragging = False
        pause_btn_txt.set("一時停止")
        seek_var.set(0.0)
        current_sec_var.set("再生位置: 0.00 秒")

    def on_select_file() -> None:
        path = filedialog.askopenfilename(
            title="動画ファイル選択",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if not path:
            return
        reset_player(path)
        chapters.clear()
        refresh_chapter_list()

    def on_add_chapter() -> None:
        nonlocal chapter_index
        sec = last_video_pts
        chapters.append({"sec": float(sec), "name": f"chapter{chapter_index}"})
        chapter_index += 1
        refresh_chapter_list()

    def on_chapter_select(_event=None) -> None:
        sel = chapter_listbox.curselection()
        if not sel:
            chapter_name_var.set("")
            return
        idx = sel[0]
        sorted_chapters = sorted(chapters, key=lambda x: x["sec"])
        if 0 <= idx < len(sorted_chapters):
            chapter_name_var.set(sorted_chapters[idx]["name"])

    def on_chapter_rename() -> None:
        sel = chapter_listbox.curselection()
        if not sel:
            return
        new_name = chapter_name_var.get().strip()
        if not new_name:
            messagebox.showerror("エラー", "チャプター名を入力してください。")
            return
        idx = sel[0]
        sorted_chapters = sorted(chapters, key=lambda x: x["sec"])
        if not (0 <= idx < len(sorted_chapters)):
            return
        target = sorted_chapters[idx]
        for ch in chapters:
            if ch is target:
                ch["name"] = new_name
                break
        refresh_chapter_list()
        chapter_listbox.selection_set(idx)

    def on_chapter_delete() -> None:
        sel = chapter_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        sorted_chapters = sorted(chapters, key=lambda x: x["sec"])
        if not (0 <= idx < len(sorted_chapters)):
            return
        target = sorted_chapters[idx]
        for i, ch in enumerate(chapters):
            if ch is target:
                del chapters[i]
                break
        refresh_chapter_list()
        chapter_name_var.set("")

    def on_chapter_jump(_event=None) -> None:
        nonlocal skip_av_sync_until
        sel = chapter_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        sorted_chapters = sorted(chapters, key=lambda x: x["sec"])
        if 0 <= idx < len(sorted_chapters):
            player.seek(clamp_seek_target(sorted_chapters[idx]["sec"]), relative=False)
            skip_av_sync_until = time.time() + 0.4

    def on_save_chapters() -> None:
        if not current_file:
            messagebox.showerror("エラー", "保存対象の動画ファイルがありません。")
            return
        base_name = os.path.splitext(os.path.basename(current_file))[0]
        out_path = os.path.join(os.getcwd(), f"{base_name}.txt")
        sorted_chapters = sorted(chapters, key=lambda x: x["sec"])
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(current_file + "\n")
                for ch in sorted_chapters:
                    f.write(f"{seconds_to_hms(ch['sec'])},{ch['name']}\n")
            messagebox.showinfo("保存完了", f"保存しました:\n{out_path}")
        except Exception as ex:
            messagebox.showerror("エラー", f"保存に失敗しました。\n{ex}")

    def on_load_chapters() -> None:
        path = filedialog.askopenfilename(
            title="チャプターファイル読込",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\n") for line in f]
        except Exception as ex:
            messagebox.showerror("エラー", f"読み込みに失敗しました。\n{ex}")
            return
        if len(lines) < 1:
            messagebox.showerror("エラー", "ファイル内容が空です。")
            return

        video_path = lines[0].strip()
        parsed_chapters = []
        for i, line in enumerate(lines[1:], start=2):
            if not line.strip():
                continue
            if "," not in line:
                messagebox.showerror("形式エラー", f"{i}行目が不正です。h:mm:ss,チャプター名 形式にしてください。")
                return
            hms, name = line.split(",", 1)
            sec = hms_to_seconds(hms.strip())
            if sec is None or not name.strip():
                messagebox.showerror("形式エラー", f"{i}行目が不正です。h:mm:ss,チャプター名 形式にしてください。")
                return
            parsed_chapters.append({"sec": float(sec), "name": name.strip()})

        reset_player(video_path)
        chapters.clear()
        chapters.extend(parsed_chapters)
        refresh_chapter_list()

    def on_seek_press(_event) -> None:
        nonlocal slider_dragging
        slider_dragging = True

    def on_seek_release(_event) -> None:
        nonlocal skip_av_sync_until
        nonlocal slider_dragging
        slider_dragging = False
        player.seek(clamp_seek_target(seek_var.get()), relative=False)
        skip_av_sync_until = time.time() + 0.4

    pause_btn.config(command=on_pause_toggle)
    back_btn.config(command=lambda: do_relative_seek(-15.0))
    forward_btn.config(command=lambda: do_relative_seek(15.0))
    add_chapter_btn.config(command=on_add_chapter)
    select_file_btn.config(command=on_select_file)
    load_chapter_btn.config(command=on_load_chapters)
    save_chapter_btn.config(command=on_save_chapters)
    rename_btn.config(command=on_chapter_rename)
    delete_btn.config(command=on_chapter_delete)
    seek_scale.bind("<ButtonPress-1>", on_seek_press)
    seek_scale.bind("<ButtonRelease-1>", on_seek_release)
    chapter_listbox.bind("<<ListboxSelect>>", on_chapter_select)
    chapter_listbox.bind("<Double-Button-1>", on_chapter_jump)

    while True:
        meta = player.get_metadata()
        if meta and isinstance(meta.get("duration"), (int, float)):
            duration_sec = float(meta["duration"])
            if duration_sec > 0:
                seek_scale.config(to=duration_sec)

        frame, val = player.get_frame()

        if frame is None:
            time.sleep(0.01)
        else:
            data, frame_pts = frame
            # ffpyplayer の映像フレーム(Image)のみ処理する
            # 音声フレームはこれらのメソッドを持たないため除外できる
            if all(hasattr(data, attr) for attr in ("get_size", "get_pixel_format", "to_bytearray")):
                # 映像
                img = data
                video_pts = frame_pts
                if isinstance(video_pts, (int, float)):
                    last_video_pts = float(video_pts)

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
                if isinstance(video_pts, (int, float)):
                    # 巻き戻し/シーク直後は古いPTS差で固まりやすいため、短時間だけ同期待ちを抑止
                    if video_pts + 0.001 < last_video_pts:
                        skip_av_sync_until = max(skip_av_sync_until, time.time() + 0.4)
                if time.time() >= skip_av_sync_until and audio_pts is not None and video_pts > audio_pts:
                    time.sleep(min(video_pts - audio_pts, 0.05))

                if img_on_cnv is None:
                    setSize(root, w + side_w, h + control_h)
                    cnv.config(width=w, height=h)
                    seek_scale.config(length=max(200, w - 20))
                    img_on_cnv = cnv.create_image(0, 0, anchor='nw', image=tk_img)
                else:
                    cnv.itemconfig(img_on_cnv, image=tk_img)

        now_sec = last_video_pts
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
