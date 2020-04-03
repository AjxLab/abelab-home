# -*- coding: utf-8 -*-
import os
import re
import time
import yaml
import numpy as np
import wave
import pyaudio
import threading
import requests
import pycrawl
import recorder
import docomo
import warnings
warnings.simplefilter("ignore", DeprecationWarning)


class Engine():
    def __init__(self):
        ## -----*----- コンストラクタ -----*----- ##
        self.config = yaml.load(open('config/wave.yml'), Loader=yaml.SafeLoader)
        # ストリーマ
        pa = pyaudio.PyAudio()
        self.streamer = pa.open(
            format=pyaudio.paFloat32,
            channels=self.config['channels'],
            rate=self.config['rate']*2,
            input=True,
            output=False,
            frames_per_buffer=self.config['chunk'],
        )
        # 立ち上がり・下がり検出数
        self.cnt_edge = {'up': 0, 'down': 0}
        # 音量・閾値などの状態管理
        self.state = {'amp': 0, 'total': 0, 'n': 0, 'border': 9999, 'average': 0}
        # フラグを初期化
        self.is_stream = False
        self.is_exit = False
        self.talk_dajare = False
        # 録音器
        self.record = recorder.Recorder()
        # HEXAGONの返答
        self.msg = '話しかけてください。'

        self.start()


    def start(self):
        ## -----*----- 検出開始 ------*----- ##
        status = 0
        # 閾値更新を並列化
        thread = threading.Thread(target=self.update_border)
        thread.start()

        self.past_time = time.time()

        print('   HEXAGON： %s' % self.msg)

        try:
            while not self.is_exit:
                if time.time() - self.past_time > 0.5:
                    self.reset_state()
                self.state['n'] += 1
                self.detection()
        except KeyboardInterrupt:
            self.is_exit = True
            status = 1

        self.record.exit()
        return status


    def detection(self):
        ## -----*----- 命令検出 -----*----- ##
        wav = np.fromstring(self.streamer.read(self.config['chunk'], exception_on_overflow=False), np.float32)
        wav *= np.hanning(self.config['chunk'])
        # パワースペクトル
        x = np.fft.fft(wav)
        x = [np.sqrt(c.real ** 2 + c.imag ** 2) for c in x]
        # バンドパスフィルタ（100~5000 Hz）
        x = x[
            int((self.config['chunk'] / (self.config['rate'] * 2)) * 100):
            int((self.config['chunk'] / (self.config['rate'] * 2)) * 5000)
        ]

        # Amp値・平均値の算出
        self.state['amp'] = sum(x)
        self.state['total'] += self.state['amp']
        self.state['average'] = self.state['total'] / self.state['n']

        # 立ち上がり・下がり検出
        if self.up_edge() and not self.is_stream:
            self.record.start()
            self.state['border'] = self.state['average']
            self.is_stream = True
        if self.down_edge() and self.is_stream:
            self.record.end()
            self.reset_state()
            self.is_stream = False
            self.reply()


    def up_edge(self):
        ## -----*----- 立ちがり検出 -----*----- ##
        if self.state['amp'] >= self.state['border']:
            self.cnt_edge['up'] += 1
        if self.cnt_edge['up'] > 5:
            return True
        return False


    def down_edge(self):
        ## -----*----- 立ち下がり検出 -----*----- ##
        if self.state['average'] <= self.state['border']:
            self.cnt_edge['down'] += 1
        if self.cnt_edge['down'] > 15:
            self.cnt_edge['up'] = 0
            self.cnt_edge['down'] = 0
            return True
        return False


    def update_border(self):
        ## -----*----- 閾値を更新 -----*----- ##
        offset = range(50, 201, 10)
        while not self.is_exit:
            time.sleep(0.2)
            if self.cnt_edge['up'] < 3 and not self.record.b_stream:
                if int(self.state['average'] / 20) > len(offset) - 1:
                    i = len(offset) - 1
                else:
                    i = int(self.state['average'] / 20)
                self.state['border'] = pow(10, 1.13) * pow(self.state['average'], 0.72)


    def reset_state(self):
        ## -----*----- 状態をリセット ------*------ ##
        self.state['total'] = self.state['average'] * 15
        self.state['n'] = 15
        if self.state['average'] >= self.state['amp']:
            self.cnt_edge['up'] = 0
        self.past_time = time.time()


    def reply(self):
        ## -----*----- 返信 -----*----- ##
        b_talk = False

        res = docomo.speech_recognition(self.config['wav_path'])
        if docomo.check_health(res):
            speech = res.json()['text']
            if speech =='':
                return

            print('   You：     {}'.format(res.json()['text']))

            # ダジャレを評価
            if self.talk_dajare:
                self.talk_dajare = False
                speech = speech.replace('。', '')
                url = 'http://abelab.dev:8080/joke/judge?joke={}'.format(speech)
                res = requests.get(url)
                if docomo.check_health(res):
                    if res.json()['is_joke']:
                        url = 'http://abelab.dev:8080/joke/evaluate?joke={}'.format(speech)
                        res = requests.get(url)
                        if docomo.check_health(res):
                            self.msg = '「{}」は{:1.1f}点です。'.format(speech, res.json()['score'])
                            b_talk = True
                    else:
                        self.msg = '「{}」はダジャレではありません。'.format(speech)
                        b_talk = True

            # フリーワード検索
            words = ['を検索', 'の意味', 'とは']
            if not b_talk:
                for w in words:
                    if re.match(w, speech):
                        target = re.match(r'.+{}'.format(w), speech).group()
                        target = target.replace(w, '')
                        if not target == '':
                            doc = pycrawl.PyCrawl('https://ja.wikipedia.org/wiki/{}'.format(target))
                            self.msg = doc.css('.mw-parser-output').css('p').inner_text()
                            self.msg = re.sub(r'（.+）', '', self.msg)
                            self.msg = re.sub(r'\[\d\]', '', self.msg)
                            b_talk = True
                            break

            # ダジャレを評価
            words = ['(ダジャレ|地口).*(判定|評価)']
            if not b_talk:
                for w in words:
                    if re.match(w, speech):
                        self.msg = 'ダジャレを評価します。'
                        b_talk = True
                        self.talk_dajare = True

            # ダジャレを検索
            words = ['ダジャレ', '地口', 'ジョーク']
            if not b_talk:
                for w in words:
                    if re.match(w, speech):
                        url = 'https://script.google.com/macros/s/AKfycbx2h8jWePcUxszENqm4EqO7gk1bMDqGQKOUSPfQkDKtdwfoxAM/exec?randNum=1'
                        res = requests.get(url)
                        if docomo.check_health(res):
                            self.msg = res.json()['jokes'][0]['joke']
                            b_talk = True
                            break

            # 自己紹介を求める
            words = ['あなたは誰', 'あなたはだれ', 'あなたの名前は']
            if not b_talk:
                for w in words:
                    if re.match(w, speech):
                        self.msg = '初めまして。私の名前はHEXAGON、阿部健太朗さんによって開発されたお手伝いbotです。'
                        b_talk = True
                        break

            # 自己紹介をする
            words = ['私の名前は', '僕の名前は', '俺の名前は']
            if not b_talk:
                for w in words:
                    if re.match(w, speech):
                        name = speech.replace(w, '').replace('です', '').replace('。', '')
                        self.msg = 'こんにちは。{}さん'.format(name)
                        b_talk = True
                        break

            # 挨拶
            words = ['初めまして', 'はじめまして', 'おはよう', 'おはようございます', 'こんにちは', 'こんばんは']
            if not b_talk:
                for w in words:
                    if re.match(w, speech):
                        self.msg = w + '。'
                        b_talk = True
                        break

            # 終了
            words = ['さようなら', '終了']
            if not b_talk:
                for w in words:
                    if re.match(w, speech):
                        self.is_exit = True
                        self.msg = 'また遊んでくださいね。'
                        b_talk = True

        if not b_talk:
            self.msg = 'すみません、よくわかりません。'
        time.sleep(0.2)
        print('   HEXAGON： %s' % self.msg)
        os.system('say {}'.format(self.msg))

