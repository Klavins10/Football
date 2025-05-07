from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'man_patik_fubols'

# Routes
@app.route('/')
def index():
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    c.execute('SELECT * FROM teams')
    teams = c.fetchall()
    conn.close()
    return render_template('index.html', teams=teams)

@app.route('/team/<int:team_id>')
def team(team_id):
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    c.execute('SELECT * FROM teams WHERE id = ?', (team_id,))
    team = c.fetchone()
    c.execute('SELECT * FROM players WHERE team_id = ?', (team_id,))
    players = c.fetchall()
    c.execute('SELECT * FROM comments WHERE team_id = ?', (team_id,))
    comments = c.fetchall()
    conn.close()
    return render_template('team.html', team=team, players=players, comments=comments)

@app.route('/matches')
def matches():
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    c.execute('''SELECT m.*, t1.name as home_team, t2.name as away_team 
                 FROM matches m
                 JOIN teams t1 ON m.home_team_id = t1.id
                 JOIN teams t2 ON m.away_team_id = t2.id''')
    matches = c.fetchall()
    conn.close()
    return render_template('matches.html', matches=matches)

# Admin routes
@app.route('/admin')
def admin_login():
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    c.execute('SELECT * FROM teams')
    teams = c.fetchall()
    c.execute('''
        SELECT p.id, p.name, t.name as team_name 
        FROM players p 
        JOIN teams t ON p.team_id = t.id
    ''')
    players = c.fetchall()
    c.execute('''
        SELECT m.id, t1.name as home_team, t2.name as away_team, m.date, m.time
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
    ''')
    matches = c.fetchall()
    conn.close()
    return render_template('admin/dashboard.html', teams=teams, players=players, matches=matches)

@app.route('/admin/login', methods=['POST'])
def admin_auth():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    c.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password))
    admin = c.fetchone()
    conn.close()
    
    if admin:
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('admin_login'))

# Team CRUD operations
@app.route('/admin/team/add', methods=['GET', 'POST'])
def add_team():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        founded = request.form['founded']
        stadium = request.form['stadium']
        logo = request.form['logo']
        
        conn = sqlite3.connect('football.db')
        c = conn.cursor()
        c.execute('INSERT INTO teams (name, city, founded, stadium, logo) VALUES (?, ?, ?, ?, ?)',
                 (name, city, founded, stadium, logo))
        conn.commit()
        conn.close()
        
        flash('Team added successfully')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_team.html')

@app.route('/admin/team/edit/<int:team_id>', methods=['GET', 'POST'])
def edit_team(team_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        founded = request.form['founded']
        stadium = request.form['stadium']
        logo = request.form['logo']
        
        c.execute('''UPDATE teams 
                    SET name = ?, city = ?, founded = ?, stadium = ?, logo = ?
                    WHERE id = ?''',
                 (name, city, founded, stadium, logo, team_id))
        conn.commit()
        conn.close()
        
        flash('Team updated successfully')
        return redirect(url_for('admin_dashboard'))
    
    c.execute('SELECT * FROM teams WHERE id = ?', (team_id,))
    team = c.fetchone()
    conn.close()
    return render_template('admin/edit_team.html', team=team)

@app.route('/admin/team/delete/<int:team_id>')
def delete_team(team_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    c.execute('DELETE FROM teams WHERE id = ?', (team_id,))
    conn.commit()
    conn.close()
    
    flash('Team deleted successfully')
    return redirect(url_for('admin_dashboard'))

# Player CRUD operations
@app.route('/admin/player/add', methods=['GET', 'POST'])
def add_player():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        team_id = request.form['team_id']
        position = request.form['position']
        number = request.form['number']
        
        c.execute('INSERT INTO players (name, team_id, position, number) VALUES (?, ?, ?, ?)',
                 (name, team_id, position, number))
        conn.commit()
        conn.close()
        
        flash('Player added successfully')
        return redirect(url_for('admin_dashboard'))
    
    c.execute('SELECT * FROM teams')
    teams = c.fetchall()
    conn.close()
    return render_template('admin/add_player.html', teams=teams)

@app.route('/admin/player/edit/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        team_id = request.form['team_id']
        position = request.form['position']
        number = request.form['number']
        
        c.execute('''
            UPDATE players 
            SET name = ?, team_id = ?, position = ?, number = ?
            WHERE id = ?
        ''', (name, team_id, position, number, player_id))
        conn.commit()
        conn.close()
        flash('Player updated successfully!')
        return redirect(url_for('admin_dashboard'))
    
    c.execute('SELECT * FROM players WHERE id = ?', (player_id,))
    player = c.fetchone()
    c.execute('SELECT * FROM teams')
    teams = c.fetchall()
    conn.close()
    return render_template('admin/edit_player.html', player=player, teams=teams)

@app.route('/admin/player/delete/<int:player_id>')
def delete_player(player_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    c.execute('DELETE FROM players WHERE id = ?', (player_id,))
    conn.commit()
    conn.close()
    flash('Player deleted successfully!')
    return redirect(url_for('admin_dashboard'))

# Match CRUD operations
@app.route('/admin/match/add', methods=['GET', 'POST'])
def add_match():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        home_team_id = request.form['home_team_id']
        away_team_id = request.form['away_team_id']
        date = request.form['date']
        time = request.form['time']
        stadium = request.form['stadium']
        
        c.execute('''INSERT INTO matches (home_team_id, away_team_id, date, time, stadium)
                    VALUES (?, ?, ?, ?, ?)''',
                 (home_team_id, away_team_id, date, time, stadium))
        conn.commit()
        conn.close()
        
        flash('Match added successfully')
        return redirect(url_for('admin_dashboard'))
    
    c.execute('SELECT * FROM teams')
    teams = c.fetchall()
    conn.close()
    return render_template('admin/add_match.html', teams=teams)

@app.route('/admin/match/edit/<int:match_id>', methods=['GET', 'POST'])
def edit_match(match_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        home_team_id = request.form['home_team_id']
        away_team_id = request.form['away_team_id']
        date = request.form['date']
        time = request.form['time']
        stadium = request.form['stadium']
        
        c.execute('''
            UPDATE matches 
            SET home_team_id = ?, away_team_id = ?, date = ?, time = ?, stadium = ?
            WHERE id = ?
        ''', (home_team_id, away_team_id, date, time, stadium, match_id))
        conn.commit()
        conn.close()
        flash('Match updated successfully!')
        return redirect(url_for('admin_dashboard'))
    
    c.execute('SELECT * FROM matches WHERE id = ?', (match_id,))
    match = c.fetchone()
    c.execute('SELECT * FROM teams')
    teams = c.fetchall()
    conn.close()
    return render_template('admin/edit_match.html', match=match, teams=teams)

@app.route('/admin/match/delete/<int:match_id>')
def delete_match(match_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('football.db')
    c = conn.cursor()
    c.execute('DELETE FROM matches WHERE id = ?', (match_id,))
    conn.commit()
    conn.close()
    flash('Match deleted successfully!')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True) 