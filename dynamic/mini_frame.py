#-*- coding:utf-8 -*-
__author__ = 'lenovo'

import re
from pymysql import connect
import urllib.parse
import logging

URL_FUNC_DICR = dict()


def data(sql,templates,content):

    conn = connect(host="localhost",port=3306,user="root",password="root",database="stock_db")
    cs = conn.cursor()
    cs.execute(sql)
    my_stock_info = cs.fetchall()
    cs.close()

    html = ""
    conn.close()
    for item in my_stock_info:
        str1 = templates
        for i in range(0,len(item)):
            str1 = re.sub(r"%s",str(item[i]),str1,1)
        html += str1

    return re.sub(r"\{%content%\}", html ,content)


def route(url):
    def set_func(func):
        URL_FUNC_DICR[url]=func
        def call_func(*args,**kwargs):
            return func(*args,**kwargs)
        return call_func
    return set_func

@route('/index.html')
def index(ret):
    with open('./templates/index.html',encoding='utf-8') as f:
        content = f.read()

    templates ="""
    <tr>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td><input type="button" value="添加" id="toAdd" name="toAdd" systemIdValue="%s"/> </td>
    </tr>
    """
    sql = "select * ,code from info;"
    return  data(sql,templates,content)

@route('/center.html')
def center(ret):
    with open('./templates/center.html',encoding='utf-8') as f:
        content = f.read()
    templates ="""
    <tr>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>
        <a type="button" class="btn btn-default btn-xs" href="/update/%s.html">
        <span class="glyphicon glyphicon-star" aria-hidden="true"></span>修改</a>
    </td>
    <td><input type="button" value="删除" id="toDel" name="toDel" systemIdValue="%s"/> </td>
    </tr>
    """
    sql = "select i.code,i.short,i.chg,i.turnover,i.price,i.highs,f.note_info ,i.code,i.code from info as i inner join focus as f on " \
          "i.id=f.info_id;"
    return  data(sql,templates,content)

# 给路由添加正则表达式的原因：在实际开发时，url中往往会带有很多参数，例如/add/000007.html中000007就是参数，
# 如果没有正则的话，那么就需要编写N次@route来进行添加 url对应的函数 到字典中，此时字典中的键值对有N个，浪费空间
# 而采用了正则的话，那么只要编写1次@route就可以完成多个 url例如/add/00007.html /add/000036.html等对应同一个函数，
# 此时字典中的键值对个数会少很多
@route(r"/del/(\d+)\.html")
def add_del(ret):
    #获取股票代码
    stock_code = ret.group(1)


    # 2. 判断试下是否有这个股票代码
    conn = connect(host='localhost',port=3306,user='root',password='root',database='stock_db',charset='utf8')
    cs = conn.cursor()
    sql = """select * from info where code=%s;"""
    cs.execute(sql, (stock_code,))

    # 如果没有这个股票代码，那么就认为是非法请求
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "没有这支股票，大哥 ，我们是创业公司，请手下留情..."

    # 3.判断以下是否已经关注过
    sql = """ select * from info as i inner join focus as f on i.id=f.info_id where i.code=%s;"""
    cs.execute(sql, (stock_code,))
    # 如果查出来了，那么表示已经关注过
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "操作非法..."
    # 4. 取消关注
    sql = """delete from focus where info_id=(select id from info where code=%s);"""
    cs.execute(sql, (stock_code,))
    conn.commit()
    cs.close()
    conn.close()

    return "删除成功...."

@route(r"/add/(\d+)\.html")
def add_focus(ret):
    #获取股票代码
    stock_code = ret.group(1)

    # 2. 判断试下是否有这个股票代码
    conn = connect(host='localhost',port=3306,user='root',password='root',database='stock_db',charset='utf8')
    cs = conn.cursor()
    sql = """select * from info where code=%s;"""
    cs.execute(sql, (stock_code,))

    # 如果没有这个股票代码，那么就认为是非法请求
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "没有这支股票，大哥 ，我们是创业公司，请手下留情..."

    # 3.判断以下是否已经关注过
    sql = """ select * from info as i inner join focus as f on i.id=f.info_id where i.code=%s;"""
    cs.execute(sql, (stock_code,))
    # 如果查出来了，那么表示已经关注过
    if cs.fetchone():
        cs.close()
        conn.close()
        return "已经关注过了，请勿重复关注..."
    # 4. 添加关注
    sql = """insert into focus (info_id) select id from info where code=%s;"""
    cs.execute(sql, (stock_code,))
    conn.commit()
    cs.close()
    conn.close()

    return "关注成功...."

@route(r"/update/(\d+)\.html")
def update_page(ret):
    with open("./templates/update.html",encoding="utf-8") as f:
        content = f.read()
    stock_code = ret.group(1)

    conn = connect(host='localhost',port=3306,user='root',password='root',database='stock_db',charset='utf8')
    cs = conn.cursor()
    sql = """select f.note_info from focus as f inner join info as i on i.id=f.info_id where i.code =%s;"""
    cs.execute(sql, (stock_code,))
    stock_info = cs.fetchone()
    note_info = stock_info[0]
    cs.close()
    conn.close()

    content = re.sub(r"\{%note_info%\}",note_info,content)
    content = re.sub(r"\{%code%\}",stock_code,content)

    return content


@route(r"/update/(\d+)/(.*)\.html")
def save_update_page(ret):
    stock_code = ret.group(1)
    stock_info = urllib.parse.unquote(ret.group(2))

    sql="""update focus set note_info =%s where info_id = (select id from info where code=%s);"""
    conn = connect(host='localhost',port=3306,user='root',password='root',database='stock_db',charset='utf8')
    cs = conn.cursor()
    cs.execute(sql,(stock_info,stock_code,))
    conn.commit()
    cs.close()
    conn.close()

    return "修改成功"

# environ 字典属性; start_response:函数的引用
def application(environ,start_response):
    start_response('200 OK',[('content-Type','text/html;charset=utf-8')])

    file_name = environ['PATH_INFO']

    logging.basicConfig(level = logging.INFO,
                        filename = './log.txt',
                        filemode = 'a',
                        format = ('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s:%(message)s'))
    logging.info("访问的是%s" % file_name)
    try:
        for url,func in URL_FUNC_DICR.items():
            ret = re.match(url,file_name)
            if ret:
                return func(ret)
        else:
            logging.warning("没有对应的函数")
            return "请求的url(%s)没有对应的函数...." % file_name
    except Exception as ret:
        return "产生异常 %s" %str(ret)
