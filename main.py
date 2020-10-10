from flask import Flask, render_template, request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
import pymysql
import json
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import time
import math
from flask_mail import Mail, Message

pymysql.install_as_MySQLdb()

with open('config.json', 'r') as c:
    params = json.load(c)["params"]
local_server = True
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
app.secret_key='super-secret-key'
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config['UPLOAD_SERVERFOL']=params['upload_in_server']

app.config.update(
    DEBUG=True,
    # EMAIL SETTINGS
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)

if local_server == True:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class samplecontacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=False, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    phno = db.Column(db.String(13), unique=True, nullable=False)
    msg = db.Column(db.String(50), unique=False, nullable=False)
    date = db.Column(db.String(12), unique=False, nullable=True)

class posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=False, nullable=False)
    tagline = db.Column(db.String(50), unique=False, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.String(13), unique=False, nullable=True)
    content= db.Column(db.String(200), unique=False, nullable=False)
    img_file = db.Column(db.String())

@app.route("/")
def index():
    posters= posts.query.filter_by().all()
    last=math.ceil(len(posters)/int(params['no_of_posts']))
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posters=posters[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    if(page==1):
        prev="#"
        next="/?page="+ str(page+1)
    elif(page==last):
        prev="/?page="+str(page-1)
        next="#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    return render_template("indexs.html", params=params,posters=posters,prev=prev,next=next)


@app.route("/index")
def index1():
    posters = posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template("indexs.html", params=params,posters=posters)


@app.route("/about")
def about():
    return render_template("abouts.html", params=params)

@app.route("/uploader",methods=['POST','GET'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if(request.method == "POST"):
            f=request.files['img_file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))

        return redirect("/dashboard")
        flash("uploaded sucessfully")



@app.route("/uploaders",methods=['POST','GET'])
def upload_file():
    if ('user' in session and session['user'] == params['admin_user']):
        if(request.method == "POST"):
            f = request.files['img_file']
            f.save(os.path.join(app.config['UPLOAD_SERVERFOL'], secure_filename(f.filename)))
        return redirect("/dashboard")
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        posted=posts.query.filter_by(sno=sno).first()
        db.session.delete(posted)
        db.session.commit()
    return redirect("/dashboard")


@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if ('user' in session and session['user']== params['admin_user']):
        posting = posts.query.all()
        return render_template('dashboard.html',params=params,posting=posting)


    elif (request.method=="POST"):
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            session['user']=username
            posting=posts.query.all()
            return render_template('dashboard.html',params=params,posting=posting)
    return render_template("login.html", params=params)

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if('user' in session and session['user']== params['admin_user']):
        if (request.method == "POST"):
            title=request.form.get('title')
            tagline=request.form.get('tagline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            date = datetime.now()

            if sno=='0':
                post = posts(title=title,tagline=tagline,slug=slug,date=date,content=content,img_file=img_file)
                db.session.add(post)
                db.session.commit()

            else:
                post=posts.query.filter_by(sno=sno).first()
                post.title=title
                post.tagline=tagline
                post.slug=slug
                post.date=date
                post.content=content
                post.img_file=img_file
                db.session.add(post)
                db.session.commit()
                return redirect('/edit/'+ sno)
        post=posts.query.filter_by(sno=sno).first()
        return render_template("edit.html",params=params,post=post,sno=sno)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == "POST":
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = samplecontacts(name=name, email=email, phno=phone, msg=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        mail.send_message('New message from ' + name + 'for sarkar flask',
                          sender=email,
                          recipients=[params['gmail_user']],
                          body=message + "\n" + phone
                          )

    return render_template('contacts.html', params=params)



@app.route("/post/<string:post_slug>" , methods=['POST','GET'] )
def post_route(post_slug):
        post=posts.query.filter_by(slug=post_slug).first()
        return render_template("posts.html", params=params, post=post)




if __name__ == "__main__":
    app.run(debug=True)
