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
from urllib.parse import urlparse
import os, sys, datetime
import psycopg2
import requests
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['GET', 'POST'])
def sites():
    if request.method == "GET":
        with conn.cursor() as cur:
            cur.execute("SELECT id, name from urls order by created_at desc")
            sites = []
            for row in cur.fetchall():
                site = {}
                site['id'] = row[0]
                site['name'] = row[1]
                with conn.cursor() as cur_inner:
                    cur_inner.execute("select url_check.created_at, url_check.status_code from url_check join urls on url_check.url_id=urls.id where urls.id=%s order by created_at desc limit 1", (site['id'],))
                    data = cur_inner.fetchone()
                    if data:
                        site['last_check'] = data[0]
                        site['status_code'] = data[1]
                sites.append(site)
        return render_template('sites.html', sites=sites)
    
    if request.method == "POST":
        url = request.form.to_dict()['url']
        errors = validate(url)
        if errors:
            flash(errors, 'error')
            return redirect(url_for('index'))
        else:
            url = urlparse(url)
            name = url.scheme + "://" + url.netloc # normalize name
            with conn.cursor() as cur:
                cur.execute("select id from urls where name = %s", (name,))
                data = cur.fetchone()
                if not data:
                    cur.execute("insert into urls (name, created_at) values (%(name)s, %(date)s) returning id", {'name': name, 'date': datetime.datetime.now()})
                    id = cur.fetchone()[0]
                    conn.commit()
                    flash('Страница успешно добавлена')
                else:
                    id = data[0]
                    flash('Страница уже существует')
            return redirect(url_for('site_detail', id=id))

@app.route('/urls/<id>')
def site_detail(id):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, created_at from urls where id = %s", (id,))
        site = {}
        data = cur.fetchone()
        site['id'] = data[0]
        site['name'] = data[1]
        site['created_at'] = data[2]
    with conn.cursor() as cur:
        cur.execute("SELECT id, created_at, status_code, h1, title, description from url_check where url_id = %s order by created_at desc", (id,))
        checks = []
        for row in cur.fetchall():
            check = {}
            check['id'] = row[0]
            check['created_at'] = row[1]
            check['status_code'] = row[2]
            check['h1'] = row[3]
            check['title'] = row[4]
            check['description'] = row[5]
            checks.append(check)
    return render_template('site_detail.html', site=site, checks=checks)

@app.route('/urls/<id>/checks', methods = ['POST'])
def check_site(id):
    url_id = id
    created_at = datetime.datetime.now()
    with conn.cursor() as cur:
        cur.execute("select name from urls where id=%s", (url_id,))
        url = cur.fetchone()[0]
    try:
        r = requests.get(url)
        status_code = r.status_code
        soup = BeautifulSoup(r.content, 'html.parser')
        h1_list = soup.select('h1')
        if h1_list:
            h1 = h1_list[0].text.strip()
        else:
            h1 = ''
        title_list = soup.select('title')
        if title_list:
            title = title_list[0].text.strip()
        else:
            title = ''
        description = soup.find('meta', { 'name':'description' }).get('content').strip()
        
    except:
        flash('Произошла ошибка при проверке')
        return redirect(url_for('site_detail', id=id))

    with conn.cursor() as cur:
        cur.execute("insert into url_check (url_id, created_at, status_code, h1, title, description) values (%(url_id)s, %(date)s, %(status_code)s, %(h1)s, %(title)s, %(description)s)", {'url_id': url_id, 'date': created_at, 'status_code': status_code, 'h1': h1, 'title': title, 'description': description})
        conn.commit()
    flash("Страница успешно проверена")
    return redirect(url_for('site_detail', id=id))