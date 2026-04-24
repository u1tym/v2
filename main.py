# -*- coding: utf-8 -*-

import sys
import warnings
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import vlc

sys.dont_write_bytecode = True
warnings.filterwarnings("ignore")


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
    root = tk.Tk()
    root.title("python-vlc sample")
    root.geometry("1000x620")
    root.minsize(1000, 620)

    root_frame = tk.Frame(root)
    root_frame.pack(fill="both", expand=True)

    left_frame = tk.Frame(root_frame)
    left_frame.pack(side="left", fill="both", expand=True)

    right_frame = tk.Frame(root_frame, width=360)
    right_frame.pack(side="right", fill="y", padx=8, pady=8)
    right_frame.pack_propagate(False)

    video_frame = tk.Frame(left_frame, bg="black", width=640, height=480)
    video_frame.pack(side="top", fill="both", expand=True)
    video_frame.pack_propagate(False)

    ctrl_frame = tk.Frame(left_frame)
    ctrl_frame.pack(side="top", fill="x", padx=8, pady=6)

    instance = vlc.Instance()
    player = instance.media_player_new()

    current_file = os.path.abspath("hoge.mp4")
    duration_sec = 0.0
    paused = False
    slider_dragging = False
    chapters = []
    chapter_index = 1
    app_closing = False
    speed_supported = callable(getattr(player, "set_rate", None))

    current_sec_var = tk.StringVar(value="再生位置: 0.00 秒")
    pause_btn_txt = tk.StringVar(value="一時停止")
    file_var = tk.StringVar(value=f"ファイル: {current_file}")
    chapter_name_var = tk.StringVar(value="")
    speed_var = tk.StringVar(value="1.0x")

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
        length=620,
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

    speed_frame = tk.Frame(right_frame)
    speed_frame.pack(side="top", fill="x", pady=(0, 8))
    tk.Label(speed_frame, text="再生速度:").pack(side="left")
    speed_options = ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"]
    speed_menu = tk.OptionMenu(speed_frame, speed_var, *speed_options)
    speed_menu.config(width=8)
    speed_menu.pack(side="left", padx=(8, 0))
    speed_status_var = tk.StringVar(value="")
    tk.Label(speed_frame, textvariable=speed_status_var, anchor="w").pack(side="left", padx=(8, 0))

    chapter_listbox = tk.Listbox(right_frame, height=18)
    chapter_listbox.pack(side="top", fill="both", expand=True)

    chapter_edit_frame = tk.Frame(right_frame)
    chapter_edit_frame.pack(side="top", fill="x", pady=(8, 0))
    tk.Entry(chapter_edit_frame, textvariable=chapter_name_var).pack(side="left", fill="x", expand=True)
    rename_btn = tk.Button(chapter_edit_frame, text="名称更新", width=10)
    rename_btn.pack(side="left", padx=(8, 0))
    delete_btn = tk.Button(chapter_edit_frame, text="削除", width=8)
    delete_btn.pack(side="left", padx=(8, 0))

    def clamp_seek_target(target: float) -> float:
        if duration_sec > 0:
            return max(0.0, min(target, duration_sec))
        return max(0.0, target)

    def get_pos_sec() -> float:
        cur = player.get_time()
        if cur is None or cur < 0:
            return 0.0
        return cur / 1000.0

    def seek_to(target: float) -> None:
        player.set_time(int(clamp_seek_target(target) * 1000))

    def apply_video_target() -> None:
        root.update_idletasks()
        hwnd = video_frame.winfo_id()
        player.set_hwnd(hwnd)

    def refresh_chapter_list() -> None:
        chapter_listbox.delete(0, tk.END)
        for ch in sorted(chapters, key=lambda x: x["sec"]):
            chapter_listbox.insert(tk.END, f"({ch['sec']:.2f}) {seconds_to_hms(ch['sec'])} {ch['name']}")

    def on_speed_change(*_args) -> None:
        if not speed_supported:
            return
        text = speed_var.get().strip().lower()
        if not text.endswith("x"):
            return
        try:
            rate = float(text[:-1])
        except ValueError:
            return
        if rate <= 0:
            return
        ok = player.set_rate(rate)
        if ok == -1:
            messagebox.showerror("エラー", "再生速度の変更に失敗しました。")

    def start_media(video_path: str) -> None:
        nonlocal current_file, duration_sec, paused
        player.stop()
        media = instance.media_new(video_path)
        player.set_media(media)
        current_file = video_path
        file_var.set(f"ファイル: {current_file}")
        duration_sec = 0.0
        paused = False
        pause_btn_txt.set("一時停止")
        seek_var.set(0.0)
        current_sec_var.set("再生位置: 0.00 秒")
        apply_video_target()
        player.play()
        on_speed_change()

    def do_relative_seek(delta: float) -> None:
        seek_to(get_pos_sec() + delta)

    def on_pause_toggle() -> None:
        nonlocal paused
        paused = not paused
        if paused:
            player.pause()
        else:
            player.play()
            on_speed_change()
        pause_btn_txt.set("再開" if paused else "一時停止")

    def on_select_file() -> None:
        path = filedialog.askopenfilename(
            title="動画ファイル選択",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
        )
        if not path:
            return
        start_media(path)
        chapters.clear()
        refresh_chapter_list()

    def on_add_chapter() -> None:
        nonlocal chapter_index
        sec = get_pos_sec()
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
        name = chapter_name_var.get().strip()
        if not name:
            messagebox.showerror("エラー", "チャプター名を入力してください。")
            return
        idx = sel[0]
        sorted_chapters = sorted(chapters, key=lambda x: x["sec"])
        if 0 <= idx < len(sorted_chapters):
            target = sorted_chapters[idx]
            for ch in chapters:
                if ch is target:
                    ch["name"] = name
                    break
            refresh_chapter_list()
            chapter_listbox.selection_set(idx)

    def on_chapter_delete() -> None:
        sel = chapter_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        sorted_chapters = sorted(chapters, key=lambda x: x["sec"])
        if 0 <= idx < len(sorted_chapters):
            target = sorted_chapters[idx]
            for i, ch in enumerate(chapters):
                if ch is target:
                    del chapters[i]
                    break
            refresh_chapter_list()
            chapter_name_var.set("")

    def on_chapter_jump(_event=None) -> None:
        sel = chapter_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        sorted_chapters = sorted(chapters, key=lambda x: x["sec"])
        if 0 <= idx < len(sorted_chapters):
            seek_to(sorted_chapters[idx]["sec"])

    def on_save_chapters() -> None:
        if not current_file:
            messagebox.showerror("エラー", "保存対象の動画ファイルがありません。")
            return
        base = os.path.splitext(os.path.basename(current_file))[0]
        out_path = os.path.join(os.getcwd(), f"{base}.txt")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(current_file + "\n")
                for ch in sorted(chapters, key=lambda x: x["sec"]):
                    f.write(f"{seconds_to_hms(ch['sec'])},{ch['name']}\n")
            messagebox.showinfo("保存完了", f"保存しました:\n{out_path}")
        except Exception as ex:
            messagebox.showerror("エラー", f"保存に失敗しました。\n{ex}")

    def on_load_chapters() -> None:
        path = filedialog.askopenfilename(
            title="チャプターファイル読込",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\n") for line in f]
        except Exception as ex:
            messagebox.showerror("エラー", f"読み込みに失敗しました。\n{ex}")
            return
        if not lines:
            messagebox.showerror("エラー", "ファイル内容が空です。")
            return

        video_path = lines[0].strip()
        parsed = []
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
            parsed.append({"sec": float(sec), "name": name.strip()})

        start_media(video_path)
        chapters.clear()
        chapters.extend(parsed)
        refresh_chapter_list()

    def on_seek_press(_event) -> None:
        nonlocal slider_dragging
        slider_dragging = True

    def on_seek_release(_event) -> None:
        nonlocal slider_dragging
        slider_dragging = False
        seek_to(seek_var.get())

    def on_close() -> None:
        nonlocal app_closing
        if app_closing:
            return
        app_closing = True
        try:
            player.stop()
        except Exception:
            pass
        root.destroy()

    def ui_tick() -> None:
        nonlocal duration_sec
        if app_closing:
            return
        length = player.get_length()
        if length is not None and length > 0:
            duration_sec = length / 1000.0
            seek_scale.config(to=duration_sec)

        now_sec = get_pos_sec()
        current_sec_var.set(f"再生位置: {now_sec:.2f} 秒")
        if not slider_dragging:
            seek_var.set(clamp_seek_target(now_sec))

        root.after(30, ui_tick)

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
    speed_var.trace_add("write", on_speed_change)
    root.protocol("WM_DELETE_WINDOW", on_close)

    if speed_supported:
        speed_menu.config(state="normal")
        speed_status_var.set("")
    else:
        speed_menu.config(state="disabled")
        speed_status_var.set("(この環境では未対応)")

    apply_video_target()
    start_media(current_file)
    ui_tick()
    root.mainloop()


if __name__ == "__main__":
    main()
