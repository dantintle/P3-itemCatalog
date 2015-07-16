#python HTTP server library
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#common gateway interface library, for do_post Response
import cgi

#for restaurant info from lesson 1, including our classes from db set up
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#create session and connect to db
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


#handler indicate code that's executed based on HTTP request sent to server
class WebServerHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		try:
			if self.path.endswith('/restaurants'):
				restaurants = session.query(Restaurant).all()
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				output = ""
				output += "<html><body>"
				output += "<a href='restaurants/new'>Make New Restaurant</a><br><br>"
				for restaurant in restaurants:
					output += restaurant.name
					output += "<br><a href='/restaurants/%s/edit'>Edit</a><br>" % restaurant.id
					output += "<a href='/restaurants/%s/delete'>Delete</a><br>" % restaurant.id
					output += "<br>"
				output += "</body></html>"
				self.wfile.write(output)
				return

			if self.path.endswith('/restaurants/new'):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body><h1>Make a New Restaurant</h1>"
				output += "<form method='POST' enctype='multipart/form-data' action='/restaurants/new'><input name ='newRestaurantName' type='text' placeholder='New Restaurant Name'><input type='submit' value='Create'></form>"
				output += "</body></html>"
				self.wfile.write(output)
				return

			if self.path.endswith('/edit'):
				restaurantIDPath = self.path.split("/")[2]
				myRestaurantQuery = session.query(Restaurant).filter_by(id=restaurantIDPath).one()
				if myRestaurantQuery:
					self.send_response(200)
					self.send_header('Content-type', 'text/html')
					self.end_headers()
					output = "<html><body>"
					output += "<h1>"
					output += myRestaurantQuery.name
					output += "</h1>"
					output += "<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/edit'>" % restaurantIDPath
					output += "<input name='newRestaurantName' type='text' placeholder='%s' >" % myRestaurantQuery.name
					output += "<input type='submit' value='Rename'> </form>"
					output += "</body></html>"
					self.wfile.write(output)

			if self.path.endswith('/delete'):
				restaurantIDPath = self.path.split("/")[2]
				myRestaurantQuery = session.query(Restaurant).filter_by(id=restaurantIDPath).one()
				if myRestaurantQuery:
					self.send_response(200)
					self.send_header('Content-type', 'text/html')
					self.end_headers()
					output = "<html><body>"
					output += "<h1>Are you sure you want to delete %s?</h1>" % myRestaurantQuery.name
					output += "<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/delete'>" % restaurantIDPath
					output += "<input type='submit' value='Delete'></form>"
					output += "<br><a href='/restaurants'>Cancel</a></body></html>"
					self.wfile.write(output)


		except IOError:
			self.send_error(404, "File not found %s" % self.path)

	def do_POST(self):
		try:
			if self.path.endswith("/restaurants/new"):
				
			#cgi.parse_header function parses header 'content-type' into a main value and dictionary parameter. check if ctype is form data being received. fields variable collects all fields into form. message content to get value of specific field and put into array.
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
					messagecontent = fields.get('newRestaurantName')

					newRestaurantName = Restaurant(name=messagecontent[0])
					session.add(newRestaurantName)
					session.commit()

					self.send_response(301)
					self.send_header('Content-type', 'text/html')
					self.send_header('Location', '/restaurants')
					self.end_headers()


			if self.path.endswith("/edit"):
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
				messagecontent = fields.get('newRestaurantName')
				restaurantIDPath = self.path.split('/')[2]

				myRestaurantQuery = session.query(Restaurant).filter_by(id=restaurantIDPath).one()
				if myRestaurantQuery != [] :
					myRestaurantQuery.name = messagecontent[0]
					session.add(myRestaurantQuery)
					session.commit()
					self.send_response(301)
					self.send_header('Content-type', 'text/html')
					self.send_header('Location', '/restaurants')
					self.end_headers()

			if self.path.endswith("/delete"):
				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

				restaurantIDPath = self.path.split('/')[2]

				myRestaurantQuery = session.query(Restaurant).filter_by(id=restaurantIDPath).one()
				if myRestaurantQuery != [] :
					session.delete(myRestaurantQuery)
					session.commit()
					self.send_response(301)
					self.send_header('Content-type', 'text/html')
					self.send_header('Location', '/restaurants')
					self.end_headers()

				

		except:
			pass

#entrypoint of code-instantiate server, specify port that it will listen on
def main():
	#try code except when user types in KeyboardInterrupt
	try:
		port = 8080
		server = HTTPServer(('', port), WebServerHandler)
		print "Web server running on port %s" % port
		server.serve_forever()

	##user holds control c will stop 
	except KeyboardInterrupt:
		print "^C entered, stopping web server..."
		server.socket.close()
	


#run main method when python interpreter executes script
if __name__ == '__main__':
		main()