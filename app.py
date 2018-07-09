import os
import secrets
import bcrypt

from flask import Flask, render_template, request,\
    jsonify, redirect, session, url_for, flash,\
    send_from_directory, send_file
from werkzeug.utils import secure_filename
from core import *
import database


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)

    with app.app_context():
        wiki_config = tools.Config('config/wiki')
        if not wiki_config.exist():
            wiki_config.save({"name": None, "information": None, "main": None,
                         "disqus_url": None, "wiki_url": None})

        app_config = tools.Config('config/app')
        if not app_config.exist():
            app_config.save({"install": False, "secret_key": secrets.token_hex(16)})
            database.init_db()

        secret_key = app_config.load()['secret_key']

        print("config 폴더의 app 설정 파일에 들어 있는 내용은 절대로 유실하지 마세요.")
        print("You must not lose contents of app settings file in config folder.")

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=os.path.join('.', 'db.sqlite'),
    )

    database.init_app(app)

    def get_current_list():
        lists = {'new': [], 'edit': []}

        db = database.get_db()

        new_db = db.execute("SELECT name FROM docs_list ORDER BY datetime(date) DESC LIMIT 10")
        if new_db is not None:
            new_db = new_db.fetchall()
            for row in new_db:
                for element in row:
                    lists['new'].append(element)
        edit_db = db.execute("SELECT name FROM (history join docs_list using (id)) as t ORDER BY datetime(t.date) DESC LIMIT 10")
        if edit_db is not None:
            edit_db = edit_db.fetchall()
            for row in edit_db:
                for element in row:
                    lists['edit'].append(element)

        return lists

    def get_setting(file):
        return tools.Config('config/' + file).load()

    # 문서 관련 페이지
    # 문서 보기
    @app.route('/')
    def index():
        if get_setting('app')['install']:
            return redirect('/docs/{0}'.format(get_setting('wiki')['main']), code=302)
        else:
            return redirect('/setting/install', code=302)

    @app.route('/docs/<path:doc_name>')
    def doc_request(doc_name):
        db = database.get_db()

        name = (doc_name,)
        text = db.execute("SELECT html_data FROM docs join docs_list using (id) WHERE name = ?", name).fetchone()
        a = db.execute("SELECT * FROM docs").fetchone()

        sidebar_list = get_current_list()

        if text is None:
            return render_template('document/no_doc.html', subject=doc_name, setting=get_setting('wiki'),
                                   sidebar_list=sidebar_list, nav={'document': False})
        else:
            text = text['html_data']
            return render_template('document/view.html', subject=doc_name, text=text, setting=get_setting('wiki'),
                                   sidebar_list=sidebar_list, nav={'document': True})
    # 문서 부가 기능
    @app.route('/history/<path:doc_name>')
    def doc_history(doc_name):
        db = database.get_db()
        doc_id = db.execute("SELECT id FROM docs_list WHERE name=?", (doc_name,)).fetchone()

        if doc_id is not None:
            doc_id = doc_id['id']
            is_edit = True
        else:
            return '없는 문서'

        history = db.execute("SELECT * FROM history where id = ? ORDER BY version DESC",
                             (doc_id,)).fetchall()

        return render_template('document/history.html', subject=doc_name, setting=get_setting('wiki'),
                               sidebar_list=get_current_list(), nav={'document': False}, history=history)

    @app.route('/markdown/<path:doc_name>')
    def doc_markdown(doc_name):
        db = database.get_db()
        doc_id = db.execute("SELECT id FROM docs_list WHERE name=?", (doc_name,)).fetchone()

        if doc_id is not None:
            doc_id = doc_id['id']
            is_edit = True
        else:
            return '없는 문서'

        text = db.execute("SELECT markdown_data FROM history where id = ? ORDER BY version DESC LIMIT 1",
                          (doc_id,)).fetchone()

        return render_template('document/markdown.html', subject=doc_name, setting=get_setting('wiki'),
                               sidebar_list=get_current_list(), nav={'document': False}, text=text['markdown_data'])

    @app.route('/random')
    def random():
        db = database.get_db()
        doc_name = db.execute("SELECT name FROM docs_list ORDER BY RANDOM() LIMIT 1").fetchone()
        if doc_name:
            doc_name = doc_name['name']
            return redirect("/docs/{0}".format(doc_name), code=302)
        else:
            sidebar_list = get_current_list()
            return render_template('error/404.html', setting=get_setting('wiki'), sidebar_list=sidebar_list,
                                   nav={'document': False})

    # 문서 쓰기
    @app.route('/edit/<path:doc_name>')
    def doc_write(doc_name):
        sidebar_list = get_current_list()

        db = database.get_db()
        doc_id = db.execute("SELECT id FROM docs_list WHERE name = ?", (doc_name,)).fetchone()
        if doc_id is not None:  # 있는 글을 편집함.
            text = db.execute("SELECT markdown_data FROM history WHERE id = ? order by version DESC LIMIT 1",
                              (doc_id['id'],)).fetchone()
            return render_template('document/write.html', subject=doc_name, setting=get_setting('wiki'),
                                   sidebar_list=sidebar_list, text=text['markdown_data'], nav={'document': False})
        else:
            text = None
            return render_template('document/write.html', subject=doc_name, setting=get_setting('wiki'),
                                   sidebar_list=sidebar_list, nav={'document': False})

    @app.route('/preview', methods=['post'])
    def preview():
        text = request.form['text']
        translator = translate.Translator(text.replace("\n", "\r\n"))
        text = translator.compile()
        return jsonify(text)

    @app.route('/save/<path:doc_name>', methods=['post'])
    def doc_save(doc_name):
        db = database.get_db()
        doc_id = db.execute("SELECT id FROM docs_list WHERE name=?", (doc_name,)).fetchone()
        if doc_id is not None:
            doc_id = doc_id['id']
            is_edit = True
        else:
            is_edit = False

        markdown_text = request.form['mytext']
        translator = translate.Translator(markdown_text)
        html_text = translator.compile()

        if not is_edit:
            id = db.execute("SELECT max(id) FROM docs_list").fetchone()['max(id)']
            if id is None:
                id = 0
            id += 1
            docs_list_list = (id, doc_name)
            docs_list = (id, html_text)
            history_list = (id, 1, markdown_text)
            db.execute("INSERT into docs_list VALUES(?, ?, datetime('now', 'localtime'))", docs_list_list)
            db.execute("INSERT into docs VALUES(?, ?)", docs_list)
            db.execute("INSERT into history VALUES(?, ?, ?, datetime('now', 'localtime'))", history_list)
            db.commit()
            return redirect("/docs/{0}".format(doc_name), code=302)
        else:
            history_version = db.execute("SELECT max(version) FROM history where id = ?",
                                         (doc_id,)).fetchone()['max(version)'] + 1
            history_list = (doc_id, history_version, markdown_text)
            db.execute("INSERT into history VALUES(?, ?, ?, datetime('now', 'localtime'))", history_list)
            db.execute("UPDATE docs SET html_data = ? WHERE id = ?", (html_text, doc_id))
            db.commit()
            return redirect("/docs/{0}".format(doc_name), code=302)

    # 문서 지우기
    @app.route('/remove/<path:doc_name>')
    def doc_remove(doc_name):
        if 'id' in session:
            db = database.get_db()
            # 으악... 캐스트 캐이드를 디비 열 때마다 켜줘야 한다는데, 파이썬으로는 조작도 안되고.. 허;;
            # 일일이 지우는 수 밖에;;
            doc_id = db.execute("SELECT id FROM docs_list WHERE name=?", (doc_name,)).fetchone()['id']
            db.execute("DELETE FROM docs_list WHERE id=?", (doc_id,))
            db.execute("DELETE FROM docs WHERE id=?", (doc_id,))
            db.execute("DELETE FROM history WHERE id=?", (doc_id,))
            db.commit()
            return redirect('/', code=302)
        else:
            sidebar_list = get_current_list()
            return render_template('error/404.html', setting=get_setting('wiki'), sidebar_list=sidebar_list,
                                   nav={'document': False})

    # 파일 업로드
    @app.route('/upload/<path:doc_name>')
    def file_upload(doc_name):
        sidebar_list = get_current_list()
        return render_template('document/file_upload.html', setting=get_setting('wiki'), subject=doc_name, sidebar_list=sidebar_list, nav={'document': False})

    @app.route('/upload', methods=['post'])
    def upload():
        upload_folder = 'uploads/' + request.form['doc_name'] + '/'

        allowed_extensions = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3']
        picture_extensions = ['png', 'jpg', 'jpeg', 'gif']
        attached_extensions = ['txt', 'pdf', 'mp3']

        # 허용되는 확장자인지 검사함
        if 'file' not in request.files:
            flash('No file part')
            return 'errr'
        file = request.files['file']

        # 파일을 선택했는지 검사함
        if file.filename == '':
            flash('No selected file')
            return 'errrrr'

        # 해당 문서가 있는지 검사함
        db = database.get_db()
        if not db.execute('SELECT * FROM docs_list WHERE name=?', (request.form['doc_name'],)):
            return 'errr'

        if file and '.' in file.filename:
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            if file_ext in allowed_extensions:
                filename = file.filename
                filename = secure_filename(file.filename)

                origin_umask = os.umask(0)
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder, 0o777)
                os.umask(origin_umask)

                file.save(os.path.join(upload_folder, filename))

        return redirect(url_for('file_list', doc_name=request.form['doc_name']), code=302)

    @app.route('/files/<path:doc_name>')
    def file_list(doc_name):
        file_path = 'uploads/' + doc_name
        if os.path.exists(file_path):
            files = os.listdir(file_path)
        else:
            return 'No file'

        sidebar_list = get_current_list()
        return render_template('document/file_list.html', setting=get_setting('wiki'), subject=doc_name,
                               sidebar_list=sidebar_list, file_list=files, nav={'document': False})

    @app.route('/file/<path:file_name>')
    def show_file(file_name):
        return send_file('uploads/' + file_name)

    # 설정 관련 페이지
    @app.route('/setting/blog')
    def set_blog():
        sidebar_list = get_current_list()
        return render_template('admin/set_blog.html', setting=get_setting('wiki'), sidebar_list=sidebar_list, nav={'document': False})

    @app.route('/setting/blog/save', methods=['post'])
    def set_blog_save():
        sidebar_list = get_current_list()
        data = {"name": request.form['name'], "information": request.form['information'],
                "main": request.form['main'], "disqus_url": request.form['disqus_url'],
                "wiki_url": request.form['wiki_url']}
        wiki_config.save(data)
        return redirect(url_for('set_blog'), code=302)

    @app.route('/setting/user')
    def set_user():
        sidebar_list = get_current_list()
        db = database.get_db()
        user = db.execute("SELECT * FROM user WHERE id=?", (session['id'],)).fetchone()
        return render_template('admin/set_user.html', setting=get_setting('wiki'), sidebar_list=sidebar_list, user=user, nav={'document': False})

    @app.route('/setting/user/save', methods=['post'])
    def set_user_save():
        db = database.get_db()
        password = request.form['pw'].encode('utf8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(14))
        db.execute("UPDATE user SET name=?, password=? WHERE id=?", (request.form['name'], hashed_password, session['id']))
        db.commit()
        return redirect(url_for('set_user'), code=302)

    @app.route('/login')
    def login():
        sidebar_list = get_current_list()
        if 'id' in session:
            return render_template('error/404.html', setting=get_setting('wiki'), sidebar_list=sidebar_list,
                                   nav={'document': False})
        else:
            return render_template('admin/login.html', setting=get_setting('wiki'), sidebar_list=sidebar_list,
                                   nav={'document': False})

    @app.route('/login_session', methods=['post'])
    def login_session():
        db = database.get_db()
        password = request.form['pw'].encode('utf8')
        hashed_password = db.execute("SELECT password FROM user WHERE id = ?",(request.form['id'],)).fetchone()['password']
        if bcrypt.checkpw(password, hashed_password):
            session["id"] = request.form['id']
            return redirect('/', code=302)
        else:
            return error_page('login')

    @app.route('/logout')
    def logout():
        if 'id' in session:
            session.pop('id')
        return redirect('/', code=302)

    # 설치 관련 페이지
    @app.route('/setting/install')
    def install_page():
        if not get_setting('app')['install']:
            return render_template('admin/install.html')
        else:
            sidebar_list = get_current_list()
            return render_template('error/404.html', setting=get_setting('wiki'), sidebar_list=sidebar_list,
                                   nav={'document': False})

    @app.route('/install', methods=['post'])
    def install():
        if not get_setting('app')['install']:
            wiki_data = {"name": request.form['wiki_name'], "information": request.form['info_doc'],
                    "main": request.form['main_doc'], "disqus_url": request.form['disqus_url'],
                    "wiki_url": request.form['wiki_url']}
            app_data = {"install": True, "secret_key": app_config.load()['secret_key']}
            db = database.get_db()
            password = request.form['pw'].encode('utf8')
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(14))
            db.execute("INSERT INTO user VALUES(?, ?, ?, 0, datetime('now', 'localtime'))",
                       (request.form['id'], hashed_password, request.form['name']))
            db.commit()
            wiki_config.save(wiki_data)
            app_config.save(app_data)
            return redirect('/', code=302)
        else:
            sidebar_list = get_current_list()
            return render_template('error/404.html', setting=get_setting('wiki'), sidebar_list=sidebar_list,
                                   nav={'document': False})

    # 에러 관련 페이지
    @app.route('/error')
    def error_page(error):
        return render_template('error/error.html', error=error, setting=get_setting('wiki'), sidebar_list=get_current_list(), nav={'document': False})

    @app.errorhandler(500)
    @app.errorhandler(404)
    def page_not_found(e):
        sidebar_list = get_current_list()
        return render_template('error/404.html', setting=get_setting('wiki'), sidebar_list=sidebar_list, nav={'document': False})

    return app

