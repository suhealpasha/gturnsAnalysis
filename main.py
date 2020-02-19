from playsound import playsound
from flask import Flask, jsonify, render_template, request,Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from pywebpush import webpush, WebPushException
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId
import webbrowser
import time
import datetime
from datetime import datetime
from datetime import date
from nsetools import Nse
import json
import string
import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
from gtts import gTTS 
from playsound import playsound
import json,os
import random
from bson import ObjectId
# import win10toast
# from pynotifier import Notification
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail,Attachment,FileContent, FileName, FileType, Disposition, ContentId
import base64
nse = Nse()

app = Flask(__name__)




@app.route('/', methods=['GET'])
def index():    
    entryLevelData=[]
    riskData=[]
    return render_template('index.html')

@app.route('/TechnicalAnalysis', methods = ['GET'])
def index1():
    allStocksCode = nse.get_stock_codes()
    online_users=[]
    users_list=[]

    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    online_users = collection.find()
    for users in online_users:
        users['_id'] = str(users['_id'])
        users['scripCode'] = str(users['scripCode'])
        users['scripName'] = str(users['scripName'])
        users['sectorName'] = str(users['sectorName'])
        users_list.append(users)   
    payload={'result':users_list ,'stockListResult':allStocksCode}
    return jsonify(payload)


@app.route('/_stuff', methods = ['GET'])
def stuff():
    temp=[]
    temp1=[]
    temp2=[]
    flagStatus=[]
    entryLevelData=[]
    riskData=[]
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    online_users = collection.find()
    for usr in online_users:
        q = nse.get_quote(usr['scripCode'])
        temp.append(q.get("lastPrice"))
        ltp = q.get("lastPrice")
        ltp = int(ltp)        
        temp1.append(q.get("pChange"))        
        myquery = { "scripCode":usr['scripCode'] }
        flag_status=collection.find(myquery)
        for fs in flag_status:
            a = 0.01 * float(fs['entryLevel']) + int(fs['entryLevel'])    
            temp2.append(fs['flag'])        
            if(ltp <= int(a)  and int(fs['flag'])==0):
                mytext = q['companyName']+' Has hit '+str(fs['timeline'])+' demand at Entry Level price of '+str(fs['entryLevel'])+ '   Thank You'
                language = 'en'
                myobj = gTTS(text=mytext, lang=language, slow=False)                                           
                myobj.save("welcome.mp3")
                playsound("beep-02.mp3")  
                playsound("welcome.mp3")                
                os.remove("welcome.mp3")
                time.sleep(10)
                # account_sid = 'AC40e6f1d400057a5ac738867e70b50ee1'
                # auth_token = 'f2a46daf001b96c1b8939d7d3e0e5b28'
                # client = Client(account_sid, auth_token)
                # message = client.messages.create(
                # to="+919743230136",
                # from_="+12564483976",
                # body=str(q['companyName'])+' Has hit '+str(fs['timeline'])+' demand at Entry Level price of '+str(fs['entryLevel'])+'.')
                client = MongoClient("mongodb://localhost:27017/")
                db = client.uptrendAnalysis
                collection = db.uptrendTechnicals
                myquery = { "scripCode":usr['scripCode'] }
                newvalues = { "$set": { "flag": "1" } }
                collection.update_one(myquery, newvalues)
        
    return (jsonify(result=temp,result1=temp1,result2=temp2))

