from flask import Flask, request, render_template, jsonify
import threading
from client import Client  # Import your Client class from client.py

app = Flask(__name__)

client_instance = Client()  # Create a Client instance
client_thread = threading.Thread(target=client_instance.start)
client_thread.start()  # Start the client in a separate thread

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/execute_command', methods=['POST'])
def execute_command():
    command = request.form.get('command')
    
    if command == 'add':
        num = request.form.get('num')
        title = request.form.get('title')
        response = client_instance.add(num, title)
    elif command == 'lookup':
        num = request.form.get('num')
        title = request.form.get('title', '')
        response = client_instance.lookup(num, title)
    elif command == 'listall':
        response = client_instance.listall()
    elif command == 'predownload':
        num = request.form.get('num')
        response = client_instance.pre_download(num)
        return jsonify(response), response['status']  # Send the response directly
    elif command == 'download':
        num = request.form.get('num')
        title = request.form.get('title')
        peer_host = request.form.get('peer_host')
        peer_port = int(request.form.get('peer_port'))
        response = client_instance.download(num, title, peer_host, peer_port)
        return jsonify({'message': response}), 200  # Assuming the download method returns a message
    elif command == 'shutdown':
        client_instance.shutdown()  # Shutdown will exit the thread
        return jsonify({'message': 'Client shutting down...'}), 200
    else:
        return jsonify({'message': 'Invalid command.'}), 400

    return jsonify({'message': response}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)
