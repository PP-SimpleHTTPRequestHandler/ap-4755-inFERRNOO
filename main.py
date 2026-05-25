import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
from urllib.parse import urlparse

USERS_LIST = [
    {
        "id": 1,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
    }
]


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _set_response(self, status_code=200, body=None):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body if body else {}).encode('utf-8'))

    def _pars_body(self):
        
        content_length = int(self.headers.get('Content-Length', '0'))
        if content_length == 0:
            return None
        return json.loads(self.rfile.read(content_length).decode('utf-8'))
    
    def _validate_user_structure(self, user):
        """Перевіряє структуру для POST запитів (включаючи id)."""
        required_keys = {"id", "username", "firstName", "lastName", "email", "password"}
        if not isinstance(user, dict) or set(user.keys()) != required_keys:
            return False
        if not isinstance(user["id"], int) or isinstance(user["id"], bool):
            return False
        for key in ["username", "firstName", "lastName", "email", "password"]:
            if not isinstance(user[key], str):
                return False
        return True

    def _validate_put_structure(self, data):
       
        required_keys = {"username", "firstName", "lastName", "email", "password"}
        if not isinstance(data, dict) or set(data.keys()) != required_keys:
            return False
        for key in required_keys:
            if not isinstance(data[key], str):
                return False
        return True

    def do_GET(self):
        global USERS_LIST

        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == '/reset':
            USERS_LIST = [
                {
                    "id": 1,
                    "username": "theUser",
                    "firstName": "John",
                    "lastName": "James",
                    "email": "john@email.com",
                    "password": "12345",
                }
            ]

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {"message": "Users list has been reset"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
    
        elif path == '/users':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(USERS_LIST).encode('utf-8'))
            return
        
        elif path.startswith('/user/'):
            match = re.match(r'^/user/([^/]+)$', path)
            if match:
                username_param = match.group(1)

                user = next((u for u in USERS_LIST if u["username"] == username_param), None)

                if user:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(user).encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    
                    error_response = {"error": "User not found"}
                    self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return

        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

    def do_POST(self):
        global USERS_LIST

        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        try:
            payload = self._pars_body()
            if payload is None:
                self._set_response(400, {})
                return
        except Exception:
            self._set_response(400, {})
            return

        is_list = isinstance(payload, list)
        incoming_users = payload if is_list else [payload]
        
        if not incoming_users:
            self._set_response(400, {})
            return

        for user in incoming_users:
            if not self._validate_user_structure(user):
                self._set_response(400, {})
                return
        
        existing_ids = {user["id"] for user in USERS_LIST}
       
        if path == '/user':
            if is_list:  
                self._set_response(400, {})
                return

            new_user = incoming_users[0]
            if new_user["id"] in existing_ids:
                self._set_response(400, {})
                return

            USERS_LIST.append(new_user)
            self._set_response(201, new_user)
            return
        
        elif path == '/user/createWithList':
            if not is_list: 
                self._set_response(400, {})
                return
           
            incoming_ids = [user["id"] for user in incoming_users]
            if len(incoming_ids) != len(set(incoming_ids)):
                self._set_response(400, {})
                return
            
            for user in incoming_users:
                if user["id"] in existing_ids:
                    self._set_response(400, {})
                    return
            
            USERS_LIST.extend(incoming_users)
            self._set_response(201, incoming_users)
            return
        
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

    def do_PUT(self):
        global USERS_LIST

        parsed_url = urlparse(self.path)
        path = parsed_url.path

        match = re.match(r'^/user/(\d+)$', path)
        if match:
            user_id = int(match.group(1))

            try:
                payload = self._pars_body()
                if payload is None:
                    self._set_response(400, {"error": "not valid request data"})
                    return
            except Exception:
                self._set_response(400, {"error": "not valid request data"})
                return

            if not self._validate_put_structure(payload):
                self._set_response(400, {"error": "not valid request data"})
                return

            user = next((u for u in USERS_LIST if u["id"] == user_id), None)
            if user is None:
                self._set_response(404, {"error": "User not found"})
                return

            user["username"] = payload["username"]
            user["firstName"] = payload["firstName"]
            user["lastName"] = payload["lastName"]
            user["email"] = payload["email"]
            user["password"] = payload["password"]

            self._set_response(200, user)
            return

        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

    def do_DELETE(self):
        global USERS_LIST

        parsed_url = urlparse(self.path)
        path = parsed_url.path

        match = re.match(r'^/user/(\d+)$', path)
        if match:
            user_id = int(match.group(1))

            user_to_delete = next((u for u in USERS_LIST if u["id"] == user_id), None)
            
            if user_to_delete:
                USERS_LIST.remove(user_to_delete)
                self._set_response(200, {})
            else:
                self._set_response(404, {"error": "User not found"})
            return

        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, host='localhost', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()