@app.route('/addStock', methods=['POST'])
def register():
    allStCode = nse.get_stock_codes()
    stock_name = request.get_json()['stock_name']

    i=0
    for value in allStCode.values():
        i=i+1
        stock_name = stock_name.strip()
        if value == stock_name:
            break
    stock_code = list(allStCode)[i-1]

    entry_level = request.get_json()['entry_level']
    stop_loss = request.get_json()['stop_loss']
    risk = int(entry_level) - int(stop_loss)
    timeline = request.get_json()['timeline']
    buy_date = request.get_json()['buy_date']
    resultTechTarget = int(entry_level) + ( risk * 2)
    sector_name=''
    res=requests.get('https://www.screener.in/company/'+stock_code+'/consolidated/#peers')
    soup = BeautifulSoup(res.text,'html.parser')
    for ana in soup.findAll('a'):
        if ana.parent.name == 'small':
            if ana.get_text() == '\n':
                 sector_name = 'FMCG'
            else:
                sector_name = ana.get_text()
                sector_name = sector_name.replace(",","")
            break


    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    collection.insert_one({
    'scripCode':stock_code,
    'scripName':stock_name,
    'sectorName':sector_name.strip(),
    'flag':0,
    'entryLevel':entry_level,
    'stopLoss':stop_loss,
    'techTarget':resultTechTarget,
    'risk':risk,
    'timeline':timeline,   
    'buyDate':buy_date
    }).inserted_id

    result = {
        'stock_code' :stock_code,
		'stock_name' : stock_name,
        'sector_name':sector_name,
        'flag':0,
		'entry_level' : entry_level,
        'stop_loss':stop_loss,
        'tech_target':resultTechTarget,
        'risk':risk,
        'timeline':timeline,     
        'buyDate':buy_date
	}
    return jsonify({'result' : result})

@app.route('/<scripCode>', methods=['DELETE'])
def delRegister(scripCode):
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    collection1 = db.uptrendTechnicalsMessages
    myquery = { "scripCode":scripCode.strip() }
    collection.delete_one(myquery)
    collection1.delete_many(myquery)
    return jsonify({'result' : ''})

@app.route('/editStock/<scripCode>', methods=['POST'])
def editRegister(scripCode):
    entry_level = request.get_json()['entry_level']
    stop_loss = request.get_json()['stop_loss']
    risk = int(entry_level) - int(stop_loss)
    timeline = request.get_json()['timeline']
    resultTechTarget = int(entry_level) + ( risk * 2)
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    collection.update_one(
            {"scripCode": scripCode.strip()},
            {
                "$set": {
                    'flag':0,
                    'entryLevel':entry_level,
                    'stopLoss':stop_loss,
                    'techTarget':resultTechTarget,
                    'risk':risk,
                    'timeline':timeline,
                }
            }
        )

    result = {
        'flag':0,
		'entry_level' : entry_level,
        'stop_loss':stop_loss,
        'tech_target':resultTechTarget,
        'risk':risk,
        'timeline':timeline
	}

    return jsonify({'result' : result})

@app.route('/editStockHoldings/<scripCode>', methods=['POST'])
def editRegisterHolding(scripCode):   
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")   
    order = request.get_json()['order']
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    collection.update_one(
            {"scripCode": scripCode.strip()},
            {
                "$push": {                
                     'order':order
                }
            }
        )

    result = {        
       'order':order
	}

    return jsonify({'result' : result})

@app.route('/editStockHoldingsRemove/<itemNo>', methods=['DELETE'])
def editRegisterHoldingRemove(itemNo):    
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    collection.update_one({},{"$pull":{"order":{'itemNumber':float(itemNo)}}})

    result = {        
       'buyDate':''
	}

    return jsonify({'result' : result})


@app.route('/message/<scripCode>', methods=['POST'])
def messageRegister(scripCode):
    stock_name = request.get_json()['stock_name']
    target_price = request.get_json()['target_price']
    condition = request.get_json()['condition']
    message = request.get_json()['message']
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicalsMessages
    collection.insert_one(
    {"scripCode": scripCode.strip(),
    'scripName':stock_name,
    'targetPrice':target_price,
    'condition':condition,
    'message':message
    }
    ).inserted_id
    result = {
        'scripName':stock_name,
        'targetPrice':target_price,
        'condition':condition,
        'message':message
	}
    return jsonify({'result' : result})

@app.route('/Observation')
def messages():
    allStocksCode = nse.get_stock_codes()
    notifications=[]
    message_list=[]

    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicalsMessages
    notifications = collection.find()
    for notify in notifications:
        notify['_id'] = str(notify['_id'])
        notify['scripCode'] = str(notify['scripCode'])
        notify['scripName'] = str(notify['scripName'])
        notify['targetPrice'] = str(notify['targetPrice'])
        notify['condition'] = str(notify['condition'])
        notify['message'] = str(notify['message'])
        message_list.append(notify)    
    return jsonify({'result':message_list})

