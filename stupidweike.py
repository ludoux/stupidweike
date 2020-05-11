# -*- coding: UTF-8 -*-
import re
import requests
import json
import time
import os, sys
from contextlib import closing

def down(url, path):
    try:
        global headers
        with closing(requests.get(url, stream=True)) as response:
            chunk_size = 1024  # 单次请求最大值
            with open(path, "wb") as file:
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
    except:
        print('Failed to down url:%s, path:%s' % (url, path))

tenantCode = '71000012'
token = ''
userId = ''
tasklist = [] # projectName, userProjectId, endTime

headers = {'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0'}
ss = requests.Session()

ss.get('https://weiban.mycourse.cn/#/login',headers = headers)
qr = ss.get('https://weiban.mycourse.cn/pharos/login/genBarCodeImageAndCacheUuid.do',headers = headers)

qrdict = json.loads(qr.content)
down(qrdict['data']['imagePath'],'login.jpg')
barcode = qrdict['data']['barCodeCacheUserId']


print('扫码登录(login.jpg)')
while True:
    statusdata = {'barCodeCacheUserId': barcode}
    qrs = ss.post('https://weiban.mycourse.cn/pharos/login/barCodeWebAutoLogin.do',headers = headers, data= statusdata)
    qrstatus = json.loads(qrs.content)
    if(qrstatus['code'] == '0'):
        print('登录成功')
        break
    else:
        print('re等待')
        time.sleep(3)

os.remove('login.jpg')
token = qrstatus['data']['token']
userId = qrstatus['data']['userId']

authdata = {'userId': userId, 'tenantCode': tenantCode, 'token': token}
namepost = ss.post('https://weiban.mycourse.cn/pharos/my/getInfo.do',headers = headers, data= authdata)

if input('你的名字: %s，确定无误小写y:' % json.loads(namepost.content)['data']['realName']) != 'y':
    exit(0)

#学习任务
taskpost = ss.post('https://weiban.mycourse.cn/pharos/index/listStudyTask.do',headers = headers, data= authdata)
taskdict = json.loads(taskpost.content)
for single in taskdict['data']:
    tasklist.append((single['projectName'],single['userProjectId'],single['endTime']))

print(tasklist)

for single in tasklist:# projectName, userProjectId, endTime
    if input('当前处理%s，确定小写y:' % str(single)) !='y':
        exit(0)
    
    listdata = authdata
    listdata['userProjectId'] = single[1]
    listdata['chooseType'] = '3'
    listpost = ss.post('https://weiban.mycourse.cn/pharos/usercourse/listCourse.do',headers = headers, data= listdata)
    listdict = json.loads(listpost.content)['data']#这个是大list，是章的，每章下面有“节” categoryCode,categoryName,totalNum,finishedNum
    print('本任务的章数目: %d' % (len(listdict)))
    for zhang in listdict:
        print('本章信息: %s:%s [%d/%d]' % (zhang['categoryCode'],zhang['categoryName'],int(zhang['finishedNum']),int(zhang['totalNum'])))
        for jie in zhang['courseList']:
            print('本节信息: %s' % jie['resourceName'])
            if(int(jie['finished']) != 1):
                print('finished= %d，好像没做，做做看' % int(jie['finished']))
                studydata = authdata
                studydata['userProjectId']= single[1]
                studydata['courseId'] = jie['resourceId']
                ss.post('https://weiban.mycourse.cn/pharos/usercourse/study.do',headers = headers, data= studydata)
                ss.get('https://weiban.mycourse.cn/pharos/usercourse/finish.do?userCourseId=' + jie['userCourseId'] + '&tenantCode=' + tenantCode,headers = headers)
                print('可能搞定本节了')
                time.sleep(1)