# -*- coding: utf-8 -*-
import pypyodbc, json
from django.shortcuts import render
import collections
from django.http import JsonResponse
from django.http import HttpResponse
runnerid_session = 0

#資料庫連接語法
conn = pypyodbc.connect('DRIVER={SQL Server};SERVER=.;DATABASE=RPi0116;UID=sa;PWD=nfu123@@@',autocommit=True)
cursor = conn.cursor()

#取得跑者id，並將資料做成下拉式選單回傳
def get_runnerid(runneridrecept):
    cursor.execute("select distinct Runner_id from IDTable order by Runner_id DESC ") #查詢有哪些跑者
    rows = list(cursor.fetchall())
    #開始串接跑者id下拉式選單的html語法字串，當中的onchange方法讓選單改變時會觸發javascript的onchangeFunc()
    s = '<select id="runnerid" name="runnerid" class="form-control" style="height:5em;" onchange="onchangeFunc()"><option value=" "> </option>'
    #如果接收到的值為0，代表第一次讀取，直接全部列出來
    if runneridrecept == 0:
        for i in rows:
            s += '<option value="%d">%d</option>' % (int(i[0]), int(i[0]))
        s += '</select>'
    #如果不是0，做判斷讓傳送進來的那個值相對應的選單選項預設為selected，設定為預選值
    else:
        for i in rows:
            if i[0] == int(runneridrecept):
                s += '<option value="%d" selected>%d</option>' % (int(i[0]), int(i[0]))
            else:
                s += '<option value="%d">%d</option>' % (int(i[0]), int(i[0]))
        s += '</select>'
    #最後回傳下拉式選單
    return (s)

#取得測試id，並將資料做成下拉式選單回傳，其中資料處理同上
def get_testid(testidrecept):
    global runnerid_session
    cursor.execute("select distinct Test_id from IDTable where Runner_id=%s order by Test_id DESC "%runnerid_session)
    rows = list(cursor.fetchall())
    s = '<select name="testid" class="form-control" style="height:5em;">'
    if testidrecept == 0:
        for i in rows:
            s += '<option value="%d">%d</option>' % (int(i[0]), int(i[0]))
    else:
        for i in rows:
            if i[0] == int(testidrecept):
                s += '<option value="%d" selected>%d</option>' % (int(i[0]), int(i[0]))
            else:
                s += '<option value="%d" >%d</option>' % (int(i[0]), int(i[0]))
    s += '</select>'
    return (s)

#取得所有資料以一個表格顯示，現在先不用這方法，之後需要再做修改
'''
def get_TestData(inp):
    sql = 'SELECT dbo.BasicData.Test_id, dbo.Runner.Runner_id, dbo.BasicData.Date, dbo.BasicData.Time, dbo.SpeedTest.StartTime,dbo.BasicData.RPi1, dbo.BasicData.RPi2, dbo.BasicData.RPi3, dbo.BasicData.RPi4, dbo.SpeedTest.RPi1S, dbo.SpeedTest.RPi2S, dbo.SpeedTest.RPi3S, dbo.SpeedTest.RPi4S, dbo.SpeedTest.RPi1T, dbo.SpeedTest.RPi2T, dbo.SpeedTest.RPi3T, dbo.SpeedTest.RPi4T FROM dbo.BasicData INNER JOIN dbo.Runner ON dbo.BasicData.Runner_id = dbo.Runner.Runner_id INNER JOIN dbo.SpeedTest ON dbo.BasicData.Test_id = dbo.SpeedTest.Test_id WHERE dbo.SpeedTest.Test_id=%s'%inp
    cursor.execute(sql)

    table = '<table class="table table-striped">'
    columnName = ['Test_id', 'Runner_id', 'Date', 'Time', 'StartTime', 'RPi1', 'RPi2', 'RPi3', 'RPi4', 'RPi1S', 'RPi2S', 'RPi3S', 'RPi4S', 'RPi1T', 'RPi2T', 'RPi3T', 'RPi4T']
    rows = list(cursor.fetchall())

    for i in range(len(rows[0])):
        table += '<tr><td>%s</td><td>%s</td></tr>' % (columnName[i], str(rows[0][i]))
    table += '</table>'

    return (table)
'''