@app.route('/Holdings', methods = ['GET'])
def holdings():
    ltp_list=[]
    notifications=[]
    message_list=[]
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    notifications = collection.find({'order': { '$exists': True, '$ne': False }})
    for notify in notifications:   
        test = notify['order']
        for t in test:
            if t['sold']== False and t['flag'] ==False:
                q = nse.get_quote(notify['scripCode'])
                ltp = q.get("lastPrice")
                ltp_change = q.get("pChange")
                ltp_list.append(ltp_change)
                if ltp >=t['techTarget']:
                    dueTo = 'Target Hit' 
                if ltp <= int(t['stopLoss']):
                    dueTo = 'Stop Loss'
                if ltp >= notify['techTarget'] or ltp <= int(notify['stopLoss']):                   
                    
                    client = MongoClient("mongodb://localhost:27017/")
                    db = client.uptrendAnalysis
                    collection = db.uptrendExecutionSellNotifications
                    collection.insert_one({
                    'itemNumber':t['itemNumber'],   
                    'scripCode':notify['scripCode'],
                    'scripName':notify['scripName'],
                    'stopLoss':t['stopLoss'],
                    'buyPrice':t['present'],
                    'remarks':'Sell the holdings..',
                    'timeline':'Sell',
                    'quantity':100,
                    'techTarget':t['techTarget'],
                    'soldDueTo':dueTo,
                    'executeDate':datetime.now()
                    }).inserted_id
                    collection = db.uptrendTechnicals
                    collection.update_one(
                    {"scripCode":notify['scripCode'],'order.itemNumber':t['itemNumber']},
                    {
                        "$set": {
                        'order.$.flag':True,
                        'order.$.sellPrice':ltp,
                        'order.$.soldDueTo':dueTo
                    
                    }
                    }
                    )
                    collection = db.uptrendExecutionSellNotifications
                    res = collection.find().sort("executeDate", -1)   
                    # Notification(
	                # title='GTurns',
	                # description='Stock Name: '+str(res[0]['scripName'])+'\n' +'Action: '+str(res[0]['timeline'])+'\n' +'Quantity: '+str(res[0]['quantity']),
	                # duration=5, 
  	                # urgency=Notification.URGENCY_CRITICAL
                    # ).send()   
                    # toaster = win10toast.ToastNotifier()
                    # toaster.show_toast('GTurns','Stock Name: '+str(res[0]['scripName'])+'\n' +'Action: '+str(res[0]['timeline'])+'\n' +'Quantity: '+str(res[0]['quantity']),threaded=True) 
                    # while toaster.notification_active(): time.sleep(0.1)  





        notify['_id'] = str(notify['_id'])
        notify['scripCode'] = str(notify['scripCode'])
        notify['scripName'] = str(notify['scripName'])
        notify['sectorName'] = str(notify['sectorName'])
        notify['techTarget'] = str(notify['techTarget'])
        notify['stopLoss'] = str(notify['stopLoss'])
        notify['order'] = notify['order']  
        message_list.append(notify)  
        message_list.append(ltp_list)     
    return jsonify({'result':message_list})


