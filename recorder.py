# -*- coding: utf-8 -*-
import os
import time
import yaml
import wave
import pyaudio
import threading
import requests


class Recorder(object):
    def __init__(self):
        ## -----*----- コンストラクタ -----*----- ##
        self.config = yaml.load(open('config/wave.yml'), Loader=yaml.SafeLoader)

        # ストリーマの設定
        self._pa = pyaudio.PyAudio()
        self.stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self.config['channels'],
            rate=self.config['rate'],
            input=True,
            output=False,
            frames_per_buffer=self.config['chunk'],
        )

        # 音声データの格納リスト（past：欠け補完，main：メイン音声）
        self.audio = {'past': [], 'main': []}

        # 録音開始・終了フラグ
        self.b_record_start = threading.Event()
        self.b_record_end = threading.Event()

        self.file = './files/source.wav'

        self.exe()


    def exe(self):
        ## -----*----- 処理実行 -----*----- ##
        # フラグの初期化
        self.is_exit = False
        self.b_record_start.clear()
        self.b_record_end.set()

        # 欠け補完部分の録音
        self.past_record(True)

        # サブスレッド起動
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def loop(self):
        ## -----*----- ループ（録音） -----*----- ##
        while not self.is_exit:
            if self.b_record_start.is_set():
                self.record()
                self.past_record(True)
            else:
                self.past_record(False)

        # 音声録音を行うスレッドを破壊
        del self.thread


    def record(self):
        ## -----*----- 音声録音 -----*----- ##
        # 開始フラグが降りるまで音声データを格納
        while self.b_record_start.is_set():
            self.audio['main'].append(self.input_audio())
        # ファイル保存
        self.save_audio()

    def past_record(self, init=False):
        ## -----*----- 欠け補完部分の録音 -----*----- ##
        if init:
            self.audio['past'] = []
            for i in range(int(self.settings['rate'] / self.settings['chunk'] * self.settings['past_second'])):
                self.audio['past'].append(self.input_audio())
        else:
            self.audio['past'].pop(0)
            self.audio['past'].append(self.input_audio())


    def save_audio(self):
        ## -----*----- 音声データ保存 -----*----- ##
        # 音声ファイルのフォーマット指定
        wav = wave.open(self.file, 'wb')
        wav.setnchannels(self.settings['channels'])
        wav.setsampwidth(self._pa.get_sample_size(self.settings['format']))
        wav.setframerate(self.settings['rate'])

        # 音声データをファイルに書き込み
        for data in [self.audio['past'], self.audio['main']]:
            wav.writeframes(b''.join(data))
        wav.close()

        # 音声データの初期化
        self.audio = {'past': [], 'main': []}
        self.b_record_end.set()


def input_audio(self):
        ## -----*----- 音声入力 -----*----- ##
        return self.stream.read(self.settings['chunk'], exception_on_overflow=False)


if __name__ == '__main__':
    recorder = Recorder()
    time.sleep(2)
    print('start')
    recorder.b_record_start.set()
    time.sleep(1)
    recorder.b_record_start.clear()
完
