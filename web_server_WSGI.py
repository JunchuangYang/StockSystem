#-*- coding:utf-8 -*-
# __author__ = 'lenovo'


import multiprocessing
import re
import socket

from dynamic import mini_frame


class WSGIServer(object):

    def __init__(self):
        """用来完成整体的控制"""
        # 1.创建套接字
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置当服务器先close,即服务器端4次挥手之后资源能立即释放，这样就保证了下次运行时可以立即使用刚才的端口
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 2. 绑定
        self.tcp_server_socket.bind(("", 7890))
        # 3. 变为监听套接字
        self.tcp_server_socket.listen(128)

    def service_client(self,new_socket):
        # 1.接受浏览器发送过来的请求,即http请求
        # get /HTTP/1.1
        # ....
        request = new_socket.recv(1024).decode("utf-8")
        request_lines = request.splitlines()
        print("")
        print(">"*20)
        print(request_lines)
        # GEt/index.html Http/1.1
        # get post put del
        file_name = ""
        ret = re.match(r"[^/]+(/[^ ]*)", request_lines[0])
        if ret:
            file_name = ret.group(1)

            if file_name == "/":
                file_name = "/index.html"
        # 2.返回http格式的数据，给浏览器-header + body
        # 2.1如果请求的资源不是以.py结尾的，那么就认为是静态资源（html/css/js/png/jpg）
        if not file_name.endswith(".html"):
            try:
                f = open("./static" + file_name,"rb")
            except:
                response = "HTTP/1.1 404 NOT FOUND\r\n"
                response += '\r\n'
                response += '------file not found------'
                # 将数据编码成urf-8的格式
                new_socket.send(response.encode("utf-8"))
            else:
                html_content = f.read()
                f.close()
                # 2.1 准备发送给浏览器的数据 --- header
                response = 'HTTP/1.1 200 OK\r\n'
                response += '\r\n'
                # 2.2准备发送个浏览器的数据 ---body
                # 将response header发送给浏览器
                new_socket.send(response.encode("utf-8"))
                # 将response body发送给浏览器
                new_socket.send(html_content)
        else :

            env = dict()
            env['PATH_INFO'] = file_name
            body = mini_frame.application(env,self.set_response_header)

            header = "HTTP/1.1 %s\r\n" % self.status

            for temp in self.headers:
                header += "%s:%s\r\n" % (temp[0],temp[1])

            header += "\r\n"
            response = header + body
            new_socket.send(response.encode("utf-8"))
        # 关闭套接字
        new_socket.close()

    # 把服务器的信息和回过来的框架的信息合并在一起
    def set_response_header(self,status,headers):
        self.status = status
        self.headers = [("server","mini_web v8.8")]
        self.headers +=headers

    def run_forever(self):
        while True:
            # 4. 等待新客户端的链接
            new_socket, client_addr = self.tcp_server_socket.accept()
            # 5. 为这个客户端服务
            p = multiprocessing.Process(target=self.service_client, args=(new_socket,))
            p.start()
            new_socket.close()

        # 关闭监听套接字
        self.tcp_server_socket.close()

def main():
    """控制整体，创建一个web服务器对象，然后调用这个对象的run_forever方法运行"""
    wsgi_server = WSGIServer()
    wsgi_server.run_forever()

if __name__ == '__main__':
    main()