@app.route('/_stuff1', methods = ['GET','DELETE'])
def stuff1():
    temp=[]
    temp1=[]
    indicies=[]
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicalsMessages
    online_users = collection.find()

    for usr in online_users:        
        detailedData = nse.get_quote(usr['scripCode'])
        
        temp.append(detailedData.get("lastPrice"))
        ltp = detailedData.get("lastPrice")
        ltp = int(ltp)
        temp1.append(detailedData.get("pChange"))

        myquery = { "scripName":detailedData['companyName'] }
        flagStatus= collection.find(myquery)

        for fs in flagStatus:
            con = fs['condition']
            account_sid = 'ACc02942297798e5633d1de8b0d36971b0'
            auth_token = '54dc5903fff1259ae906bb43c2f8f545'
            client = Client(account_sid, auth_token)
            clt = MongoClient("mongodb://localhost:27017/")
            db = clt.uptrendAnalysis

            if(con == 'LTP Lesser than or Equal to'):
                if(ltp <= int(fs['targetPrice'])):                    
                    # mytext = 'Stock Name: '+str(detailedData['companyName'])+'Target Price: '+str(fs['targetPrice']) +'Present Price: '+str(ltp)+'Action: '+str(fs['message'])+'Thank you'
                    # language = 'en'
                    # myobj = gTTS(text=mytext, lang=language, slow=False)
                    # myobj.save("welcome2.mp3")
                    playsound('beep-02.mp3')
                    # os.remove("welcome2.mp3")
                    # message = client.messages.create(
                    # to="+917348870488",
                    # from_="+14844630125",
                    # body=str(' \n Stock Name: '+str(detailedData['companyName']))+'\nTarget Price: '+str(fs['targetPrice']) +'\nPresent Price: '+str(ltp)+'\nAction: '+str(fs['message']))
                    myquery = {"_id":fs['_id'] }
                    collection = db.uptrendTechnicalsMessages
                    collection.delete_one(myquery)
            else:
                if(ltp >= int(fs['targetPrice'])):
                    playsound('beep-02.mp3')
                    # message = client.messages.create(
                    # to="+917348870488",
                    # from_="+14844630125",
                    # body=str(' \n Stock Name: '+str(detailedData['companyName']))+'\nTarget Price: '+str(fs['targetPrice']) +'\nPresent Price: '+str(ltp)+'\nAction: '+str(fs['message']))
                    myquery = {"_id":fs['_id'] }
                    collection = db.uptrendTechnicalsMessages
                    collection.delete_one(myquery)
    bankNifty=nse.get_index_quote("nifty bank") 
    nifty50 = nse.get_index_quote("nifty 50")
    niftyNext50 = nse.get_index_quote("NIFTY NEXT 50")
    nifty100 = nse.get_index_quote("nifty 100")
    nifty500 = nse.get_index_quote("nifty 500")
    niftyMidcap100 = nse.get_index_quote("NIFTY MIDCAP 100")
    niftyMidcap50 = nse.get_index_quote("NIFTY MIDCAP 50")
    niftyInfra = nse.get_index_quote("NIFTY INFRA")
    niftyPharma = nse.get_index_quote("NIFTY Pharma")
    niftyIt = nse.get_index_quote("NIFTY It")
    indicies.append(bankNifty)
    indicies.append(nifty50) 
    indicies.append(niftyNext50)   
    indicies.append(nifty100)
    indicies.append(nifty500)
    indicies.append(niftyMidcap50)
    indicies.append(niftyMidcap100)
    indicies.append(niftyInfra)
    indicies.append(niftyPharma)
    indicies.append(niftyIt)
    return (jsonify(result=temp,result1=temp1,result2=indicies))


@app.route('/Observation/<scripCode>', methods=['DELETE'])
def delRegisterAlert(scripCode):
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis    
    collection1 = db.uptrendTechnicalsMessages
    myquery = { "scripCode":scripCode.strip() }
    collection1.delete_one(myquery)  
    return jsonify({'result' : ''})

@app.route('/message/<_id>', methods=['POST'])
def editRegisterMessage(_id):
    stock_name = request.get_json()['stock_name']
    target_price = request.get_json()['target_price']
    condition = request.get_json()['condition']
    message = request.get_json()['message']
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicalsMessages
    collection.update_one(
            {"_id":  ObjectId(_id.strip())},
            {
                "$set": {
                    'scripName':stock_name,
                    'targetPrice':target_price,
                    'condition':condition,
                    'message':message,
                    
                }
            }
        )
    result = {
        'scripName':stock_name,
        'targetPrice':target_price,
        'condition':condition,
        'message':message
	}
    return jsonify({'result' : result})

@app.route('/send_message')
def subscribe():
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendExecutionNotifications
    res = collection.find().sort("executeDate", -1)
    # Notification(
	# title='GTurns',
	# description='Stock Name: '+str(res[0]['scripName'])+'\n' +'Action: '+str(res[0]['timeline'])+'\n' +'Quantity: '+str(res[0]['quantity']),
	# duration=5, 
  	# urgency=Notification.URGENCY_CRITICAL
    # ).send()  
    
    # toaster = win10toast.ToastNotifier()
    # toaster.show_toast('GTurns','Stock Name: '+str(res[0]['scripName'])+'\n' +'Action: '+str(res[0]['timeline'])+'\n' +'Quantity: '+str(res[0]['quantity']),threaded=True) 
    # while toaster.notification_active(): time.sleep(0.1)  
    return jsonify({'sucess':'Sent'})

