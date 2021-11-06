from tester import Tester
from ga import GeneticAlgorithm
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import data_gen

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socketio = SocketIO(app, message_queue=os.getenv(
    'REDIS_URL'), cors_allowed_origins=os.getenv('CLIENT_ORIGIN'))


@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


@socketio.on('connect')
def connect():
    join_room(request.sid)
    emit('connect-response',
         {'data': 'Client {} connected'.format(request.sid), 'id': request.sid})
    print('Client {} connected'.format(request.sid))


@socketio.on('disconnect')
def disconnect():
    leave_room(request.sid)
    print('Client {} disconnected'.format(request.sid))


@socketio.on('data-in')
def data_in(data):
    id = data['id'] if 'id' in data else request.sid
    boxes = data['boxes']
    grid_x = data['grid_x']
    grid_y = data['grid_y']
    grid_z = data['grid_z']
    mutation_probability = data['mutation_probability']
    max_generation = data['max_generation']
    population_size = data['population_size']

    population = data_gen.loadData(
        boxes, grid_x, grid_y, grid_z, population_size)

    GA = GeneticAlgorithm(population, mutation_probability,
                          max_generation, room_id=id)

    emit("status", {"status": "ga-begin"}, room=id)
    GA.start()
    emit("status", {"status": "ga-end"}, room=id)

    Test = Tester(GA, show=False, save=True, savePath='static', room_id=id)

    emit("status", {"status": "generate-best-fitness-begin"}, room=id)
    path = Test.getBestIndividual("fitness")
    emit("status", {"status": "generate-best-fitness-end",
                    "graph": path}, room=id)

    emit("status", {"status": "generate-best-center_of_mass-begin"}, room=id)
    path = Test.getBestIndividual("center_of_mass")
    emit("status", {"status": "generate-best-center_of_mass-end",
                    "graph": path}, room=id)

    emit("status", {"status": "generate-best-volume-begin"}, room=id)
    path = Test.getBestIndividual("volume")
    emit("status", {"status": "generate-best-volume-end",
                    "graph": path}, room=id)

    emit("status", {"status": "generate-best-weight-begin"}, room=id)
    path = Test.getBestIndividual("weight")
    emit("status", {"status": "generate-best-weight-end",
                    "graph": path}, room=id)

    emit("status", {"status": "done"}, room=id)


if __name__ == '__main__':
    socketio.run(app)
