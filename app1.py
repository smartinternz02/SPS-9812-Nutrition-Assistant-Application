
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from ibm_watson import VisualRecognitionV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import wolframalpha
client=wolframalpha.Client(API_KEY)
authenticator = IAMAuthenticator(API_KEY)

visual_recognition = VisualRecognitionV3(
    version='2018-03-19',
    authenticator=authenticator)

app = Flask(__name__)
app.secret_key = 'a' 
app.config['MYSQL_HOST'] = ''
app.config['MYSQL_USER'] = ''
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = ''
mysql = MySQL(app)
@app.route('/')
def intro():
    return render_template('intro.html')
@app.route('/signup',methods=['GET','POST'])
def signup():
    msg = ''
    if request.method == 'POST' :
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT * FROM jobportal WHERE username = % s', (username, ))
        account = cursor.fetchone()
        print(account)
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
        else:
            cursor.execute('INSERT INTO jobportal VALUES (NULL, % s, % s, % s)', (username, email,password))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            body=" Hello {} \n\n Welcome to Nutrition. We're thrilled to see you here!\n We're confident that Nutrition Assist will help you find right diet \n stay Healthy\n Best\n Nutrition".format(username)
            subject="Nutrition Assist"
            message=MIMEMultipart()
            message['From']=""
            message['To']=email
            message['subject']=subject
            message.attach(MIMEText(body,'plain'))
            text=message.as_string()
            mail=smtplib.SMTP('smtp.gmail.com', 587)
            mail.starttls()
            mail.login("")
            mail.sendmail("",email,text)
            mail.close()
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
            
    return render_template('signup.html',msg=msg)   
@app.route('/signin',methods=['GET','POST'])
def signin():
    global userid
    msg = '' 
    if request.method=='POST' :
        username = request.form['username']
        password = request.form['password']
        print(username ,password)
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM jobportal WHERE username = % s AND password = % s', (username, password ),)
        account = cursor.fetchone()
        print (account)
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            userid=  account[0]
            session['username'] = account[1]
            msg = 'Logged in successfully !'
            
            msg = 'Logged in successfully !'
            return render_template('mainpage.html', msg = msg,username=session['username'],)
        else:
            msg = 'Incorrect username / password !'
    return render_template('signin.html', msg = msg)
   
@app.route('/contactus',methods=['GET','POST'])
def contactus():
    msg=""
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        messages=request.form['message']
        print(username, email,messages)
        body=" Hello  Nutrition.\n\n {}".format(messages)
        subject=email
        message=MIMEMultipart()
        message['From']=""
        message['To']=""
        message['subject']=subject
        message.attach(MIMEText(body,'plain'))
        text=message.as_string()
        mail=smtplib.SMTP('smtp.gmail.com', 587)
        mail.starttls()
        mail.login("")
        mail.sendmail("",email,text)
        mail.close()
        msg="We will contact you soon"
    return render_template('contactus.html',msg=msg)

@app.route('/mainpage',methods=['GET','POST'])
def mainpage():
    if request.method=='POST':
       if request.method=='POST':
        try:
            url=request.form['url']
            visual_recognition.set_service_url('https://api.us-south.visual-recognition.watson.cloud.ibm.com/instances/80c78105-880f-4bb7-b79c-93764795ee73') 
            session['url']= url
            print(url)
            classes = visual_recognition.classify(url=url,classifier_ids='food').get_result()	
            data=json.dumps(classes,indent=4)
            data2=json.loads(data)
            query=data2["images"][0]['classifiers'][0]["classes"][0]["class"]
            print(query)
            session['query']=query
            if query=="non-food":
              return render_template('mainpage.html',username=session['username'],msg="non food")
            else:
                res=client.query(query+" nutrition")  
                output=next(res.results).text
                print(output)
                session['output']=output
                print(session['output'])
                return render_template('mainpage.html',username=session['username'],msg=session['query'])
        except:
            return render_template('mainpage.html',username=session['username'],msg='error:Check the url')
    return render_template('mainpage.html')
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/values',methods=['GET','POST'])
def values():
    try: 
        return render_template('values.html',imgurl=session["url"],query=session['query'],msg=session['output'])
    except:
        return render_template('mainpage.html',username=session['username'],msg="After giving url please press enter key")
@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('query', None)
   session.pop("url", None)
   session.pop('output', None) 
   return render_template('intro.html')  

    
if __name__ == '__main__':
   app.run(debug=True, host = "0.0.0.0",port = 8080)

