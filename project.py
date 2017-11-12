from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
from collections import OrderedDict

app = Flask(__name__)

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Item, User

from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "CATALOG ITEM"


engine = create_engine('sqlite:///catalogitemwithusers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()



@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print ("access token received %s " % access_token)


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# Client ID
# 319439754645-mgak0pls9ahgn6mhbfg5fplcmc9t8nvl.apps.googleusercontent.com

# Client Secret
# 60s78SrDUlkGG29sjY5PEQTM

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    
    # check if user exists in database
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

def createUser(login_session):
    newUser = User(name = login_session['username'], email=login_session['email'],
                picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id
    
def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()

    return user
def isAdmin(login_session):
    user = session.query(User).filter_by(email=login_session['email']).one()
    try:
        if user.admin:
            print('user is admin', user.email)
            return True
        else:
            print('user is not admin', user.email)
            return False
    except:
        print('user is not admin', user.email)
        return False
        
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/categories/JSON')
def category_list_JSON():
    categories = session.query(Category).all()    
    return jsonify(Catogory=[i.serialize for i in categories])

@app.route('/')
@app.route('/categories/')
def category_list():
    categories = session.query(Category).all()
    items = session.query(Item).join(Category).filter(Item.cat_id==Category.id).all()
    user_logged = is_user_login()
    for i in items:
        print ('name %s'% i.category.name)        
    return render_template('categories.html', categories = categories, items = items, user_logged = user_logged)
    
@app.route('/categories/admin')
def category_admin():
    if 'username' not in login_session:
        return redirect('/login')
    else:
        if (isAdmin(login_session) == True):
            categories = session.query(Category).all()
            user_logged = is_user_login()
            return render_template('categories_admin.html', categories = categories, user_logged = user_logged)
        else:
            user_id = getUserID(login_session['email'])
            user_logged = is_user_login()
            return render_template('login_admin.html', user_id = user_id, user_logged = user_logged)
            
@app.route('/categories/admin_auth/<int:user_id>', methods=['GET', 'POST'])
def admin_auth(user_id):
    auth_user = session.query(User).filter_by(id=user_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if auth_user.id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to update this user. Please contact system administrator.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        if request.form['auth_code'] == '494840810897994':
            auth_user.admin = True
            session.add(auth_user)
            session.commit()
            return redirect(url_for('category_admin'))
        else:
            flash('Authorization code is not valid')
            return redirect(url_for('category_list'))
    else:
        flash('Authorization code is not valid')
        return redirect(url_for('category_list'))

@app.route('/categories/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if (isAdmin(login_session) == False):
        return redirect(url_for('category_admin'))
            
    if (request.method == 'POST'):
        newCategory = Category(name = request.form['name'], user_id = login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash("new category item created!")
        return redirect(url_for('category_list'))
    else:
        user_logged = is_user_login()
        return render_template('newcategory.html', user_logged = user_logged)
              
@app.route('/categories/<int:categoryID>/edit/', methods=['GET','POST'])
def editCategory(categoryID):
    if 'username' not in login_session:
        return redirect('/login')
    if (isAdmin(login_session) == False):
        return redirect(url_for('category_admin'))
        
    editedCategory = session.query(Category).filter_by(id=categoryID).one()
    if (request.method == 'POST'):
        if (request.form['name']):
            editedCategory.name = request.form['name']
        session.add(editedCategory)
        session.commit()
        flash('"%s" is edited' % editedCategory.name)
        return redirect(url_for('category_list'))
    else:
        # USE THE RENDER_TEMPLATE FUNCTION BELOW TO SEE THE VARIABLES YOU
        # SHOULD USE IN YOUR EDITMENUITEM TEMPLATE
        user_logged = is_user_login()
        return render_template(
            'editcategory.html', category = editedCategory, user_logged = user_logged)

@app.route('/categories/<int:categoryID>/delete/',methods=['GET','POST'])
def deleteCategory(categoryID):
    if 'username' not in login_session:
        return redirect('/login')
    if (isAdmin(login_session) == False):
        return redirect(url_for('category_admin'))
    
    deletedCategory = session.query(Category).filter_by(id=categoryID).one()
    if (request.method == 'POST'):
        session.delete(deletedCategory)
        session.commit()
        flash('"%s" is deleted' % deletedCategory.name)
        return redirect(url_for('category_list'))
    else:
        # USE THE RENDER_TEMPLATE FUNCTION BELOW TO SEE THE VARIABLES YOU
        # SHOULD USE IN YOUR EDITMENUITEM TEMPLATE
        user_logged = is_user_login()
        return render_template(
            'deletecategory.html', category = deletedCategory, user_logged = user_logged)
            
##### Item Section:
@app.route('/categories/<int:categoryID>/items/JSON')
def items_list_JSON(categoryID):
    # category = session.query(Category).filter_by(id= categoryID).one()
    # items = session.query(Item).filter_by(cat_id=categoryID) 
    # return jsonify(Item=[i.serialize for i in items])
    categories = session.query(Category).all()
    #data={}
    data = []
    for category in categories:
        items = session.query(Item).filter_by(cat_id=category.id)
        items_list = []
        for item in items:
            items_list.append(item.serialize)
        category_element = {            
        "name": category.name,
        "id" : category.id, 
        "Items" : items_list,                               
        }
        data.append(category_element)
        
        # for i in items:
        #     data['Item'][i.title] = (i.serialize)
    jsons = jsonify(data)
    return jsons
     

@app.route('/categories/<int:categoryID>/items/')
def items_list(categoryID):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id= categoryID).one()
    items = session.query(Item).filter_by(cat_id=categoryID)
    user_logged = is_user_login()
    return render_template('items.html', category = category,categories = categories, items=items, user_logged = user_logged)

@app.route('/categories/<int:categoryID>/<int:item_id>/view',
           methods=['GET', 'POST'])
def viewItem(categoryID, item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id= categoryID).one()
    user_logged = is_user_login()
    if ('username' in login_session) and (editedItem.user_id == login_session['user_id']):
        
        return render_template(
            'viewitem.html', category = category, categoryID=categoryID, item=editedItem, user_logged = user_logged)  
    else:
        return render_template(
            'publicviewitem.html', category = category, categoryID=categoryID, item=editedItem,user_logged = user_logged )  
    

@app.route('/categories/<int:categoryID>/new/', methods=['GET', 'POST'])
def newItem(categoryID):
    if 'username' not in login_session:
        return redirect('/login')

    if (request.method == 'POST'):
        newItem = Item(cat_id = request.form['category_id'],
                title = request.form['title'],
                description = request.form['description'],
                user_id = login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("new item created!")
        return redirect(url_for('items_list',categoryID = request.form['category_id']))
    else:
        categories = session.query(Category).all()
        user_logged = is_user_login()
        return render_template('newitem.html', categoryID= categoryID, categories = categories, user_logged= user_logged)         

@app.route('/categories/<int:categoryID>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(categoryID, item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this item. Please create your own item in order to edit.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
            editedItem.description = request.form['description']
            editedItem.cat_id = request.form['category_id']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('items_list', categoryID=categoryID))
    else:
        categories = session.query(Category).all()
        user_logged = is_user_login()
        return render_template(
            'edititem.html', categories = categories , categoryID=categoryID, item=editedItem, user_logged= user_logged)  


@app.route('/categories/<int:categoryID>/<int:item_id>/delete',
           methods=['GET', 'POST'])            
def deleteItem(categoryID, item_id):
    deletedItem = session.query(Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if deletedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this item. Please create your own item in order to delete.');}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        flash('"%s" is deleted' % deletedItem.title)    
        return redirect(url_for('items_list', categoryID=categoryID))
    else:
        user_logged = is_user_login() 
        return render_template(
            'deleteitem.html', categoryID=categoryID, item = deletedItem, user_logged= user_logged)                      
                                                                     
###################   
@app.route('/links')
def showLinks():
    user_logged = is_user_login()
    return render_template('links.html', user_logged = user_logged)

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    #return "The current session state is %s" % login_session['state']
    return render_template('login.html',STATE=state)

                
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print ('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print ('result is ')
    print (result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        #return response
    else:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        #return response
    flash('User successfully logged out...')    
    return redirect(url_for('category_list'))
                       
def is_user_login():                                                 
    if 'username' not in login_session:
        return False
    else:
        return True

                                       # Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            if 'gplus_id' in login_session:
                del login_session['gplus_id']
            if 'credentials' in login_session:
                del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            if 'facebook_id' in login_session:
                del login_session['facebook_id']
        if 'username' in login_session:
            del login_session['username']
        if 'email' in login_session:
            del login_session['email']
        if 'picture' in login_session:
            del login_session['picture']
        if 'user_id' in login_session:
            del login_session['user_id']
        if 'provider' in login_session:
            del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('category_list'))
    else:
        if 'username' in login_session:
            del login_session['username']
        if 'email' in login_session:
            del login_session['email']
        if 'picture' in login_session:
            del login_session['picture']
        if 'user_id' in login_session:
            del login_session['user_id']
        if 'provider' in login_session:
            del login_session['provider']
        #Sdel login_session['provider']
        flash("You were not logged in")
        return redirect(url_for('category_list'))
                                               
                                        
####################                                                        
            
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port = 5000)
    