@app.route('/send_sell_message')
def seller():
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendExecutionSellNotifications
    res = collection.find().sort("executeDate", -1)
    # Notification(
	# title='GTurns',
	# description='Stock Name: '+str(res[0]['scripName'])+'\n' +'Action: '+str(res[0]['timeline'])+'\n' +'Quantity: '+str(res[0]['quantity']),
	# duration=5, 
  	# urgency=Notification.URGENCY_CRITICAL
    # ).send()  
    # toaster = win10toast.ToastNotifier()
    # toaster.show_toast('GTurns','Stock Name: '+str(res[0]['scripName'])+'\n' +'Action: '+str(res[0]['timeline'])+'\n' +'Quantity: '+str(res[0]['quantity']),threaded=True) 
    # while toaster.notification_active(): time.sleep(0.1)  
    return jsonify({'sucess':'Sent'})

@app.route('/executeNotifications', methods=['POST'])
def registerExecute():
    stock_name= request.get_json()['stock_name']
    stop_loss = request.get_json()['stop_loss']  
    tech_target = request.get_json()['tech_target']
    timeline = request.get_json()['timeline']
    stock_code = request.get_json()['stock_code']
    execute_date = request.get_json()['execute_date']
    remarks = request.get_json()['remarks']
    present = request.get_json()['present']
    quantity = request.get_json()['quantity']


    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendExecutionNotifications
    collection.insert_one({
    'scripCode':stock_code,
    'scripName':stock_name,
    'stopLoss':stop_loss,
    'techTarget':tech_target,
    'buyPrice':present,
    'remarks':remarks,
    'timeline':timeline,
    'quantity':quantity,
    'executeDate':datetime.now()
    }).inserted_id

    result = {
      'scripCode':stock_code,
    'scripName':stock_name,
    'stopLoss':stop_loss,
    'techTarget':tech_target,
    'buyPrice':present,
    'remarks':remarks,
    'timeline':timeline,
    'quantity':quantity,
    'executeDate':execute_date
	}
    return jsonify({'result' : result})   

@app.route('/Execution',methods=['GET'])
def notificationMessages():      
    message_list=[]
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendExecutionNotifications
    notifications = collection.find()
    for notify in notifications:      
        notify['_id'] = str(notify['_id'])
        notify['scripCode'] = str(notify['scripCode'])
        notify['scripName'] = str(notify['scripName'])
        notify['remarks'] = str(notify['remarks'])
        notify['stopLoss'] = str(notify['stopLoss'])
        notify['present'] = str(notify['buyPrice'])
        notify['timeline'] = str(notify['timeline'])
        notify['executeDate'] = str(notify['executeDate'])
        notify['quantity'] = str(notify['quantity'])
        message_list.append(notify)    
    return jsonify({'result':message_list})

