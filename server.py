import email.utils
import http.server
import os
import urllib
from collections import abc

from http.server import HTTPStatus
import sys

import logging as lg
lg.basicConfig(level=lg.DEBUG, format='%(levelname)-8s: %(message)s')

__version__ = '0.1.0'

class Cors_container(abc.Container) :
  def __init__(self, cors) :
    self.cors = tuple(
      tuple(addr.split(':')) for addr in cors.split(',')
    )

  def __contains__(self, addr) :
    url, port = addr if addr else 'NoURL', 'NoPort'
    return any(
      '*' == c_url or (url == c_url and (
        (not c_port) or port in c_port
      )) for c_url, *c_port in self.cors
    )

class RequestHandler(http.server.SimpleHTTPRequestHandler) :
  server_version = 'DashX_HTTP/' + __version__

  def __init__(self, *args, cors=None, **kwargs) :
    self.cors = Cors_container(cors)
    lg.info ('Cors: %s', self.cors.cors)
    super().__init__(*args, **kwargs)
  
  def do_GET(self):
    """Serve a GET request."""
    lg.info(self.headers)
    lg.info(list(self.headers.keys()))
    origin = self.headers['Origin']
    origin_pair = None
    if origin :
      origin = urllib.parse.urlsplit(origin)
      origin_pair = origin.hostname, origin.port
    lg.info('Origin: %s', origin)

    if origin_pair in self.cors :
      self.send_header(
        'Access-Control-Allow-Origin',
        (urllib.parse.urlunsplit(origin) if origin else '*')
      )
    else :
      lg.debug('Origin Pair: %s not in Cors', origin_pair)

    super().do_GET()

  def send_response_only(self, code, message=None):
    """Send the response header only."""
    if self.request_version != 'HTTP/0.9':
      if message is None:
        if code in self.responses:
          message = self.responses[code][0]
        else:
          message = ''
      if not hasattr(self, '_headers_buffer'):
        self._headers_buffer = []
      self._headers_buffer.insert(0, (
        "%s %d %s\r\n" % (
          self.protocol_version, code, message
        )).encode('latin-1', 'strict'))

def test(HandlerClass=http.server.BaseHTTPRequestHandler,
         ServerClass=http.server.ThreadingHTTPServer,
         protocol="HTTP/1.0", port=8000, bind=""):
  """Test the HTTP request handler class.

  This runs an HTTP server on port 8000 (or the port argument).

  """
  server_address = (bind, port)

  HandlerClass.protocol_version = protocol
  with ServerClass(server_address, HandlerClass) as httpd:
    sa = httpd.socket.getsockname()
    serve_message = "Serving HTTP on {host} port {port} (http://{host}:{port}/) ..."
    print(serve_message.format(host=sa[0], port=sa[1]))
    try:
      httpd.serve_forever()
    except KeyboardInterrupt:
      print("\nKeyboard interrupt received, exiting.")
      sys.exit(0)


if __name__ == '__main__':
  import argparse
  from functools import partial

  parser = argparse.ArgumentParser()
  parser.add_argument('--bind', '-b', default='', metavar='ADDRESS',
                      help='Specify alternate bind address '
                      '[default: all interfaces]')
  parser.add_argument('--directory', '-d', default=os.getcwd(),
                      help='Specify alternative directory '
                      '[default:current directory]')
  parser.add_argument('port', action='store',
                      default=8000, type=int,
                      nargs='?',
                      help='Specify alternate port [default: 8000]')
  parser.add_argument('--cors', '-c', metavar='URI',
                      help='Allow CORS for this URI. Use `*\' for all')
  args = parser.parse_args()
  handler_class = partial(RequestHandler,
                          directory=args.directory,
                          cors=args.cors)
  test(HandlerClass=handler_class, port=args.port, bind=args.bind)
