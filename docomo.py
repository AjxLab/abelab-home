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


def goo(joke):
    ## -----*----- カタカナ化 -----*----- ##
    url = "https://api.apigw.smt.docomo.ne.jp/gooLanguageAnalysis/v1/hiragana?APIKEY={}"
    header = { 'Content-Type': 'application/json' }
    data = { 'sentence': joke, 'output_type': 'katakana' }

    for key in APIKEY:
        res = requests.post(url.format(key), headers=header, data=json.dumps(data))
        if check_health(res, False): return res

    return res


def jetrun(joke):
    ## -----*----- センシティブチェック -----*----- ##
    url = 'https://api.apigw.smt.docomo.ne.jp/truetext/v1/sensitivecheck?APIKEY={}'
    header = { 'Content-Type': 'application/x-www-form-urlencoded' }
    body = { 'text': joke }

    for key in APIKEY:
        res = requests.post(url.format(key), headers=header, data=body)
        if check_health(res, False): return res

    return res


def check_health(res, alert=True):
    ## -----*----- ステータスチェック -----*----- ##
    code = res.status_code
    try:
        assert code == requests.codes.ok
    except:
        return False

    return True


if __name__ == '__main__':
    print(goo('布団が吹っ飛んだ').json())
    print(jetrun('布団が吹っ飛んだ').json())
