# -*- coding: utf-8 -*-
import os
import time
import yaml
import wave
import pyaudio
import threading
import requests
import numpy as np
import recorder
import warnings
warnings.simplefilter("ignore", DeprecationWarning)


# 各種設定
config = yaml.load(open('config/wave.yml'), Loader=yaml.SafeLoader)
# ストリーマ
pa = pyaudio.PyAudio()
streamer = pa.open(
    format=pyaudio.paFloat32,
    channels=config['channels'],
    rate=config['rate']*4,
    input=True,
    output=False,
    frames_per_buffer=config['chunk'],
)
# 立ち上がり・下がり検出数
cnt_edge = {'up': 0, 'down': 0}
# 音量・閾値などの状態管理
state = {'amp': 0, 'total': 0, 'n': 0, 'border': 9999, 'average': 0}
# フラグを初期化
is_stream = False
is_exit = False
# 録音器
record = recorder.Recorder()


def start():
    ## -----*----- 検出開始 ------*----- ##
    # 閾値更新を並列化
    thread = threading.Thread(target=update_border)
    thread.start()

    global past_time
    past_time = time.time()

    while not is_exit:
        if time.time() - past_time > 0.5:
            reset_state()
        state['n'] += 1
        detection()

    record.exit()


def detection():
    ## -----*----- 命令検出 -----*----- ##
    global is_stream
    wav = np.fromstring(streamer.read(config['chunk'], exception_on_overflow=False), np.float32)
    wav *= np.hanning(config['chunk'])
    # パワースペクトル
    x = np.fft.fft(wav)
    x = [np.sqrt(c.real ** 2 + c.imag ** 2) for c in x]
    # バンドパスフィルタ（100~5000 Hz）
    x = x[
        int((config['chunk'] / (config['rate'] * 2)) * 100):
        int((config['chunk'] / (config['rate'] * 2)) * 5000)
    ]

    # Amp値・平均値の算出
    state['amp'] = sum(x)
    state['total'] += state['amp']
    state['average'] = state['total'] / state['n']

    # 立ち上がり・下がり検出
    if up_edge() and not is_stream:
        record.start()
        state['border'] = state['average']
        is_stream = True
    if down_edge() and is_stream:
        record.end()
        reset_state()
        is_stream = False


def up_edge():
    ## -----*----- 立ちがり検出 -----*----- ##
    if state['amp'] >= state['border']:
        cnt_edge['up'] += 1
    if cnt_edge['up'] > 5:
        return True
    return False


def down_edge():
    ## -----*----- 立ち下がり検出 -----*----- ##
    if state['average'] <= state['border']:
        cnt_edge['down'] += 1
    if cnt_edge['down'] > 10:
        cnt_edge['up'] = 0
        cnt_edge['down'] = 0
        return True
    return False


def update_border():
    ## -----*----- 閾値を更新 -----*----- ##
    offset = range(50, 201, 10)
    while not is_exit:
        time.sleep(0.2)
        if cnt_edge['up'] < 3 and not record.b_stream:
            if int(state['average'] / 20) > len(offset) - 1:
                i = len(offset) - 1
            else:
                i = int(state['average'] / 20)
            state['border'] = pow(10, 1.13) * pow(state['average'], 0.72)


def reset_state():
    ## -----*----- 状態をリセット ------*------ ##
    state['total'] = state['average'] * 15
    state['n'] = 15
    if state['average'] >= state['amp']:
        cnt_edge['up'] = 0
    past_time = time.time()