@app.route('/sendEmail<param>',methods=['POST'])
def sendEmail(param):      
    arg=param.split('_')
    email = arg[0]
    name = arg[1]
    scripCode = arg[2]
    scripName = arg[3]
    quantity = arg[4]
    filePath = "Marico_Ltd_Fundamental_analysis.pdf"
    imageFilePath = "logoTemplate.png"
    
    message = Mail(from_email='support@gturns.com',to_emails= "suheal@gturns.com" ,subject='GTurns Advisories',html_content='<p>Dear '+str(name)+',<br/><br/>We recommend you to buy the below stock as per the risk management.We believe that the stock would perform according to the analysis made. Hence, refer the attached document for further more details.<br/><table><tr><td>Stock Name</td><td><strong>'+str(scripName)+'</strong></td></tr><tr><td>Stock Code</td><td><strong>'+str(scripCode)+'</strong></td></tr><tr><td>Quantity</td><td><strong> '+str(quantity)+'</td></tr></table>  <br/><br/>Best Regards,<br/></p><img src="cid:logo" alt="img" width="100px" height="80px" /><br/>#83 Sri Vasavi Arcade, 2nd floor,<br/>17th cross, 21st main, Banashankari IInd stage,<br/> Bangalore - 560070<hr/><p><b style="color:red">Note:</b><span style="font-style:italic">This document is shared only with the recipient of this email. This is not for public distribution and has been furnished solely for information and must not be reported or redistributed to any other person or entity. </span></p>')
    with open(filePath, 'rb') as f:
        data = f.read()
        f.close()
    encoded = base64.b64encode(data).decode()
    attachment = Attachment()
    attachment.file_content = FileContent(encoded)
    attachment.file_type = FileType('application/pdf')
    attachment.file_name = FileName('test_filename.pdf')
    attachment.disposition = Disposition('attachment')
    attachment.content_id = ContentId('Example Content ID')
    message.attachment = attachment
    with open(imageFilePath, 'rb') as f:
        imageData = f.read()
        f.close()
    encodedImage = base64.b64encode(imageData).decode()
    attachment2 = Attachment()
    attachment2.file_content = FileContent(encodedImage)
    attachment2.file_type = FileType('image/png')
    attachment2.file_name = FileName('logo.png')
    attachment2.disposition = Disposition('inline')
    attachment2.content_id = ContentId('logo')
    message.attachment = attachment2

    try:
        sendgrid_client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sendgrid_client.send(message)      
    except Exception as e:
        print(e.message)
    return jsonify({'result':'sucess'})

@app.route('/sendEmailSell<param>',methods=['POST'])
def sendEmailSell(param):      
    arg=param.split('_')
    email = arg[0]
    name = arg[1]
    scripCode = arg[2]
    scripName = arg[3]
    quantity = arg[4]    
    imageFilePath = "logoTemplate.png"
    
    message = Mail(from_email='support@gturns.com',to_emails= "suheal@gturns.com" ,subject='GTurns Advisories',html_content='<p>Dear '+str(name)+',<br/><br/>We recommend you to kindly sell the below stock.<br/><table><tr><td>Stock Name</td><td><strong>'+str(scripName)+'</strong></td></tr><tr><td>Stock Code</td><td><strong>'+str(scripCode)+'</strong></td></tr><tr><td>Quantity</td><td><strong> '+str(quantity)+'</td></tr></table>  <br/><br/>Best Regards,<br/></p><img src="cid:logo" alt="img" width="100px" height="80px" /><br/>#83 Sri Vasavi Arcade, 2nd floor,<br/>17th cross, 21st main, Banashankari IInd stage,<br/> Bangalore - 560070')
    
    with open(imageFilePath, 'rb') as f:
        imageData = f.read()
        f.close()
    encodedImage = base64.b64encode(imageData).decode()
    attachment2 = Attachment()
    attachment2.file_content = FileContent(encodedImage)
    attachment2.file_type = FileType('image/png')
    attachment2.file_name = FileName('logo.png')
    attachment2.disposition = Disposition('inline')
    attachment2.content_id = ContentId('logo')
    message.attachment = attachment2

    try:
        sendgrid_client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sendgrid_client.send(message)      
    except Exception as e:
        print(e.message)
    return jsonify({'result':'sucess'})



@app.route('/removeExecution/<_id>', methods=['DELETE'])
def delExecution(_id): 
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendExecutionNotifications
    myquery = { "_id":ObjectId(_id)}
    collection.delete_one(myquery)    
    return jsonify({'result' : ''})


@app.route('/executeSellNotifications', methods=['POST'])
def registerSellExecute():
    item_no = request.get_json()['item_no']
    stock_name = request.get_json()['stock_name']
    stop_loss = request.get_json()['stop_loss']  
    timeline = request.get_json()['timeline']
    stock_code = request.get_json()['stock_code']
    execute_date = request.get_json()['execute_date']
    remarks = request.get_json()['remarks']
    present = request.get_json()['present']
    quantity = request.get_json()['quantity']
    tech_target = request.get_json()['tech_target']
    sold_due_to = request.get_json()['sold_due_to']

    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendExecutionSellNotifications
    collection.insert_one({
    'itemNumber':item_no,   
    'scripCode':stock_code,
    'scripName':stock_name,
    'stopLoss':stop_loss,
    'buyPrice':present,
    'remarks':remarks,
    'timeline':timeline,
    'quantity':quantity,
    'techTarget':tech_target,
    'soldDueTo':sold_due_to,
    'executeDate':datetime.now()
    }).inserted_id

    result = {
      'scripCode':stock_code,
    'scripName':stock_name,
    'stopLoss':stop_loss,
    'buyPrice':present,
    'remarks':remarks,
    'timeline':timeline,
    'quantity':quantity,
     'techTarget':tech_target,
    'soldDueTo':sold_due_to,
    'executeDate':execute_date
	}
    return jsonify({'result' : result})   