#取得BasicData表格資料
def get_BasicData(inp):
    #取得表格欄位名稱
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'BasicData'")
    columnName = list(cursor.fetchall())
    #取得表格資料
    cursor.execute("SELECT * FROM [RPi0116].[dbo].[BasicData] WHERE Test_id=%s"%inp)
    rows = list(cursor.fetchall())

    table_BasicData = '<div class="page-header"><h1>BasicData</h1></div><table class="table table-striped">'
    #將欄位名稱與表格內容一一做配對然後再以html碼包起來
    try:
        for i in range(len(columnName)):
            table_BasicData += '<tr><td>%s</td><td>%s</td></tr>'%(str(columnName[i][0]),str(rows[0][i]))
        table_BasicData += '</table>'
    except: #表格資料有誤時處理
        table_BasicData += '<tr><td>data lost or error</td></tr>'
        table_BasicData += '</table>'
    return table_BasicData

#取得SpeedTest表格資料，資料處理方式同BasicData
def get_SpeedTest(inp):
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'SpeedTest'")
    columnName = list(cursor.fetchall())
    cursor.execute("SELECT * FROM [RPi0116].[dbo].[SpeedTest] WHERE Test_id=%s"%inp)
    rows = list(cursor.fetchall())

    table_SpeedTest = '<div class="page-header"><h1>SpeedTest</h1></div><table class="table table-striped">'
    try:
        for i in range(len(columnName)):
            table_SpeedTest += '<tr><td>%s</td><td>%s</td></tr>'%(str(columnName[i][0]),str(rows[0][i]))
        table_SpeedTest += '</table>'
    except:
        table_SpeedTest += '<tr><td>data lost or error</td></tr>'
        table_SpeedTest += '</table>'
    return table_SpeedTest

#取得左腳壓力資料
def get_L_Voltage(inp):
    #執行SQL Server裡的預存程序，取出壓力值
    cursor.execute("EXEC L_TheVoltage %s"%inp)
    rows = list(cursor.fetchall())
    leftFootKgTime = []  #壓力時間
    leftFootKg = [[], [], [], [], [], [], [], [],[]]  #各channel值
    for a, b, c, d, e, f, g, h, i in rows:
        leftFootKgTime.append(a)
        leftFootKg[1].append(b)
        leftFootKg[2].append(c)
        leftFootKg[3].append(d)
        leftFootKg[4].append(e)
        leftFootKg[5].append(f)
        leftFootKg[6].append(g)
        leftFootKg[7].append(h)
        leftFootKg[8].append(i)
    #最後將值包起來回傳，時間與壓力值分開是因為時間資料要做資料處理
    return [leftFootKgTime,leftFootKg]

#取得右腳壓力資料，說明同取得左腳
def get_R_Voltage(inp):
    #執行SQL Server裡的預存程序，取出壓力值
    cursor.execute("EXEC R_TheVoltage %s"%inp)
    rows = list(cursor.fetchall())
    rightFootKgTime = []
    rightFootKg = [[], [], [], [], [], [], [], [],[]]
    for a, b, c, d, e, f, g, h, i in rows:
        rightFootKgTime.append(a)
        rightFootKg[1].append(b)
        rightFootKg[2].append(c)
        rightFootKg[3].append(d)
        rightFootKg[4].append(e)
        rightFootKg[5].append(f)
        rightFootKg[6].append(g)
        rightFootKg[7].append(h)
        rightFootKg[8].append(i)
    return [rightFootKgTime,rightFootKg]

