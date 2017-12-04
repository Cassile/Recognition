#!/usr/bin/env python


import os
import posixpath
import BaseHTTPServer
import urllib
import cgi
import shutil
import mimetypes
import re
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import performRecognition
#import predict_2

class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET/HEAD/POST commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.

    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    #server_version = "SimpleHTTPWithUpload/" + __version__

    def do_GET(self):
        #print "Serve a GET request."
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        #print "Serve a HEAD request."
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        #print "Serve a POST request."
        r, info,fn = self.deal_post_data()

        #print r, info, fn
        performRecognition.recognize(fn)
        #predict_2.main("2.png")
        self.send_response(200)
        size = os.path.getsize(fn)
        # print type(fn)
        # print type(self.wfile)

        # #print "size",size
        self.send_header("Content-Description", "File Transfer")
        self.send_header("Content-Type","application/octet-stream")
        self.send_header("Cache-Control"," public, must-revalidate, max-age=0")
        self.send_header("Pragma","no-cache")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length",size)
        self.send_header("Content-Disposition", "inline; filename="+fn)
        self.send_header("Content-Transfer-Encoding:","binary\n")
        self.send_header("Connection", "Close")
        self.end_headers()

        data = open(fn, 'rb')
        l=data.read(1024)
        remainBytes = size
        self.wfile.write(l)
        #print "remainBytes:",remainBytes
        while(remainBytes - 1024>0):
            remainBytes = remainBytes - 1024
            #print "remainBytes:", remainBytes
            bufferSize = min(remainBytes,1024)
            l = data.read(bufferSize)
            self.wfile.write(l)
           #print "bufferSize",bufferSize
        self.wfile.close()


        
    def deal_post_data(self):
        print "Deal Picture"
        boundary = self.headers.plisttext.split("=")[1]
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        #print "line",line
        fn = re.findall(r'Content-Disposition: form-data; name="file"; filename="(.*)"', line)
        print "fn",fn

        if not fn:
            return (False, "Can't find out file name...","0")
        path = self.translate_path(self.path)
        fn = os.path.join(path, fn[0])
        #print "path",fn
        line = self.rfile.readline()
        #print "line", line
        remainbytes -= len(line)
        line = self.rfile.readline()
        #print "line", line
        remainbytes -= len(line)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?",fn)
                
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                #print preline,"\n"
                out.write(preline)
                out.close()
                return (True, "File '%s' upload success!" % fn, fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.",fn)

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        # "send_head"
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
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write("<hr>\n")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write("<input name=\"file\" type=\"file\"/>")
        f.write("<input type=\"submit\" value=\"upload\"/></form>\n")
        f.write("<hr>\n<ul>\n")
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
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
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
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
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
def load(file):
            with open(file, 'r') as file:
                return encode(str(file.read()))

def encode(file):
            return bytes(file)

def test(HandlerClass = SimpleHTTPRequestHandler, ServerClass = BaseHTTPServer.HTTPServer):
    #print"start"
    #performRecognition.recognize("test413.jpg")
    BaseHTTPServer.test(HandlerClass, ServerClass)


test()

