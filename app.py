import json

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///HighScoreDatabase.sqlite?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ScoreRecords(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    player_name = db.Column(db.String(20), nullable= False)
    score = db.Column(db.Integer, nullable= False)

    def __repr__(self):
        return '<ScoreRecords %r>' % self.id

def data_not_exist(name , score):
    all_records = get_records()
    for i in all_records:
        if name == i[1]:
            if i[2] < score:
                update_score(i[0], score)
                return False
            else:
                print('This name already has better or same score')
                return False
    return True

def get_high_scores_database():
    records = get_records()
    json = get_json(records)
    return json

def get_records():
    conn = sqlite3.connect('HighScoreDatabase.sqlite')
    records = conn.execute('SELECT id, player_name, score FROM score_records ORDER BY score DESC').fetchall()
    conn.close()
    return records

def get_json(records):
    data = {}
    i = 0
    for row in records:
        if i < 10:
            data[row[1]] = row[2]
            i += 1
        else: break
    data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    return json.dumps(data)

def update_score(idx, new_score):
    conn = sqlite3.connect('HighScoreDatabase.sqlite')
    conn.execute(f"UPDATE score_records set score = {int(new_score)} where id = {idx}")
    conn.commit()
    conn.close()


def add_new_score(file):
    data = json.loads(file)
    for player_name, player_score in data.items():
        if data_not_exist(player_name, player_score):
            conn = sqlite3.connect('HighScoreDatabase.sqlite')
            params = (player_name, player_score)
            conn.execute(f"INSERT INTO score_records(id, player_name, score) values (null ,?, ?)", params)
            conn.commit()
            conn.close()
            print('Success! ')

