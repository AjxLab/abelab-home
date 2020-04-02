#!/usr/bin/env python
import os
import time
import shutil
import threading
import engine
import docomo
import footer


logo = \
'''
H    H  EEEEEE  X   X   AAAA    GGGG    OOOO   N   N
H    H  E        X X   AA  AA  G    G  O    O  NN  N
HHHHHH  EEEEEE    X    AAAAAA  G       O    O  N N N
H    H  E        X X   AA  AA  G  GGG  O    O  N  NN
H    H  EEEEEE  X   X  AA  AA   GGGGG   OOOO   N   N
'''
len_logo = len(logo.split('\n')[1])
width = shutil.get_terminal_size()[0]
logo = [' '*((width-len(line))//2) + line for line in logo.split('\n')]
logo = '\n'.join(logo)

os.system('clear')
print('''
     Welcome to

%s


     HEXAGON is an interactive chatbot.
     This implementation by Tatsuya Abe 2020.



''' % logo)

try:
    t = threading.Thread(target=engine.start)
    t.start()

    msg = '話しかけてください。'
    while True:
        print('   HEXAGON： %s' % msg)
        # HEXAGON終了
        if msg == 'さようなら。':
            footer.footer_exit(0)

        text = input('   You：     ')
        msg = engine.make_reply(text)

except KeyboardInterrupt:
    footer.footer_exit(1)
