#!/usr/bin/env python3
  
import datetime
import os
import posixpath
import http.server
import sys
import urllib.request, urllib.parse, urllib.error
import html
import shutil
import mimetypes
import re
from io import BytesIO

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
 
    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()
 
    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()
 
    def do_POST(self):
        """Serve a POST request."""
        # Log the request body to a file for debugging
        #logself = self
        #self.log_request_body(logself)
        r, ip, message = self.deal_post_data()
        print((r, ip, message))
        f = BytesIO()
        if r == 'succeeded':
            f.write(b"Success")
        else:
            f.write(b"Failed")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()
        
    def deal_post_data(self):
        global serverpath 
        line = b'' #Initialize line data as byte
        file_data = b''  # Initialize file_data as an empty byte string
        in_file_data = False #Initialize in file as boolean
        newid = ''
        finalpath = ''
        content_type = self.headers['content-type']
        if not content_type:
            return (False, "Content-Type header doesn't contain boundary")
        boundary = content_type.split("=")[1]
        boundary = boundary.replace('"','').encode()
        end_boundary = boundary + b"--"
        totalbytes = int(self.headers['content-length'])
        remainbytes = totalbytes
        #modify serverpath with alternate upload dir  
        if uDir:
            serverpath = os.path.join(os.getcwd(),uDir)
        else:
            serverpath = os.getcwd()
   
        #Process request
        while remainbytes > 0:
            #print(remainbytes)
            line = self.rfile.readline()
            remainbytes -= len(line)

            if in_file_data:
                if boundary in line:                
                    in_file_data = False
                    file_data = file_data[:-2]  # Remove the last CRLF before boundary
                    if end_boundary in line:
                        break  # End of data
                else:
                    file_data += line
                    continue

            if end_boundary in line:
                        break  # End of data
            if boundary in line:
                line = self.rfile.readline()
                remainbytes -= len(line)
                id = re.findall(r'Content-Disposition.*name="id"', line.decode())
                reqpath = re.findall(r'Content-Disposition.*name="path"', line.decode())
                fn = re.findall(r'Content-Disposition.*name="filename"; filename="(.*)"', line.decode())
                if not fn:
                    fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode()) ## System.Net.WebClient
                if fn:
                    in_file_data = True
                    file_name = fn
                    file_data = file_data[:-2]
                    line = self.rfile.readline()
                    remainbytes -= len(line)
                    line = self.rfile.readline()
                    remainbytes -= len(line)

                elif reqpath:
                    line = self.rfile.readline()
                    remainbytes -= len(line)
                    line = self.rfile.readline()
                    remainbytes -= len(line)
                    reqpath = line
                    ip_address = self.client_address[0]
                    #remove \r\n
                    reqpathstr = reqpath.decode()
                    reqpathstr = reqpathstr.replace("\r","")
                    reqpathstr = reqpathstr.replace("\n","")
                    if reqpathstr.startswith('/') or reqpathstr.startswith('\\'):
                        reqpathstr = reqpathstr.strip('/')
                        reqpathstr = reqpathstr.strip('\\')
                    reqpathstr = reqpathstr.replace('\\','/')
                    reqpathstr = reqpathstr.replace('\\','/')
                    reqpathstr = reqpathstr.replace('//','/')
                    reqpathstr = reqpathstr.replace(':','')
                    reqpathstr = os.path.join(ip_address,reqpathstr)
                    finalpath = os.path.join(serverpath,reqpathstr)

                elif id:
                    #print(line)
                    line = self.rfile.readline()
                    #print(line)
                    remainbytes -= len(line)
                    line = self.rfile.readline()
                    #print(line)
                    remainbytes -= len(line)
                    line = line.decode()
                    line = line.replace("\r","")
                    line = line.replace("\n","")
                    newid = line
                    
        if finalpath != '':
            serverpath = finalpath                    
        
        if newid != '':
            serverpath = serverpath.replace(ip_address,newid)

        serverpath = serverpath.lower()
        if not os.path.exists(serverpath):
            os.makedirs(serverpath)

        fn = os.path.join(serverpath, file_name[0])
        #print(f'Final upload path: {serverpath}')
        try:
            with open(fn, 'wb') as out:
                out.write(file_data)
            return ('succeeded',self.client_address,fn )
        except:
            return ('Failed',self.client_address,fn )
          
    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f
 
    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = BytesIO()
        displaypath = html.escape(urllib.parse.unquote(self.path))
        f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write(("<html>\n<title>Directory listing for %s</title>\n" % displaypath).encode())
        f.write(("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath).encode())
        f.write(b"<hr>\n")
        f.write(b"<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write(b"<input name=\"file\" type=\"file\"/>")
        f.write(b"<input type=\"submit\" value=\"upload\"/></form>\n")
        f.write(b"<hr>\n<ul>\n")
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write(('<li><a href="%s">%s</a>\n'
                    % (urllib.parse.quote(linkname), html.escape(displayname))).encode())
        f.write(b"</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f
 
    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        path = path.replace('\\','/')
        path = path.replace('\\','/')
        path = path.replace('//','/')
        path = path.replace(':','')
        words = path.split('/')
        words = [_f for _f in words if _f]
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path
 
    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)
 
    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """
 
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']
 
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })
 
    def log_request_body(logself):
        # Generate a unique filename for the log
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"request_log_{timestamp}.txt"
        log_dir = "request_logs"  # Directory to store log files
        os.makedirs(log_dir, exist_ok=True)  # Ensure the log directory exists
        log_path = os.path.join(log_dir, log_filename)

        # Read the full request body
        content_length = int(logself.headers['Content-Length'])
        request_body = logself.rfile.read(content_length)

        # Write the request body to the log file
        with open(log_path, 'wb') as log_file:
            log_file.write(request_body)
         
def test(HandlerClass = SimpleHTTPRequestHandler,
         ServerClass = http.server.HTTPServer):
    http.server.test(HandlerClass, ServerClass)
 
if __name__ == '__main__':
    if __name__ == '__main__':
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--bind', '-b', default='0.0.0.0', metavar='ADDRESS',
                        help='Specify alternate bind address [default: all interfaces]')
        parser.add_argument('--port', '-p',  default=8443, type=int,
                        help='Specify alternate port [default: 8443]')
        parser.add_argument('--uploadDir', '-u', default='uploads', type=str,
                        help='Specify alternate upload location [default: Current Dir]'
                        'Relative path in RunDir')
        args = parser.parse_args()
        if args.uploadDir:
            global uDir
            uDir = args.uploadDir
        
        http.server.test(HandlerClass=SimpleHTTPRequestHandler, port=args.port, bind=args.bind)