@app.route('/SellExecution',methods=['GET'])
def notificationSellMessages():  
    message_list=[]
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendExecutionSellNotifications
    notifications = collection.find()
    for notify in notifications:      
        notify['_id'] = str(notify['_id'])
        notify['scripCode'] = str(notify['scripCode'])
        notify['scripName'] = str(notify['scripName'])
        notify['remarks'] = str(notify['remarks'])
        notify['stopLoss'] = str(notify['stopLoss'])
        notify['buyPrice'] = str(notify['buyPrice'])
        notify['timeline'] = str(notify['timeline'])
        notify['techTarget'] = str(notify['techTarget'])
        notify['executeDate'] = str(notify['executeDate'])
        notify['quantity'] = str(notify['quantity'])
        message_list.append(notify)    
    return jsonify({'result':message_list})

@app.route('/removeSellExecution/<_id>', methods=['DELETE'])
def delSellExecution(_id): 
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendExecutionSellNotifications
    myquery = { "_id":ObjectId(_id)}
    collection.delete_one(myquery)    
    return jsonify({'result' : ''})

@app.route('/rollbackSellExecution/<item>', methods = ['POST','DELETE'])
def rollbackSell(item):   
    arg = item.split('_')
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    soldDue = collection.find_one( {"scripCode":arg[0].strip(),'order.itemNumber':float(arg[1].strip())})
    sdt = soldDue['order'][-1]['soldDueTo']
    if sdt == 'Stop Loss':
        collection.update_one(
            
            {"scripCode":arg[0].strip(),'order.itemNumber':float(arg[1].strip())},
            {
                "$set": {
                    'order.$.flag':False,              
                    'order.$.stopLoss':int((0.01 * int(arg[2]) - int(arg[2].strip())))*-1,                    
                    'order.$.soldDueTo':''
                }
            }
        )
    else:
        collection.update_one(
            {"scripCode":arg[0].strip(),'order.itemNumber':float(arg[1].strip())},
            {
                "$set": {
                    'order.$.flag':False,              
                    'order.$.techTarget':int((0.01 * int(arg[3].strip()))+int(arg[3])),
                    'order.$.soldDueTo':''
                }
            }
        )
    collection1 = db.uptrendExecutionSellNotifications
    collection1.delete_one({'itemNumber':float(arg[1].strip())})

    return jsonify({'result':'test'})

@app.route('/holdingsSold/<param>', methods=['POST'])
def editOrderSold(param):
    arg = param.split('_')
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals    
    collection.update_one(
            {"scripCode":arg[0].strip(),'order.itemNumber':float(arg[1].strip())},
            {
                "$set": {
                    'order.$.sold':True,                    
                    'order.$.sellDate':datetime.now(),
                    # 'order.$.soldDueTo':'Explicit'
                }
            }
        )
    result = {
     
        'sold':arg
	}
    return jsonify({'result' : result})


@app.route('/updateOrderFlag/<param>', methods=['POST'])
def editOrderFlag(param): 
    arg = param.split('_')   
    client = MongoClient("mongodb://localhost:27017/")
    db = client.uptrendAnalysis
    collection = db.uptrendTechnicals
    collection.update_one(
        {"scripCode":arg[0].strip(),'order.itemNumber':float(arg[1].strip())},
            {
                "$set": {
                    'order.$.flag':True,
                    'order.$.sellPrice':arg[2],
                    'order.$.soldDueTo':arg[3]
                }
            }
    )

    result = {        
       'buyDate':''
	}

    return jsonify({'result' : result})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
