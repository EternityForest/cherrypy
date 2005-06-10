"""
Copyright (c) 2004, CherryPy Team (team@cherrypy.org)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, 
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, 
      this list of conditions and the following disclaimer in the documentation 
      and/or other materials provided with the distribution.
    * Neither the name of the CherryPy Team nor the names of its contributors 
      may be used to endorse or promote products derived from this software 
      without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os, os.path
import time
import sys
import socket
import httplib
import threading
from cherrypy import cpg


HOST = "127.0.0.1"
PORT = 8000

def port_is_free():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        s.close()
        return False
    except socket.error:
        return True


def startServer(serverClass=None):
    if serverClass is None:
        cpg.server.start(initOnly=True)
    else:
        if not port_is_free():
            raise IOError("Port %s is in use; perhaps the previous server "
                          "did not shut down properly." % port)
        t = threading.Thread(target=cpg.server.start, args=(False, serverClass))
        t.start()
        time.sleep(1)


def stopServer():
    cpg.server.stop()
    if cpg.config.get('server.threadPool') > 1:
        # With thread-pools, it can take up to 1 sec for the server to stop
        time.sleep(1.1)


def getPage(url, headers=None, method="GET"):
    
    # The trying 10 times is simply in case of socket errors.
    # Normal case--it should run once.
    trial = 0
    while trial < 10:
        try:
            conn = httplib.HTTPConnection('%s:%s' % (HOST, PORT))
##            conn.set_debuglevel(1)
            conn.putrequest(method.upper(), url)
            
            for key, value in headers:
                conn.putheader(key, value)
            conn.endheaders()
            
            # Handle response
            response = conn.getresponse()
            
            cpg.response.status = "%s %s" % (response.status, response.reason)
            
            cpg.response.headerMap = {}
            for line in response.msg.headers:
                key, value = line.split(":", 1)
                cpg.response.headerMap[key.strip()] = value.strip()
            cpg.response.headers = cpg.response.headerMap
            
            b = cpg.response.body = response.read()
##            print "body:", repr(b)
            
            conn.close()
            return
        except socket.error:
            trial += 1
            if trial == 10:
                raise
            else:
                time.sleep(0.5)


def request(url, headers=None, method="GET"):
    if headers is None:
        headers = []
    
    if cpg._httpserver is None:
        requestLine = "%s %s HTTP/1.0" % (method.upper(), url)
        found = False
        for k, v in headers:
            if k.lower() == 'host':
                found = True
                break
        if not found:
            headers.append(("Host", "%s:%s" % (HOST, PORT)))
        cpg.server.request(HOST, HOST, requestLine, headers, None)
        cpg.response.body = "".join(cpg.response.body)
    else:
        getPage(url, headers, method)

