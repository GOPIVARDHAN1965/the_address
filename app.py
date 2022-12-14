from base64 import encode
import codecs
from crypt import methods
from encodings import utf_8
from fileinput import filename
from turtle import done
from urllib import response
import bcrypt
from flask import Flask, flash, redirect, render_template, request, session, url_for
import pymongo
import gridfs

app = Flask(__name__, template_folder="template")


try:
    mongo =  pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.nv4kd9d.mongodb.net/retryWrites=true&w=majority")
    db = mongo.the_address
except:
    print('Error connecting to the DB')

# try:
#     mongo = pymongo.MongoClient(
#         host = "localhost",
#         port = 27017,
#         serverSelectionTimeoutMS = 1000
#     )
#     db = mongo.the_address
#     mongo.server_info()
# except:
#     print("Error connecting to the DB")


img = gridfs.GridFS(db)


####################################################
#db collections here 
users = db.users
# g=users.create_index()
####################################################
#login/logout routes and modules
####################################################

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        existing_user = users.find_one({'user_id': request.form['mobile_number']})
        if existing_user is None:
            if request.form['pass1'] == request.form['pass2']:
                hashpass = bcrypt.hashpw(request.form['pass1'].encode('utf-8'),bcrypt.gensalt())
                users.insert_one({'user_id': request.form['mobile_number'], 'password': hashpass , 'email_id': request.form['email']})
                session['user_id'] = request.form['mobile_number']
                return redirect(url_for('home'))
            else:
                return "Both passwords must be same!"
        else:
            return "user already exists" 
    return render_template('register.html')



@app.route('/login', methods=['POST','GET'])
def login():
    if request.method=='POST':
        login_user = users.find_one({'user_id': request.form['mobile_number']})
        if login_user:
            if bcrypt.hashpw(request.form['pass1'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['user_id'] = request.form['mobile_number']
                if login_user['admin'] == True:
                    session['admin'] = True
                    return render_template('admin.html')
                return redirect(url_for('home'))
                # return render_template('index.html')
            else:
                return redirect(url_for('login'))
    return render_template('login.html')


####################################################
#Admin Side pages
@app.route('/show_all_residants')
def show_all_residants():
    if 'admin' in session:
        residants = users.find()
        l=[]
        for each_member in residants:
            if 'admin' in each_member:
                continue
            photo= img.get(each_member['image'])
            base64_data = codecs.encode(photo.read(), 'base64')
            photo = base64_data.decode('utf-8')
            dict = {'name':each_member['owner_name'],
                    'flat': each_member['flat'],
                    'block': each_member['block'],
                    'm_number': each_member['user_id'],
                    'image': photo}
            l.append(dict)
        # g = users.find({ '$text': {'$search': '10'}})
        return render_template('show.html', residents = l)
    return "Page cant be accessed"



@app.route('/view_more_info/<mobile>')
def view_more_info(mobile):
    if 'admin' in session:
        user_data = users.find_one({'user_id': mobile})
        if 'owner_name' in user_data:
            owner_data = users.find_one({'user_id': mobile})
            b_img = img.get(owner_data['image'])
            base64_data = codecs.encode(b_img.read(), 'base64')
            b_img=base64_data.decode('utf-8')
            if 'family_data' in owner_data:
                l=[]
                for each_member in owner_data['family_data']:
                    photo= img.get(each_member['image'])
                    base64_data = codecs.encode(photo.read(), 'base64')
                    photo = base64_data.decode('utf-8')
                    l.append(photo)
                return render_template('view_more_info.html', family_data=owner_data['family_data'],owner_data = owner_data, b=b_img, images=l)
            return render_template('view_more_info.html', family_data=[],owner_data = owner_data, b=b_img)
        else:
            return render_template('view_more_info.html', owner_data = [])
    return "Page cant be accessed"




















####################################################
#User Side pages
@app.route('/',methods=['POST','GET'])
def home():
    if 'user_id' in session:
        user_data = users.find_one({'user_id': session['user_id']})
        if 'owner_name' in user_data:
            owner_data = users.find_one({'user_id': session['user_id']})
            b_img = img.get(owner_data['image'])
            base64_data = codecs.encode(b_img.read(), 'base64')
            b_img=base64_data.decode('utf-8')
            if 'family_data' in owner_data:
                l=[]
                for each_member in owner_data['family_data']:
                    photo= img.get(each_member['image'])
                    base64_data = codecs.encode(photo.read(), 'base64')
                    photo = base64_data.decode('utf-8')
                    l.append(photo)
                return render_template('home.html', family_data=owner_data['family_data'],owner_data = owner_data, b=b_img, images=l)
            return render_template('home.html', family_data=[],owner_data = owner_data, b=b_img)
        else:
            return render_template('home.html', owner_data = [])
    return redirect('/login')


@app.route('/add_owner_details',methods=['POST'])
def add_owner_details():
    user_data = users.find_one({'user_id': session['user_id']})
    if request.method == 'POST':
        a=img.put(request.files['owner_pic'],user_id=user_data['_id'], user_relation = 'Owner')
        b=img.get(a)
        base64_data = codecs.encode(b.read(), 'base64')
        b=base64_data.decode('utf-8')
        users.update_one({'_id':user_data['_id']}, {'$set': {'flat': request.form['flat'], 'block': request.form['block'], 'owner_name': request.form['owner_name'], 'image': a}})
        return redirect('/')

@app.route('/add_member',methods=['POST','GET'])
def add_member():
    user_data = users.find_one({'user_id': session['user_id']})
    if request.method=='POST':
        a=img.put(request.files['member_pic'],user_id=user_data['_id'], user_relation = request.form['member_relation'])
        dict = {'member_name': request.form['member_name'],
        'image': a,
        'member_relation': request.form['member_relation'],
        'member_number': request.form['member_number']
        }
        users.update_one({'_id':user_data['_id']}, {'$push': {'family_data': dict }})
        return redirect('/')
    print("inside add_member")
    return render_template('add.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



if __name__ == "__main__":
    app.secret_key = 'donjon'
    app.run(debug=True)