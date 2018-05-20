# coding:utf-8
# description:
# author:duzhengjie
# time:2017/9/27 0027 上午 11:06
import socket
import threading

import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import sys
import select


class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print 'Got a client'

    def on_message(self, message):
        # self.func()
        threading.Thread(target=self.func).start()

    def func(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.connect(('localhost', 1717))
        readBannerBytes = 0
        bannerLength = 2
        readFrameBytes = 0
        frameBodyLength = 0
        frameBody = ''
        BUFFER_SIZE = 65536
        banner = {"version": 0,
                  "length": 0,
                  "pid": 0,
                  "realWidth": 0,
                  "realHeight": 0,
                  "virtualWidth": 0,
                  "virtualHeight": 0,
                  "orientation": 0,
                  "quirks": 0
                  }
        while True:
            chunk = s.recv(BUFFER_SIZE)
            length = len(chunk)
            # print('chunk(length=%d)' % length)
            cursor = 0
            while cursor < length:
                if readBannerBytes < bannerLength:
                    if readBannerBytes == 0:
                        banner["version"] = ord(chunk[cursor])
                    elif readBannerBytes == 1:
                        banner["length"] = bannerLength = ord(chunk[cursor])
                    elif readBannerBytes == 5:
                        banner["pid"] += (ord(chunk[cursor]) << 24)
                    elif readBannerBytes == 9:
                        banner["realWidth"] += (ord(chunk[cursor]) << 24)
                    elif readBannerBytes == 13:
                        banner["realHeight"] += (ord(chunk[cursor]) << 24)
                    elif readBannerBytes == 17:
                        banner["virtualWidth"] += (ord(chunk[cursor]) << 24)
                    elif readBannerBytes == 21:
                        banner["virtualHeight"] += (ord(chunk[cursor]) << 24)
                    elif readBannerBytes == 22:
                        banner["orientation"] += ord(chunk[cursor]) * 90
                    elif readBannerBytes == 23:
                        banner["quirks"] = ord(chunk[cursor])
                    cursor += 1
                    readBannerBytes += 1
                    if readBannerBytes == bannerLength:
                        print 'banner:', banner

                elif readFrameBytes < 4:
                    frameBodyLength += (ord(chunk[cursor]) << (readFrameBytes * 8))
                    cursor += 1
                    readFrameBytes += 1
                    # print 'headerbyte %d(val=%d)' % (readFrameBytes, frameBodyLength)
                else:
                    if length - cursor >= frameBodyLength:
                        # print 'bodyfin(len=%d,cursor=%d)' % (frameBodyLength, cursor)
                        frameBody = frameBody + chunk[cursor: cursor + frameBodyLength]
                        if (frameBody[0] != '\xFF') or (frameBody[1] != '\xD8'):
                            print 'Frame body does not start with JPG header'
                            sys.exit(1)
                        self.write_message(frameBody, binary=True)
                        cursor += frameBodyLength
                        frameBodyLength = readFrameBytes = 0
                        frameBody = ''
                    else:
                        # print 'body(len=%d)' % (length - cursor)
                        frameBody = frameBody + chunk[cursor: length]
                        frameBodyLength -= length - cursor
                        readFrameBytes += length - cursor
                        cursor = length

    def on_close(self):
        print 'Lost a client'


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r'/', IndexPageHandler),
                    (r'/ws', WebSocketHandler)
                    ]
        tornado.web.Application.__init__(self, handlers)


if __name__ == '__main__':
    ws_app = Application()
    server = tornado.httpserver.HTTPServer(ws_app)
    PORT = 9002
    server.listen(PORT)
    print 'Listening on port %d' % PORT
    tornado.ioloop.IOLoop.instance().start()
