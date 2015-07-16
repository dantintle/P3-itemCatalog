from flask import Flask, render_template, request, redirect, url_for,flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Restaurant, MenuItem


from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu App"

engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange (32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
	# protect against cross site forgery attacks by checking state
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = request.data
	print "access token received %s" % access_token

	# exchange client token for long-lived server-side token with GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secre={app-secret}&fb_exchange_token{short-lived-token}
	app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
	app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token%s' % (app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url,'GET')[1]

	#use token to get user info from API
	userinfo_url = 'https://graph.facebook.com/v2.2/me'
	#strip to explore tag from access token
	token = result.split("&")[0]

	url = 'https://graph.facebook.com/v2.2/me?%s' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	#print "url sent for API access:%s"% url
	#print "API JSON result: %s" % result
	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data['name']
	login_session['email'] = data['email']
	login_session['facebook_id'] = data['id']

	#token must be stored in login_session to properly log out
	stored_token = token.split("=")[1]
	login_session['access_token'] = stored_token

	#get user picture
	url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)

	login_session['picture'] = data['data']['url']

	#see if user exists
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
	output += '" style = "width:300px;height:300px;border-radius:150px;-webkit-border-radius:150px;-moz-border-radius:150px;"> '
	flash("You are now logged in as %s"%login_session['username'])
	print "done!"
	return output

@app.route('/fbdisconnect')
def fbdisconnect():
	facebook_id = login_session['facebook_id']
	url = 'https://graph.facebook.com/%s/permissions' % facebook_id
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	del login_session['username']
	del login_session['email']
	del login_session['picture']
	del login_session['user_id']
	del login_session['facebook_id']
	return "You have been logged out."

@app.route('/gconnect', methods=['POST'])
def gconnect():
	#validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	#obtain authorization code
	code = request.data

	#upgrade auth code into credentials object
	try:
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	#check token validity
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	#if error in access token, abort
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	#verify access token is for intended user
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user"), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	#verify access token valid for app
	if result['issued_to'] != CLIENT_ID:
		response = make_response(json.dumps("Token's client id does not match app's"), 401)
		print "Token's client id does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user already connected'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	#store access token in session for later use
	login_session['provider'] = 'google'
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	#get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt':'json'}
	answer = requests.get(userinfo_url, params = params)
	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

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
	output += '">'
	flash("You are now logged in as %s"%login_session['username'])
	print "done!"
	return output

@app.route("/gdisconnect")
def gdisconnect():
	credentials = login_session.get('credentials')
	if credentials is None:
		#check if user connected
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	#execute http get to revoke token
	access_token = credentials
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]

	if result['status'] == '200':
		#reset user session
		del login_session['credentials']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']

		response = make_response(json.dumps('Successfully disconnected'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	else:
		#for whatever reason token is invalid
		response = make_response(json.dumps('Failed to revoke token for given user'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response


@app.route('/disconnect')
def disconnect():
	if 'provider' in login_session:
		if login_session['provider'] == 'google':
			gdisconnect()
			del login_session['gplus_id']
			del login_session['credentials']
		if login_session['provider'] == 'facebook':
			del login_session['facebook']

		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['user_id']
		del login_session['provider']

		flash("You have successfully been logged out.")
		return redirect(url_for('showRestaurants'))
	else:
		flash("You're not logged in.")
		return redirect(url_for('showRestaurants'))



@app.route('/')
@app.route('/restaurants')
def showRestaurants():
	restaurants = session.query(Restaurant)
	if 'username' not in login_session:
		return render_template('publicrestaurants.html', restaurants=restaurants)
	else:
		return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurant/new', methods=['GET','POST'])
def newRestaurant():
	#check if user is logged in
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newRestaurant = Restaurant(name=request.form['name'], user_id=login_session['user_id'])
		session.add(newRestaurant)
		session.commit()
		flash('New restaurant created!')
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('newrestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
	editedRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if 'username' not in login_session:
		return redirect('/login')
	if editedRestaurant.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to edit this restaurant. Please create your own restaurant in order to edit.');}</script><body onload='myFunction()'>"
	if request.method == 'POST':
		if request.form['name']:
			editedRestaurant.name = request.form['name']
		session.add(editedRestaurant)
		session.commit()
		flash("Restaurant successfully edited!")
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('editrestaurant.html', i = editedRestaurant)

@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
	restaurantToDelete = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if 'username' not in login_session:
		return redirect('/login')
	if restaurantToDelete.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"
	if request.method == 'POST':
		session.delete(restaurantToDelete)
		session.commit()
		flash('Restaurant successfully deleted!')
		return redirect(url_for('showRestaurants'))
	else:
		return render_template('deleterestaurant.html', i = restaurantToDelete)
	
	

@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	creator = getUserInfo(restaurant.user_id)
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	if 'username' not in login_session or creator.id != login_session['user_id']:
		return render_template('publicmenu.html', restaurant=restaurant, items=items, creator=creator)
	else:
		return render_template('menu.html', restaurant = restaurant, items = items, creator=creator)

@app.route('/restaurant/<int:restaurant_id>/menu/new', methods=['GET','POST'])
def newMenuItem(restaurant_id):
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newItem = MenuItem(name=request.form['name'], course=request.form['course'], description=request.form['description'], price=request.form['price'], restaurant_id = restaurant_id, user_id = login_session['user_id'])
		session.add(newItem)
		session.commit()
		flash('New menu item created!')
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('newmenuitem.html', restaurant_id = restaurant_id)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	editedMenuItem = session.query(MenuItem).filter_by(id=menu_id).one()
	if 'username' not in login_session:
		return redirect('/login')
	if editedMenuItem.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to edit this item. Please create your own item in order to edit.');}</script><body onload='myFunction()''>"
	if request.method == 'POST':
		if request.form['name']:
			editedMenuItem.name = request.form['name']
			editedMenuItem.course = request.form['course']
			editedMenuItem.description = request.form['description']
			editedMenuItem.price = request.form['price']
		session.add(editedMenuItem)
		session.commit()
		flash('Menu item successfully edited!')
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('editmenuitem.html', restaurant_id = restaurant_id, id = menu_id, i = editedMenuItem)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
	deletedItem = session.query(MenuItem).filter_by(id=menu_id).one()
	if 'username' not in login_session:
		return redirect('/login')
	if deletedItem.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to delete this item. Please create your own restaurant in order to item.');}</script><body onload='myFunction()''>"
	if request.method =='POST':
		session.delete(deletedItem)
		session.commit()
		flash('Menu item successfully deleted!')
		return redirect(url_for('showMenu', restaurant_id = restaurant_id))
	else:
		return render_template('deletemenuitem.html', restaurant_id = restaurant_id, i = deletedItem)

@app.route('/restaurants/JSON', methods=['GET'])
def restaurantListJSON():
	restaurants = session.query(Restaurant)
	return jsonify(restaurants=[r.serialize for r in restaurants])

@app.route('/restaurant/<int:restaurant_id>/menu/JSON', methods=['GET'])
def menuJSON(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
	return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON', methods=['GET'])
def menuItemJSON(restaurant_id, menu_id):
	menuItem = session.query(MenuItem).filter_by(id=menu_id).one()
	return jsonify(MenuItems=[menuItem.serialize])

def getUserID(email):
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.id
	except:
		return None

def getUserInfo(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user

def createUser(login_session):
	newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id


if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)