import TkEasyGUI as sg
#import PySimpleGUI as sg
# PySimpleGUIの場合、MenuとMultiline周りでちょい修正あり

import sys
import os.path as pa

Path_name = ''
File_name = ''
Win_title = 'GAME Viewer'
Special={17:'⏬', 18:'⏫', 19:'⏩', 20:'⏪',
         21:'⏸', 22:'⏹'
         }  # 0x11 dn,0x12 up,0x13 rt,0x14 lt, 0x15 Home,0x16 Cls

MZFont = False  # 未実装なのでTrueにしちゃだめ

Font_name = ('RetroCompute',12)  #('MS Gotic',12)
# それっぽいフォント： https://www.dafont.com/retrocompute.font

Usage = '＃ GAME-MZでSaveしたプログラムを表示する：\n\n'\
        '・Fileメニュー＞Openで MZTファイルを選択すると、ファイル中の'\
        'プログラムリストが Programメニューに入ります。\n\n'\
        '・Fileメニュー＞Exitで終了します。\n\n'\
        '・メニューでProgramを選ぶとここに表示されます。\n'\
        '　ただしWindowsの流儀で禁則処理されてしまうのでご注意ください。\n'\
        '　カーソル移動文字はそれっぽい文字に、グラフィック文字は\\xhhに'\
        '変換して表示します。\n\n'\
        '　今後の課題：MZ文字フォントで表示する'

Usage2 = '* Display program files written in GAME-MZ:\n\n'\
        '- Select a tape image (.MZT) from File|Open menu.'\
        ' -> Program files in the image file appears in Program menu\n\n'\
        '- File|Exit to quit this program.\n\n'\
        '- Select a program from menu, then display program list in '\
        'this window.\n'


def load_file():
    global Path_name, File_name
    
    File_name = sg.popup_get_file(message='GAMEVIEW - File?',
                                  file_types=(('MZT Files', ('.mzt', '.m12')),),
                                  initial_folder=Path_name)
    if File_name == '':
        return None

    ptbl = []
    Path_name = pa.dirname(File_name)
    with open(File_name, 'rb') as fi:
        ptbl=[]

        count = 0
        while True:
            ofset = fi.tell()
            try:
                b=fi.read(128)
                if len(b)<128:
                    break
                flag=b[0]
                prog_name=''
                for i in range(1,17):
                    if b[i] < 20:
                        break
                    elif (b[i]>0xbf) :
                        prog_name += '<%02x>'%(b[i])
                    else:
                        prog_name += chr(b[i])
                siz = b[19]*256+b[18]
                # print(f'{ofset:04x}, {siz:04x} - {prog_name} [{flag}]')
                fi.read(siz)
            except IOError:
                break
            if prog_name == '':
                break
            ptbl.append([count, prog_name, ofset, siz, flag])
            # print(f'{prog_name} INDEX {count}')
            count += 1
    return ptbl


def getlist(pdesc):
    pno, pname, pofset, psize, pflg = pdesc
    
    with open(File_name, mode='rb') as fi:
        fi.seek(pofset+128)  # offsetはヘッダ先頭までのサイズ
        buf = fi.read(psize)  # sizeはペイロードのサイズ
        if len(buf) < psize:
            return ['']
        txt = ''
        pos = 0
        while pos <= len(buf):
            if (buf[pos] & 0xff) == 0xff:
                break
            lineno = buf[pos]*256 + buf[pos+1]
            if lineno == 0:
                break
            pos += 2
            line = ''
            while buf[pos] != 0:
                c = buf[pos]
                if MZFont:
                    line += chr(c)
                else:
                    if (c < 0x16) and (c > 0x10):
                        line += Special[c]
                    elif (c < 0x20) or (c > 0xbf):
                        line += '\\x%02x'%(c)
                    else:
                        line += chr(c)
                pos += 1
            pos += 1
            txt += '%d%s\n'%(lineno, line)
    return txt


def write_text(widget, txt):
    wigdget.update(value=txt)


if __name__ == '__main__':
    mitems = [['File', ['Open::-getfile-', 'Exit::-exit-']],
              ['Program',[]]]
    menu = sg.Menu(mitems, key='-mnu-')
    if MZFont:
        # Multiline -> Canvas
        # MZ700.fonでCanvas上に表示する(Scrollも)
        usg = Usage2
        buf = sg.Canvas(size=(640,400), key='-buf-')
        pass
    else:
        usg = Usage
        buf = sg.Multiline(default_text=usg, key='-buf-',
                       size=(80,20), font=Font_name,
                       readonly=True,   # PySimpleGUI> この属性なし
                       text_color='#000033', background_color='#f8f8f8',
                       expand_x=True, expand_y=True,
                       pad=0)
    lo = [[menu],[buf]]
    wn = sg.Window(Win_title, layout=lo, resizable=True)
    plst = []

    while True:
        e,v = wn.read()

        if (e is not None) and ('::' in e):
            dummy,e = e.split('::')

        if (e==sg.WINDOW_CLOSED) or (e=='-exit-'):
            break
        elif e=='-getfile-':
            plst = load_file()
            print(f'{File_name}\n{plst}\n---' )
            itm = []
            for x in wn['-mnu-'].items:  # PySimpleGUI> .MenuDefinition
                if x[0] != 'Program':
                    itm.append(x)
            prg = []
            for p in plst:
                # print(p[0])
                prg.append('%s::-prg-%d'%(p[1],p[0]))
            itm.append(['Program', prg])
            wn['-mnu-'].update(menu_definition=itm)  # TkEasyGUI0.2.76で対応
            wn.refresh()
        elif '-prg-' in e:
            idx = int(e[5:])
            txt = getlist(plst[idx])
            wn.set_title(Win_title+' - '+plst[idx][1])
            if MZFont:
                write_text(wn['-buf-'], txt)
            else:
                wn['-buf-'].update(text=txt)  # PySimpleGUI> value=txt
            wn.refresh()
        else:
            print(e, v)
    wn.close()
