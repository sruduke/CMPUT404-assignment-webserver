import os


# Helper Classes
# ------------------------------------------------------------------------------
class HttpResponse():
    """
    This class is used to form and build the appropriate HTTP 1.1 response
    """
    nl = "\r\n"
    response = ""

    HTTP_CODES = {
        200: "OK",
        301: "Moved Permanently",
        404: "Not Found",
        405: "Method Not Allowed"}

    def __add_type(self, http_code : int):
        """Forms the first line of the HTTP response, containing the code and what it signifies"""
        self.response = f'HTTP/1.1 {http_code} {self.HTTP_CODES.get(http_code)}{self.nl}'
    
    def __add_headers(self, headers : dict):
        """Appends and formats the key:value pairs in the `headers` argument to the response"""
        for header,value in headers.items():
            self.response += f'{header}: {value}{self.nl}'
    
    def __add_content(self, content):
        """Append the content length header and content to the response"""
        self.response += f'Content-Length: {len(content)}{self.nl * 2}{content}'
        if content:
            self.response += content
    
    def form_response(self, code, headers, content):
        """Facilitator function to build a well-formatted HTTP 1.1 response"""
        self.__add_type(code)
        self.__add_headers(headers)
        self.__add_content(content)
        return self.response

    def serve_file(self, file_name):
        """Builds and returns the response for the content of the provided file name"""
        headers = {}
        if file_name[-3:] == "css":
            headers["Content-Type"] = "text/css"
        elif file_name[-4:] == "html":
            headers["Content-Type"] = "text/html"

        with open(file_name, 'r') as file:
            content = file.read()
            return self.form_response(200, headers, content)

    def moved_permanently(self, new_domain):
        """Builds and returns the response for a 301, moved permanently HTTP error"""
        resp = self.form_response(301, {"Location": new_domain}, "")
        return resp

    def not_found(self):
        """Builds and returns the response for a 404, not found HTTP error"""
        return self.form_response(404, {}, "404 Not Found")

    def method_not_allowed(self):
        """Builds and reutns the response for a 405, method not allowed HTTP error"""
        return self.form_response(405, {"Allow":"GET"}, "405 Method Not Allowed")



class HttpRequest():
    path = request_type = http_version = ""
    privileged = False
    headers = {}

    def __init__(self, request_string) -> None:
        """Parses and breaks up the request"""
        fields = request_string.split("\r\n")

        a = fields[0].split(" ")
        self.request_type = a[0]
        self.path = a[1]
        self.http_version = a[2]

        dir_path = f"./www{self.path}"
        self.relative = os.path.relpath(dir_path)
        self.normalized = os.path.normpath(dir_path)

        # https://stackoverflow.com/questions/39090366/how-to-parse-raw-http-request-in-python-3
        fields = fields[1:] #ignore the GET / HTTP/1.1
        output = {}
        for field in fields:
            try:
                key,value = field.split(':', 1)
                output[key] = value
            except:
                continue

        self.headers = output

    def __str__(self) -> str:
        return f"type: {self.request_type} | path: {self.path} | http version: {self.http_version} | headers: {self.headers}"

    def validateAndFormResponse(self):
        """Performs the error checks to validate if the request is valid / allowed. This will return the appropriate response version (str)
        for the request object."""
        response: HttpResponse = HttpResponse()

        file_to_serve = self.normalized

        if self.request_type != "GET":
            return response.method_not_allowed()
        
        # we'll determine whether the requested path is
        # valid. If the relative path contains "..", we know we're outside of
        # our directory and should return a 404
        if ".." in self.relative or not os.path.exists(self.normalized):
            return response.not_found()
        
        # if dir, we want the index, or handle 301 for incorrect paths
        if os.path.isdir(self.normalized):
            if self.path[-1] == "/":
                file_to_serve += "/index.html"
            # return 301 to correct paths
            else:
                return response.moved_permanently(f'http://127.0.0.1:8080{self.path}/')
        
        return response.serve_file(file_to_serve)


