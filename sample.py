#python HTTP server library
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#common gateway interface library, for do_post Response
import cgi

#for restaurant info from lesson 1
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
				output += "<a href='/new'>Make New Restaurant</a><br>"
				for restaurant in restaurants:
					output += restaurant.name
					output += "<br><a href='#'>Edit</a><br><a href='#'>Delete</a><br>"
					output += "<br>"
				output += "</body></html>"
				self.wfile.write(output)
				return

			if self.path.endswith('/restaurants/new'):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body><h1>Enter New Restaurant below</h1>"
				output += "<form method='POST' enctype='multipart/form-data' action='/restaurants/new'><input name ='message' type='text'><input type='submit' value='Submit'></form>"
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return

			if self.path.endswith('/hello'):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body><h1>Hello!</h1>"
				output += "<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name ='message' type='text'><input type='submit' value='Submit'> </form>"
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return

			if self.path.endswith('/hola'):
				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body><h1>&#161Hola!</h1>	<a href= '/hello'>back to Hello</a></body></html>"
				output += "<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name ='message' type='text'><input type='submit' value='Submit'> </form>"
				output += "</body></html>"
				self.wfile.write(output)
				print output
				return

		except IOError:
			self.send_error(404, "File not found %s" % self.path)

	def do_POST(self):
		try:
			self.send_response(301)
			self.send_header('Content-type', 'text/html')
			self.end_headers()

			#cgi.parse_header function parses header 'content-type' into a main value and dictionary parameter. check if ctype is form data being received. fields variable collects all fields into form. message content to get value of specific field and put into array.
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			if ctype == 'multipart/form-data':
				fields = cgi.parse_multipart(self.rfile, pdict)
				messagecontent = fields.get('message')

			output = ""
			output += "<html><body>"
			output += " <h2> Okay, how about this: </h2>"
			output += "<h1> %s </h1>" % messagecontent[0]

			#post request + header tag to get user to submit data. message coincides with field that we're requesting data from in post request.
			output += "<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name ='message' type='text'><input type='submit' value='Submit'> </form>"
			output += "</body></html>"
			self.wfile.write(output)
			print output

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