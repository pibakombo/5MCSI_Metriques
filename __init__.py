from flask import Flask, render_template_string, render_template, jsonify
from flask import render_template
from flask import json
from datetime import datetime
from urllib.request import urlopen
import sqlite3

app = Flask(__name__)

@app.route("/contact/")
def MaPremiereAPI():
    return render_template("contact.html")

@app.route('/tawarano/')
def meteo():
    response = urlopen('https://samples.openweathermap.org/data/2.5/forecast?lat=0&lon=0&appid=xxx')
    raw_content = response.read()
    json_content = json.loads(raw_content.decode('utf-8'))
    results = []
    for list_element in json_content.get('list', []):
        dt_value = list_element.get('dt')
        temp_day_value = list_element.get('main', {}).get('temp') - 273.15 # Conversion de Kelvin en °c 
        results.append({'Jour': dt_value, 'temp': temp_day_value})
    return jsonify(results=results)

@app.route("/rapport/")
def mongraphique():
    return render_template("graphique.html")

@app.route("/histogramme/")
def monhistogramme():
    return render_template("histogramme.html")

@app.route('/extract-minutes/<date_string>')
def extract_minutes(date_string):
        date_object = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
        minutes = date_object.minute
        return jsonify({'minutes': minutes})

# Création d'une table SQLite pour stocker les commits (optionnel)
def init_db():
    conn = sqlite3.connect('commits.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS commits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commit_date TEXT)''')
    conn.commit()
    conn.close()

# Route pour extraire les minutes d'une date donnée
@app.route('/extract-minutes/<date_string>')
def extract_minutes(date_string):
    date_object = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
    minutes = date_object.minute
    return jsonify({'minutes': minutes})

# Fonction pour récupérer les commits via l'API GitHub
def get_commits_from_github():
    api_url = 'https://api.github.com/repos/OpenRSI/5MCSI_Metriques/commits'
    
    # Appel à l'API
    response = urlopen(api_url)
    commits_data = json.load(response)

    return commits_data

# Route pour afficher les commits et générer un graphique minute par minute
@app.route('/commits/')
def commits():
    # Récupérer les données des commits
    commits_data = get_commits_from_github()

    # Liste pour stocker les minutes des commits
    commit_minutes = []

    # Connexion à la base de données (SQLite)
    conn = sqlite3.connect('commits.db')
    c = conn.cursor()

    # Parcours des commits et extraction des minutes
    for commit in commits_data:
        commit_date = commit['commit']['author']['date']
        date_object = datetime.strptime(commit_date, '%Y-%m-%dT%H:%M:%SZ')
        minutes = date_object.minute
        commit_minutes.append(minutes)

        # Stockage dans SQLite
        c.execute("INSERT INTO commits (commit_date) VALUES (?)", (commit_date,))
    
    conn.commit()
    conn.close()

    # Génération du graphique en ligne avec des étoiles "★" pour chaque minute
    graph = ['★' * commit_minutes.count(minute) for minute in range(60)]
    
    # Génération du HTML pour le graphique
    graph_html = "<h2>Nombre de Commits par Minute</h2>"
    graph_html += "<table>"
    for minute, stars in enumerate(graph):
        graph_html += f"<tr><td>Minute {minute}:</td><td>{stars}</td></tr>"
    graph_html += "</table>"

    return render_template_string(graph_html)

@app.route('/')
def hello_world():
    return render_template('hello.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
