# imports for CRUD app
from flask import Flask, request, render_template, redirect, url_for, flash
# imports for anti-forgery state token
from flask import session as login_session
import random
import string
# imports for database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CategoryItem
# imports for gconnect
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
# import for JSON Endpoints
from flask import jsonify


# Instantiate flask app
app = Flask(__name__)

# GConnect configuration
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

# Connect to DB
engine = create_engine('sqlite:///itemcatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

# Create DB session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# ------------ #
# -- Routes -- #
# ------------ #

# -- JSON Endpoints -- #
# -------------------- #
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/categories/<int:category_id>/items/JSON')
def itemsJSON(category_id):
    items = session.query(CategoryItem).filter_by(category_id=category_id)
    return jsonify(categoryItems=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/items/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


# -- Auth Routes -- #
# ----------------- #
# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# CONNECT
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
    result = json.loads((h.request(url, 'GET')[1]).decode('utf-8'))
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
        print("Token's client ID does not match app's.")
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

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists, if it doesn't make a new one
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
    print("done!")
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print ('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # print('In gdisconnect access token is %s', access_token)
    # print('User name is: ')
    # print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# -- Flask App Routes -- #
# ---------------------- #
# Show all categories - Home page
@app.route('/')
@app.route('/categories/')
def showCategories():
    categories = session.query(Category).all()
    items = session.query(CategoryItem).limit(6).all()
    return render_template('categories.html', categories=categories, items=items, login_session=login_session)


# Add a category
@app.route('/categories/new', methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        flash('New Category Created')
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


# Edit an existing category
@app.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category successfully edited')
            return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete a category
@app.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        flash('Category successfully deleted')
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategory.html', category=categoryToDelete)


# Show all items of a category
@app.route('/categories/<int:category_id>')
@app.route('/categories/<int:category_id>/items')
def showItemList(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(category_id=category_id).all()
    return render_template('items.html', category=category, items=items, login_session=login_session)


# Add item to category
@app.route('/categories/<int:category_id>/items/new', methods=['GET', 'POST'])
def addItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        newItem = CategoryItem(name=request.form['name'],
                               description=request.form['description'],
                               category_id=category_id)
        session.add(newItem)
        session.commit()
        flash('New item created')
        return redirect(url_for('showItemList', category_id=category.id))
    else:
        return render_template('newItem.html', category=category)


# Show details of a specific item
@app.route('/categories/<int:category_id>/items/<int:item_id>')
def showItem(category_id, item_id):
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('showItem.html', item=item, category=category, login_session=login_session)


# Edit an existing item
@app.route('/categories/<int:category_id>/items/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    editedItem = session.query(CategoryItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        if (request.form['name'] and request.form['description']):
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            flash('Item successfully edited')
            return redirect(url_for('showItemList', category_id=category_id))
    else:
        return render_template('editItem.html',
                               item=editedItem, category_id=category_id)


# Delete an item
@app.route('/categories/<int:category_id>/items/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    itemToDelete = session.query(CategoryItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item successfully deleted')
        return redirect(url_for('showItemList', category_id=category_id))
    else:
        return render_template('deleteItem.html',
                               item=itemToDelete, category_id=category_id)


if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