#主畫面資料處理
def show(request):
    runneridlist = get_runnerid(0) #此為第一次讀取網頁的預設值，呼叫讀取跑者id的function，先傳0進去做處理
    testidlist = '<select id="runnerid" name="testid" class="form-control" style="height:5em;"></select>'
    #runnerid_session = 0
    leftFoot = [[], [], [], [], [], [], [], [],[]]
    rightFoot = [[], [], [], [], [], [], [], [],[]]
    global runnerid_session
    table_BasicData = ''
    table_SpeedTest = ''
    state = [0,0]
    #selectedRunnerID = request.GET.get('runnerid')

    #網頁的跑者id下拉式選單選擇送出表單時，在這邊取得進行判斷，記得request的GET與POST要分清楚
    #如果name名為runnerid在收到的表單裡則做以下處理
    if 'runnerid' in request.GET:
        #request.GET.get('runnerid')為取得name為runnerid的值，在這邊先將值存起來，做後續預選值的問題
        runnerid_session = request.GET.get('runnerid')
        #然後將值送到取得跑者id得方法再重新做下拉式選單
        runneridlist = get_runnerid(request.GET.get('runnerid'))
        #選取了跑者id後，接著呼叫方法取得測試id，首先傳0進去
        testidlist = get_testid(request.GET.get('runnerid'))
        state[0] = runnerid_session

    # 如果name名為mybtn在收到的表單裡則做以下處理
    if 'mybtn' in request.GET:
        #這邊將剛剛存起來的runnerid_session傳到方法，重新取得跑者id與測試id
        runneridlist = get_runnerid(runnerid_session)
        testidlist = get_testid(request.GET.get('testid'))
        #將測試id傳進4個方法，分別取得左右腳壓力及BasicData、SpeedTest表格資料
        inp = str(request.GET.get('testid'))
        leftFoot = get_L_Voltage(inp)
        rightFoot = get_R_Voltage(inp)
        table_BasicData = get_BasicData(inp)
        table_SpeedTest = get_SpeedTest(inp)
        state = [int(runnerid_session),int(inp)]
    #最後回傳給網頁，回傳request繼續給網頁做回傳值，還有網頁檔作業面顯示，還有許多參數，參數要用字典型態，leftFoot[0]及leftFoot[1]為回傳的串列取出資料
    return render(request, 'show.html', {'state':state,'leftFootTime':leftFoot[0], 'leftFootKG':leftFoot[1],'rightFootTime':rightFoot[0], 'rightFootKG':rightFoot[1],'runneridlist':runneridlist, 'testidlist': testidlist, 'table_BasicData': table_BasicData, 'table_SpeedTest': table_SpeedTest})
    #return render(request,'show.html', {'testidlist':testidlist, 'data1':data1, 'data2':data2, 'data3':data3, 'data4':data4, 'data5':data5, 'data6':data6, 'data7':data7, 'data8':data8, 'data9':data9,'Test_id': Test_id, 'Runner_id': Runner_id, 'Date': Date, 'Time': Time, 'StartTime': StartTime, 'RPi1': RPi1, 'RPi2': RPi2, 'RPi3': RPi3, 'RPi4': RPi4,'RPi1S': RPi1S, 'RPi2S': RPi2S, 'RPi3S': RPi3S, 'RPi4S': RPi4S, 'RPi1T': RPi1T, 'RPi2T': RPi2T, 'RPi3T': RPi3T, 'RPi4T': RPi4T})
    #return render(request, 'show.html',{'testidlist': testidlist, 'data1': data1, 'data2': data2, 'data3': data3, 'data4': data4, 'data5': data5, 'data6': data6, 'data7': data7, 'data8': data8,'data9': data9, 'table_BasicData': table_BasicData, 'table_SpeedTest': table_SpeedTest})
    #return render(request, 'show.html',{'testidlist': testidlist, 'data1': data1, 'data2': data2, 'data3': data3, 'data4': data4, 'data5': data5, 'data6': data6, 'data7': data7, 'data8': data8,'data9': data9, 'testData':testData})

def addRunner(request):
    runnerTableColumnName = collections.OrderedDict()
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Runner'")
    #runnerTableColumnName = list(cursor.fetchall())
    for d in list(cursor.fetchall()):
        runnerTableColumnName.update({d[0]: d[0]})
    return render(request, 'addRunner.html',{'runnerTableColumnName':runnerTableColumnName})