#!/usr/bin/env python3
"""
能打开本地摄像头 / 文件 / RTSP / HTTP 等流，显示画面，计算并打印实时与平均 FPS，统计读取错误并尝试重连，还可以选择把流保存到文件

功能:
- 打开视频流（摄像头索引 / 本地文件 / RTSP/HTTP URL）
- 在窗口中显示并在左上角叠加实时 FPS、帧计数和错误计数
- 统计平均 FPS 与总帧数
- 在读取失败时尝试重连若干次
- 可选保存输出到文件

依赖:
- opencv-python
  pip install opencv-python
"""

import cv2
import time
import argparse
import sys

def open_capture(source):
    # 如果 source 是数字（摄像头索引），尝试转成 int
    try:
        src = int(source)
    except Exception:
        src = source
    cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)  # 尝试使用 FFMPEG backend 更稳定（若可用）
    return cap

def try_reopen(source, max_attempts=5, delay=1.0):
    """重连策略：尝试多次打开"""
    attempt = 0
    while attempt < max_attempts:
        cap = open_capture(source)
        if cap.isOpened():
            return cap
        attempt += 1
        print(f"[WARN] open failed, attempt {attempt}/{max_attempts}, retry in {delay}s...")
        time.sleep(delay)
    return None

def main():
    parser = argparse.ArgumentParser(description="测试视频流的脚本（支持摄像头/文件/RTSP/HTTP）")
    parser.add_argument("source", help="视频源，支持摄像头索引(0)、本地文件路径或 URL（rtsp://...）")
    parser.add_argument("--duration", type=float, default=0, help="运行时长（秒）。0 表示直到手动退出")
    parser.add_argument("--save", default="", help="可选，保存输出到文件（例如 output.mp4）")
    parser.add_argument("--max-reconnect", type=int, default=5, help="读取失败时的最大重连次数")
    parser.add_argument("--reconnect-delay", type=float, default=1.0, help="重连间隔（秒）")
    parser.add_argument("--width", type=int, default=0, help="可选：强制设置输出宽度（像素）")
    parser.add_argument("--height", type=int, default=0, help="可选：强制设置输出高度（像素）")
    args = parser.parse_args()

    source = args.source
    cap = try_reopen(source, max_attempts=args.max_reconnect, delay=args.reconnect_delay)
    if cap is None:
        print("[ERROR] 无法打开视频源。请检查 URL/索引/文件路径。")
        sys.exit(2)

    # 设置分辨率（若指定）
    if args.width > 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    if args.height > 0:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    writer = None
    if args.save:
        # 以读取的一帧来决定写入参数（fps & frame size）
        fps_guess = cap.get(cv2.CAP_PROP_FPS) or 25.0
        # 等待第一帧以获取大小
        ret, frame = cap.read()
        if not ret:
            print("[WARN] 读取第一帧失败，尝试不保存或稍后再保存。")
        else:
            h, w = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(args.save, fourcc, fps_guess, (w, h))
            writer.write(frame)  # 写入第一帧
            print(f"[INFO] 正在保存到 {args.save}，fps_guess={fps_guess}, size=({w},{h})")
    else:
        # 预读一帧（如果上一分支没有读到）
        ret, frame = cap.read()
        if not ret:
            frame = None

    start_time = time.time()
    frame_count = 0
    bad_reads = 0
    last_fps_time = time.time()
    frames_this_second = 0
    realtime_fps = 0.0

    # 主循环
    while True:
        if frame is None:
            ret, frame = cap.read()
        else:
            ret = True

        if not ret or frame is None:
            bad_reads += 1
            print(f"[WARN] 读取帧失败（总失败 {bad_reads}）。尝试重连...")
            cap.release()
            cap = try_reopen(source, max_attempts=args.max_reconnect, delay=args.reconnect_delay)
            if cap is None:
                print("[ERROR] 重连失败，退出。")
                break
            # 重新读取一帧
            ret, frame = cap.read()
            if not ret:
                print("[WARN] 重连后首次读取仍失败，继续下一循环。")
                frame = None
                time.sleep(0.2)
                # 继续 loop 来再次尝试读取
                pass
            continue

        # 处理与显示
        frame_count += 1
        frames_this_second += 1
        now = time.time()

        # 计算实时 FPS（每 0.5 秒更新）
        if now - last_fps_time >= 0.5:
            realtime_fps = frames_this_second / (now - last_fps_time)
            last_fps_time = now
            frames_this_second = 0

        # 叠加文字信息
        overlay = frame.copy()
        text1 = f"Frames: {frame_count}"
        text2 = f"Realtime FPS: {realtime_fps:.2f}"
        text3 = f"Bad reads: {bad_reads}"
        texts = [text1, text2, text3]
        y0 = 20
        for i, t in enumerate(texts):
            cv2.putText(overlay, t, (10, y0 + i*20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2, cv2.LINE_AA)

        cv2.imshow("Stream Test", overlay)

        # 写入文件（如启用）
        if writer is not None:
            writer.write(frame)

        # 退出条件：按 q 或 Esc；或超过 duration（若指定）
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            print("[INFO] 用户退出（按键）。")
            break

        if args.duration > 0 and (time.time() - start_time) >= args.duration:
            print("[INFO] 达到指定运行时长，退出。")
            break

        # 预读下一帧（简单优化）
        ret2, next_frame = cap.read()
        if ret2:
            frame = next_frame
        else:
            frame = None

    elapsed = time.time() - start_time
    avg_fps = frame_count / elapsed if elapsed > 0 else 0.0
    print("====== 统计 ======")
    print(f"总帧数: {frame_count}")
    print(f"读取失败次数: {bad_reads}")
    print(f"运行时长: {elapsed:.2f}s")
    print(f"平均 FPS: {avg_fps:.2f}")

    # 清理
    if writer is not None:
        writer.release()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
