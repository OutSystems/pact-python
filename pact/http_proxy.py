"""Http Proxy to be used as provider url in verifier."""
from werkzeug.local import LocalStack
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from pymemcache.client import base
import json
import logging
import io
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
localstack = LocalStack()
PROXY_PORT = 1234
#handlers = {}
client = base.Client(('localhost', 11211))

def shutdown_server():
    """Shutdown Http Proxy server."""
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if shutdown is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    shutdown()

def _match_states(payload):
    """Match states in payload against stored message handlers."""
    log.info(f'Find handler from payload: {payload}')
    #handlers = localstack.pop()
    bin_data= client.get("expected")
    json_data = bin_data.decode('utf-8').replace("'", '"')
    json_data = json_data.replace('"{"','{\"')
    json_data = json_data.replace('"}','}') 
    json_data = json_data.replace("N}",'N"}')
    json_data = json_data.replace('"true','true')
    json_data = json_data.replace('true"','true')
    json_data = json_data.replace("true",'"true"')
    handlers = json.loads(json_data)
    log.info(f'handlers: {handlers}')
    states = handlers['messageHandlers']
    log.debug(f'Setup states: {handlers}')
    provider_states = payload['providerStates']

    for state in provider_states:
        matching_state = state['name']
        if matching_state in states:
            return states[matching_state]
    raise RuntimeError('No matched handler.')

@app.route('/', methods=['POST'])
def home():
    """Match states with provided message handlers."""
    payload = request.json
    message = _match_states(payload)
    res = jsonify({
        'contents': message
    })
    res.status_code = 200
    return res

@app.route('/ping', methods=['GET'])
def ping():
    """Check whether the server is available before setting up states."""
    res = jsonify({
        'ping': 'pong'
    })
    res.status_code = 200
    return res

@app.route("/setup", methods=['POST'])
def setup():
    """Endpoint to setup states.

    Use localstack to store payload.
    """
    payload = request.json
    # Store payload in localstack
    #localstack.push(payload)
    client.set('expected',payload)
    res = jsonify(payload)
    res.status_code = 201
    return res

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown Http Proxy server."""
    shutdown_server()
    return 'Server shutting down...'

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    res = e.get_response()
    res.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    res.content_type = "application/json"
    return res

@app.errorhandler(RuntimeError)
def handle_runtime_error(e):
    """Handle the RuntimeError.

    Handle HTML stacktrace when RuntimeError occurs due to no matched handler.
    when the verifier fails.
    """
    res = jsonify({
        "name": "RuntimeError",
        "description": str(e),
    })
    res.status_code = 500
    res.content_type = "application/json"
    return res


if __name__ == '__main__':
    app.run(debug=True, port=PROXY_PORT)
