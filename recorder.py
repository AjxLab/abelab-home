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
        self.pa = pyaudio.PyAudio()
        self.pa_streamer = self.pa.open(
            format=pyaudio.paInt16,
            channels=self.config['channels'],
            rate=self.config['rate'],
            input=True,
            output=False,
            frames_per_buffer=self.config['chunk'],
        )

        # 音声データの格納リスト（past：欠け補完，main：メイン音声）
        self.wave = {'head': [], 'main': []}

        # フラグを初期化
        self.b_exit = False
        self.b_stream = False

        # 欠け補完
        self.head_record(True)

        # 録音を並列化
        self.thread = threading.Thread(target=self.streamer)
        self.thread.start()


    def streamer(self):
        ## -----*----- 録音 -----*----- ##
        while not self.b_exit:
            if self.b_stream:
                # 音声を格納
                while self.b_stream:
                    self.wave['main'].append(self.read())

                self.head_record(True)
            else:
                self.head_record(False)

        # 録音スレッドを破壊
        del self.thread


    def head_record(self, init=False):
        ## -----*----- 欠け補完部分の録音 -----*----- ##
        if init:
            self.wave['head'] = []
            for i in range(int(self.config['rate'] / self.config['chunk'] * self.config['head_sec'])):
                self.wave['head'].append(self.read())
        else:
            if len(self.wave['head']) > 0:
                self.wave['head'].pop(0)
            self.wave['head'].append(self.read())


    def dump_wave(self):
        ## -----*----- 音声保存 -----*----- ##
        # フォーマット指定
        wav = wave.open(self.config['wav_path'], 'wb')
        wav.setnchannels(self.config['channels'])
        wav.setsampwidth(self.pa.get_sample_size(pyaudio.paInt16))
        wav.setframerate(self.config['rate'])

        # 音声データをファイルに書き込み
        for data in [self.wave['head'], self.wave['main']]:
            wav.writeframes(b''.join(data))
        wav.close()

        # 音声データの初期化
        self.wave = {'head': [], 'main': []}


    def read(self):
        ## -----*----- 音声入力 -----*----- ##
        return self.pa_streamer.read(self.config['chunk'], exception_on_overflow=False)


    def start(self): self.b_stream = True
    def end(self):   self.b_stream = False; self.dump_wave()
    def exit(self):  self.b_exit = True


if __name__ == '__main__':
    recorder = Recorder()
    time.sleep(2)
    print('start')
    recorder.start()
    time.sleep(2)
    recorder.end()
    recorder.exit()
