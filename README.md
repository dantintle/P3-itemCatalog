project3-itemCatalog


Traceback (most recent call last): File "/usr/lib/python2.7/dist-packages/flask/app.py", line 1836, in call return self.wsgi_app(environ, start_response) File "/usr/lib/python2.7/dist-packages/flask/app.py", line 1820, in wsgi_app response = self.make_response(self.handle_exception(e)) File "/usr/lib/python2.7/dist-packages/flask/app.py", line 1403, in handle_exception reraise(exc_type, exc_value, tb) File "/usr/lib/python2.7/dist-packages/flask/app.py", line 1817, in wsgi_app response = self.full_dispatch_request() File "/usr/lib/python2.7/dist-packages/flask/app.py", line 1477, in full_dispatch_request rv = self.handle_user_exception(e) File "/usr/lib/python2.7/dist-packages/flask/app.py", line 1381, in handle_user_exception reraise(exc_type, exc_value, tb) File "/usr/lib/python2.7/dist-packages/flask/app.py", line 1475, in full_dispatch_request rv = self.dispatch_request() File "/usr/lib/python2.7/dist-packages/flask/app.py", line 1461, in dispatch_request return self.view_functionsrule.endpoint

File "/vagrant/python/finalproject.py", line 62, in fbconnect data = json.loads(result)

File "/usr/lib/python2.7/json/init.py", line 338, in loads return _default_decoder.decode(s) File "/usr/lib/python2.7/json/decoder.py", line 366, in decode obj, end = self.raw_decode(s, idx=_w(s, 0).end()) File "/usr/lib/python2.7/json/decoder.py", line 384, in raw_decode raise ValueError("No JSON object could be decoded") ValueError: No JSON object could be decoded