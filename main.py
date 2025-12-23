import json
from config import *
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

with open('form.json', 'r', encoding='utf-8-sig') as f:
    form_results_json = json.load(f)

with open('living.json', 'r', encoding='utf-8-sig') as f:
    living = json.load(f)

def form_res_into_dct(data):
    person_dict = {}
    for sublist in data:
        person_results = {}
        for i in range(len(sublist)-1):
            if sublist[i+1][1] in points.keys():
                person_results[sublist[i+1][0]] = points[sublist[i+1][1]]
            else:
                person_results[sublist[i+1][0]] = sublist[i+1][1]
        name = sublist[0][1].replace('ё', 'е').strip()
        person_dict[name] = person_results
    return person_dict

def points_for_person(name, neighbour, form_results):
    points = 0
    # smoking
    if form_results[name][I_SMOKE] != 1:
        points += form_results[neighbour][I_SMOKE] * form_results[name][RATE_SMOKE]
    else:
        points += 5
    # institute
    k = form_results[name][RATE_INSTITUTE]
    if form_results[name][INSTITUTE] == form_results[neighbour][INSTITUTE]:
        points_for_institute = 1
        if k < 2.5:
            k = 2.5
    else:
        points_for_institute = -1
    points += points_for_institute * k
    # personality
    k = form_results[name][RATE_PERSONALITY]
    if form_results[name][NEIGHBOUR_PERSONALITY] == form_results[neighbour][I_PERSONALITY]:
        points_for_personality = 1
        if k < 2.5:
            k = 2.5
    else:
        points_for_personality = -1
    points += points_for_personality * k
    # sleep
    k = form_results[name][RATE_SLEEP]
    n = abs(form_results[name][I_SLEEP] - form_results[neighbour][I_SLEEP])
    if (1 - n * 2/3) > 0 and k < 2.5:
        k = 2.5
    points += (1 - n * 2/3) * k
    # cleaning
    k = form_results[name][RATE_CLEAN]
    if form_results[name][NEIGHBOUR_CLEAN] != 0:
        n = abs(form_results[name][I_CLEAN] - form_results[neighbour][I_CLEAN])
        if (1 - n) > 0 and k < 2.5:
            k = 2.5
        points += (1 - n) * k
    else:
        points += 5
    # guests
    k = form_results[name][RATE_GUESTS]
    if form_results[name][NEIGHBOUR_GUESTS] != 2:
        n = abs(form_results[name][I_GUESTS] - form_results[neighbour][I_GUESTS])
        if (1 - n) > 0 and k < 2.5:
            k = 2.5
        points += (1 - n) * k
    else:
        points += 5
    # staying home
    k = form_results[name][RATE_HOME]
    n = abs(form_results[name][I_HOME] - form_results[neighbour][I_HOME])
    if (1 - n) > 0 and k < 2.5:
        k = 2.5
    points += (1 - n) * k

    return points

def find_fitting_room(name):
    form_results = form_res_into_dct(form_results_json)

    name = name.replace('ё', 'е').strip()
    
    # Проверяем, есть ли имя в данных
    if name not in form_results:
        return None, "Имя не найдено в базе данных"
    
    rooms_points = {room: {} for room in living.keys()}
    
    for room in living:
        # Проверяем комнаты на 2 и 3 человека
        for n in [2, 3]:
            if 0 < len(living[room][str(n)]) < n and form_results[name][GENDER] == form_results[living[room][str(n)][0]][GENDER]:
                neighbours = living[room][str(n)]
                for neighbour in neighbours:
                    points_name = points_for_person(name, neighbour, form_results)
                    points_neighbour = points_for_person(neighbour, name, form_results)
                    points = points_name + points_neighbour
                    if n == 2:
                        rooms_points[room][str(n)] = round(points * 2)
                    else:
                        rooms_points[room][str(n)] = round(points)
    
    # Находим комнату с максимальным количеством очков
    if rooms_points:
        max_key = max(rooms_points, key=lambda x: max(rooms_points[x].values(), default=0))
        max_value = rooms_points[max_key]
        if max_value:
            fitting_room = f"{max_key}-{list(max_value.keys())[0]}"
            return fitting_room, None
        else:
            return None, "Не найдено подходящих комнат"
    else:
        return None, "Не найдено подходящих комнат"

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    name = ""
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            fitting_room, error = find_fitting_room(name)
            if fitting_room:
                result = f"Подходящая вам комната - {fitting_room}"
        else:
            error = "Пожалуйста, введите имя"
    
    return render_template('index.html', result=result, error=error, name=name)

@app.route('/api/fitting_room/<name>', methods=['GET'])
def get_fitting_room(name):
    fitting_room, error = find_fitting_room(name)
    if fitting_room:
        return jsonify({"room": fitting_room, "message": f"Подходящая вам комната - {fitting_room}"})
    else:
        return jsonify({"error": error}), 404

if __name__ == '__main__':
    app.run(debug=True)
