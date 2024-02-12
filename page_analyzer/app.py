from flask import (
    Flask,
    render_template,
    flash,
    get_flashed_messages,
    make_response,
    redirect,
    request,
    url_for,
)
from dotenv import load_dotenv
from .validator import validate
import os
import psycopg2
import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)

@app.route('/', methods=['GET', 'POST'])
def index():
    errors = ''

    if request.method == "GET":
        return render_template('index.html', errors=errors)

    if request.method == "POST":
        name = request.form.to_dict['name']
        errors = validate(name)
        if errors:
             return render_template('index.html', errors=errors)
        else:
             cur = conn.cursor()
             cur.execute("insert into urls (name, created_at) values (%(name)s, %(date)s) returning id", {'name': name, 'date': datetime.datetime.now()})
             id = cur.fetchone()[0]
             cur.close()
             conn.close()
             return redirect(url_for(site_detail, id))

@app.route('/urls')
def sites():
        cur = conn.cursor()
        cur.execute("SELECT id, name from urls")
        sites = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('sites.html', sites=sites)


@app.route('/urls/<id>')
def site_detail(id):
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at from urls where id = %s", (id,))
    site = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('site_detail.html', site=site)