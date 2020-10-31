from flask import Flask, render_template, g, request, session, redirect, url_for
from database import connect_db, get_bd
from security import encrypt_password, check_encrypted_password
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(25)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
        db = get_bd()

        usr_cursor = db.execute('select id, name, password, expert, admin from users where name = ?', [user])
        user_result = usr_cursor.fetchone()
    return user_result


@app.route('/')
def index():
    user = get_current_user()
    db = get_bd()
    if user:
        questions_answ_curs = db.execute("select a.*, b.name from questions a inner join users b on a.asked_by_id = b.id \
                                         where expert_id = ? and answer_text is not NULL", [user['id']])
        questions_answ_result = questions_answ_curs.fetchall()

        return render_template('home.html', user = user, questions = questions_answ_result)

    return render_template('home.html', user = user)


@app.route('/register', methods = ['POST', 'GET'])
def register():
    user = get_current_user()
    db = get_bd()

    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        user_cursor = db.execute('select * from users where name = ?', [name])
        user_result = user_cursor.fetchone()

        if user_result:
            return render_template('register.html', error='The username already exists!!!')
        else:
            password_crpt = encrypt_password(password)
            # return '<h1> name: {} and password: {} </h1>'.format(name, password_crpt)

            db.execute('insert into users(name, password) values(?, ?)', [name, password_crpt])
            db.commit()
            session['user'] = name
            return redirect(url_for('index'))

    return render_template('register.html', user = user)


@app.route('/login', methods = ['GET', 'POST'])
def login():
    user = get_current_user()
    db = get_bd()
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        cursor = db.execute('select id, name, password from users where name = ?', [name])
        usr_result = cursor.fetchone()

        if check_encrypted_password(password, usr_result['password']):
            session['user'] = usr_result['name']
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))

    return render_template('login.html', user = user)


@app.route('/question/<id>', methods = ['POST', 'GET'])
def question(id):
    user = get_current_user()
    db = get_bd()
    if request.method == 'POST':
        answer = request.form['answer']
        db.execute("update questions set answer_text = ? where id = ?", [answer, id])
        db.commit()

    quest_cursor = db.execute('select a.*, b.name from questions as a inner join users as b on a.asked_by_id = b.id \
                               where a.id = ? and a.expert_id = ?', [id, user['id']])
    quest_result = quest_cursor.fetchone()

    return render_template('question.html', user = user, question_data = quest_result)


@app.route('/answer/<quest_id>')
def answer(quest_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    db = get_bd()
    quest_cursor = db.execute('select a.*, b.name from questions a '
                              'inner join users b on a.asked_by_id = b.id '
                              'where a.answer_text is NULL and a.id = ? and '
                              'a.expert_id = ?', [quest_id, user['id']])
    quest_result = quest_cursor.fetchone()

    if user['id'] == quest_result['expert_id']:
        return render_template('answer.html', user = user, quest_data = quest_result)

    return render_template('home.html', user=user)


@app.route('/ask',methods = ['POST', 'GET'])
def ask():
    user = get_current_user()
    db = get_bd()

    if not user:
        return redirect(url_for('login'))

    expert_cursor = db.execute("select * from users where expert = 'True'")
    expert_result = expert_cursor.fetchall()

    if request.method == 'POST':
        question = request.form['question']
        expert = request.form['expert']
        db.execute("insert into questions(question_text, asked_by_id, expert_id) values(?, ?, ?)", [question, user['id'], expert])
        db.commit()
        return redirect(url_for('ask'))

    return render_template('ask.html', user = user, experts = expert_result)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    db = get_bd()
    quest_cursor = db.execute('select a.*, b.name from questions a '
                              'inner join users b on a.asked_by_id = b.id '
                              'where a.answer_text is NULL and a.expert_id = ?', [user['id']])
    quest_result = quest_cursor.fetchall()

    return render_template('unanswered.html', user = user, questions = quest_result)


@app.route('/users')
def users():
    user = get_current_user()
    db = get_bd()
    if not user:
        return redirect(url_for('login'))

    cursor = db.execute('select * from users')
    result = cursor.fetchall()

    return render_template('users.html', user = user, all_users = result)


@app.route('/promote_to_expert/<id>')
def promote_to_expert(id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    if user['admin'] == 'True':
        db = get_bd()
        exp_cursor = db.execute('select * from users where id = ?', [id])
        exp_result = exp_cursor.fetchone()
        status = exp_result['expert']
        final_status = None
        if status == 'True':
            final_status = 'False'
        else:
            final_status = 'True'


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
