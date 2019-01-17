import http.server
import requests
import os
from socketserver import ThreadingMixIn
from urllib.parse import unquote, parse_qs

memory = {}

form = '''<!DOCTYPE html>
<title>Bookmark Server</title>
<form method="POST">
    <label>Long URI:
        <input name="longuri">
    </label>
    <br>
    <label>Short name:
        <input name="shortname">
    </label>
    <br>
    <button type="submit">Save it!</button>
</form>
<p>URIs I know about:
<pre>
{}
</pre> '''

def CheckURI(uri, timeout=5.0):
	try:	
		a = requests.get(uri, timeout=timeout)
		return a.status_code == 200
	except requests.RequestException:
		return False

class Handler(ThreadingMixIn, http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		name = unquote(self.path[1:])
		if name:
			if name in memory:
				self.send_response(303)
				self.send_header("Location", memory[name])
				self.end_headers()
			else:
				self.send_response(404)
				self.send_header("Content-type", "text/plain; charset=utf-8")
				self.end_headers()
				self.wfile.write("I don't know '{}'.".format(name).encode())
		else:
			self.send_response(200)
			self.send_header("Content-type", "text/html; charset=utf-8")
			self.end_headers()
			known = "\n".join("{} : {}".format(key, memory[key]) for key in sorted(memory.keys()))
			self.wfile.write(form.format(known).encode())

	def do_POST(self):
		length = int(self.headers.get('Content-length', 0))
		body = self.rfile.read(length).decode()
		params = parse_qs(body)

		if "longuri" not in params or "shortname" not in params:
			self.send_response(400)
			self.send_header("Content-type", "text/plain; charset=utf-8")
			self.end_headers()
			self.wfile.write("Required Parameters are not included. Please resubmit.".encode())
		
		longuri = params["longuri"][0]
		shortname = params["shortname"][0]
		
		if CheckURI(longuri):
			memory[shortname] = longuri
			self.send_response(303)
			self.send_header("Location", "/")
			self.end_headers()
		else:
			self.send_response(404)
			self.send_header("Content-type", "text/plain; charset=utf-8")
			self.end_headers()
			self.wfile.write("Cannot fetch URI. it does not exist. Plz check again.".encode())
	
		

if __name__ == "__main__":
	port = int(os.environ.get('PORT', 8000))
	server_address = ('', port)
	httpd = http.server.HTTPServer(server_address, Handler)
	httpd.serve_forever()

