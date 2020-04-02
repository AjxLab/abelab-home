'''
docomo API
 - Powered by アドバンスト・メディア
 - Powered by NTTテクノクロス
 - Powered by goo
 - Powered by Jetrun
'''

import requests
import json
import datetime

try:
    APIKEY = open('config/docomo-token').read().split('\n')
    if '' in APIKEY: APIKEY.remove('')
except:
    print('Configuration file does not exist')
    exit(0)


def reading(text):
    ## -----*----- カタカナ化 -----*----- ##
    url = "https://api.apigw.smt.docomo.ne.jp/gooLanguageAnalysis/v1/hiragana?APIKEY={}"
    header = { 'Content-Type': 'application/json' }
    data = { 'sentence': text, 'output_type': 'katakana' }

    for key in APIKEY:
        res = requests.post(url.format(key), headers=header, data=json.dumps(data))
        if check_health(res): return res

    return res


def sensitive(text):
    ## -----*----- センシティブチェック -----*----- ##
    url = 'https://api.apigw.smt.docomo.ne.jp/truetext/v1/sensitivecheck?APIKEY={}'
    header = { 'Content-Type': 'application/x-www-form-urlencoded' }
    body = { 'text': text }

    for key in APIKEY:
        res = requests.post(url.format(key), headers=header, data=body)
        if check_health(res): return res

    return res


def speech_recognition(wav_path):
    ## -----*----- 音声認識 -----*----- ##
    url = 'https://api.apigw.smt.docomo.ne.jp/amiVoice/v1/recognize?APIKEY={}'
    file = {'a': open(wav_path, 'rb'), 'v':'on'}

    for key in APIKEY:
        res = requests.post(url.format(key), files=file)
        if check_health(res): return res

    return res


def check_health(res):
    ## -----*----- ステータスチェック -----*----- ##
    code = res.status_code
    try:
        assert code == requests.codes.ok
    except:
        return False

    return True


if __name__ == '__main__':
    print(speech_recognition('wave/speech.wav').json())
