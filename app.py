from flask import Flask, render_template, url_for, request, send_from_directory, redirect, make_response, session
from flask_session import Session
import pandas as pd
import plotly.express as px
import ollama

app = Flask(__name__, static_folder='static', static_url_path='/')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'cuhk'  # Do not expose this
app.config['PERMANENT_SESSION_LIFETIME'] = 1800 # Expiry: 30 mins
app.config['SESSION_TYPE'] = 'cachelib' # Session as files in flask_session folder
Session(app)  # Initialize session in flask app


@app.route('/')
def default():
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/red_panda')
def red_panda():
    return render_template('red_panda.html')

@app.route('/member/', defaults={'user': ''})
@app.route('/member/<string:user>')
def member(user):
    print(user)
    premium = (user.lower() == 'cuhk')
    return render_template('member.html', premium=premium, user=user)

@app.route('/school')
def school():
    schools = {'CUHK':  'https://www.cuhk.edu.hk',
               'HKU':   'https://www.hku.hk',
               'HKUST': 'https://hkust.edu.hk',}
    return render_template('school.html', schools=schools)

@app.route('/test_get')
def test_get():
    return request.args

@app.route('/welcome_v2')
def welcome_v2():
    user = request.args.get('user', '')
    return render_template('welcome_get.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = request.form.get('user', '')
    pw = request.form.get('password', '')
    auth_user = None
    if (user, pw) in [('cuhk', 'comm'), ('jackie', 'redpanda')]:
        auth_user = user
    return render_template('login.html', auth_user=auth_user)

@app.route('/uploaded_file/<string:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/upload_img', methods=['GET', 'POST'])
def upload_img():
    img = request.files.get('user_file')
    if img and img.filename.endswith('.jpg'):
        path = f"{app.config['UPLOAD_FOLDER']}/{img.filename}"
        img.save(path)
    return render_template('upload_img.html')

@app.route('/chat_img', methods=['GET', 'POST'])
def chat_img():
    prompt = request.form.get('prompt')
    img = request.files.get('image')
    content = None
    if prompt and img and img.filename.endswith('.jpg'):
        path = f"{app.config['UPLOAD_FOLDER']}/{img.filename}"
        img.save(path)
        messages = [{'role': 'user', 'content': prompt, 'images': [path]}]
        response = ollama.chat(model='llava', messages=messages)
        content = response.message.content
    return render_template('chat_img.html', content=content)

@app.route('/plot_passenger')
def plot_passenger():
    url = 'https://www.immd.gov.hk/opendata/eng/transport/immigration_clearance/statistics_on_daily_passenger_traffic.csv'
    year_input = request.args.get('year')
    content = None
    if year_input:
        year = int(year_input)
        df = pd.read_csv(url)
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
        df['Year'] = df['Date'].dt.year
        gb = df.groupby(['Year', 'Control Point', 'Arrival / Departure'])
        agg = gb.agg(Total=('Total', 'sum')).reset_index()
        fig_pie = px.pie(agg.loc[agg['Year'] == year],
                         values='Total',
                         names='Control Point',
                         title=f'Annual Passenger Traffic by Control Point ({year})',
                         template='plotly_dark',
                         width=1200, height=600)
        fig_pie.update_traces(hoverinfo='label+value',
                              textinfo='label+percent',
                              textposition='outside',
                              marker={'line': {'color': '#FFFFFF', 'width': 2}})
        content = fig_pie.to_html()
    return render_template('plot_passenger.html', content=content)

@app.route('/set_cookies')
def set_cookies():
    currency = request.args.get('currency')
    if currency not in ('CNY', 'HKD', 'USD'):
        currency = 'HKD'
    content = render_template('cookies.html', currency=currency)
    response = make_response(content)
    response.set_cookie(key='ccy', value=currency, max_age=60 * 60 * 24)
    return response

@app.route('/login_session', methods=['GET', 'POST'])
def login_session():
    user = request.form.get('user', '')
    pw = request.form.get('password', '')
    logoff = 'logoff' in request.args
    if (user, pw) in [('cuhk', 'comm'), ('jackie', 'redpanda')]:
        session['auth_user'] = user
    elif logoff and 'auth_user' in session:
        session.pop('auth_user')
    return render_template('login_session.html')


if __name__ == '__main__':
    app.run()
