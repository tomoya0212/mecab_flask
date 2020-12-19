#import sys,io
import pymysql
from flask import Flask,render_template,request,redirect,session,url_for,json,jsonify
import MeCab
from collections import Counter

#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app=Flask(__name__)
app.secret_key="secret"

#Mysqlオプション
MYSQL_OPTIONS={
    "host":"127.0.0.1",
    "port":3306,
    "user":"root",
    "passwd":"admin",
    "db":"lab_impressions_db"
}

#データベースコネクション獲得
def getConnection():
    conn=pymysql.connect(
        host=MYSQL_OPTIONS["host"],
        port=MYSQL_OPTIONS["port"],
        user=MYSQL_OPTIONS["user"],
        passwd=MYSQL_OPTIONS["passwd"],
        db=MYSQL_OPTIONS["db"],
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

def get_lab_list():
    conn=getConnection()
    try:
        with conn.cursor() as cursor:
            sql="SELECT DISTINCT lab_name FROM test_table;"
            cursor.execute(sql)
            result=cursor.fetchall()
    finally:
        conn.close()
    result_list=list()
    for row in result:
        result_list.append({"lab_name":row["lab_name"]})
    return result_list

def get_year_list():
    conn=getConnection()
    try:
        with conn.cursor() as cursor:
            sql="SELECT DISTINCT year FROM test_table;"
            cursor.execute(sql)
            result=cursor.fetchall()
    finally:
        conn.close()
    result_list=list()
    for row in result:
        result_list.append({"year":row["year"]})
    return result_list

#形態素解析用関数
def mecab_analysis(impressions_list):
    tagger=MeCab.Tagger(r"-d /home/ai4/anaconda3/envs/urawaki_nlp7_mecab_download/lib/python3.6/site-packages/ipadic/dicdir -O chasen")
    tagger.parse('')
    nodes=tagger.parseToNode(str(impressions_list))
    output=[]
    while nodes:
        if nodes.surface != "":
            word_type=nodes.feature.split(",")[0]
            if word_type in ["名詞"]:
                output.append(nodes.surface)
        nodes=nodes.next
        if nodes is None:
            break
    return output

#lab_valとyear_valの値によって取得するデータベースを分ける
def get_student_impressions(select_lab, select_year):
    conn=getConnection()
    try:
        with conn.cursor() as cursor:
            sql="SELECT author_id, sentence_id, impressions, label FROM test_table WHERE lab_name=%s AND year=%s;"
            cursor.execute(sql,(str(select_lab), str(select_year)))
            result=cursor.fetchall()
    finally:
        conn.close()
    result_list=list()
    for row in result:
        result_list.append({"author_id":row["author_id"],"sentence_id":row["sentence_id"],"impressions":row["impressions"],"label":row["label"]})
    return result_list

#研究室と年度ごとの感想文のみ取り出すために作った関数(たぶんムダw)
def get_student_impressions2(select_lab, select_year):
    conn=getConnection()
    try:
        with conn.cursor() as cursor:
            sql="SELECT impressions FROM test_table WHERE lab_name=%s AND year=%s;"
            cursor.execute(sql,(str(select_lab), str(select_year)))
            result=cursor.fetchall()
    finally:
        conn.close()
    result_list=list()
    for row in result:
        result_list.append({"impressions":row["impressions"]})
    return result_list

#非同期通信用(研究室ごとに年度を取り出す)
def select_year_def(lab_name):
    conn=getConnection()
    try:
        with conn.cursor() as cursor:
            sql="SELECT DISTINCT year FROM test_table WHERE lab_name=%s;"
            cursor.execute(sql,(str(lab_name)))
            result=cursor.fetchall()
    finally:
        conn.close()
    result_list=list()
    for row in result:
        result_list.append({"year":row["year"]})
    return result_list

@app.route("/")
def login2():
    return render_template("select_impressions.html", lab_list=get_lab_list(), year_list="", impressions_list=None, len_posi=None, len_nega=None)

#研究室によって年度表示を変更する非同期通信
@app.route("/ajax_lab", methods=["GET","POST"])
def ajax_001():
    impressions_list=None
    if request.method == "POST":
        select_lab_name=request.json["lab"]
        print(select_lab_name)
        json_for_js=select_year_def(select_lab_name)
    return jsonify(json_for_js)

@app.route("/select", methods=["GET","POST"])
def select():
    impressions_list=None
    if request.method == "POST":
        select_lab_name=request.form["lab"]
        select_year_id=request.form["year"]
        impressions_list=get_student_impressions(select_lab_name, select_year_id)
        impressions_list2=get_student_impressions2(select_lab_name,select_year_id)
        mecab_impressions=mecab_analysis(impressions_list2)#形態素解析
        #-----------単語出現数調査-ここから----------#
        counter=Counter(mecab_impressions)
        for word, count in counter.most_common():
            if len(word) > 1 and word != "impressions" and count > 1:
                print("%s,%d" % (word,count))
        #-----------単語出現数調査-ここまで----------#

        impressions_list_author = [] #感想記入者別に感想を入れる
        author = impressions_list[0]['author_id']
        tmp_list = [impressions_list[0]['impressions']]
        for i in range(1,len(impressions_list)):
            if author == impressions_list[i]['author_id']:
                tmp_list.append(impressions_list[i]['impressions'])
            else:
                impressions_list_author.append(tmp_list)
                tmp_list = []
                tmp_list.append(impressions_list[i]['impressions'])
                author += 1
        nega_list=[]
        posi_list=[]
        for i in range(len(impressions_list)):
            if '◎' == impressions_list[i]['label']:
                posi_list.append(impressions_list[i]['impressions'])
            else:
                nega_list.append(impressions_list[i]['impressions'])
        len_posi=len(posi_list)
        len_nega=len(nega_list)
        tmp1 = len(posi_list)/(len(posi_list)+len(nega_list)) 
        tmp2 = len(nega_list)/(len(posi_list)+len(nega_list))
        rate = [round(tmp1,2)*100,round(tmp2,3)*100]
    return render_template("select_impressions.html", select_lab_name=select_lab_name, select_year_id=select_year_id, lab_list=get_lab_list(), year_list=select_year_def(select_lab_name), impressions_list=impressions_list_author,posi_list=posi_list, nega_list=nega_list,rate=rate,len_posi=len_posi,len_nega=len_nega) #感想記入者別に表示する用

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)