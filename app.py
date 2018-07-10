import os
import bcrypt
import re
from base64 import b64encode

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
            app_config.save({"install": False, "secret_key": b64encode(os.urandom(64)).decode('utf8')})
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

        new_db = db.execute("SELECT name FROM doc_list ORDER BY datetime(date) DESC LIMIT 10")
        if new_db is not None:
            new_db = new_db.fetchall()
            for row in new_db:
                for element in row:
                    lists['new'].append(element)
        edit_db = db.execute("SELECT name FROM (history join doc_list using (id)) as t ORDER BY datetime(t.date) DESC LIMIT 10")
        if edit_db is not None:
            edit_db = edit_db.fetchall()
            for row in edit_db:
                for element in row:
                    lists['edit'].append(element)

        return lists

    def get_setting(file): # 설정 파일 불러옴
        return tools.Config('config/' + file).load()

    def is_doc_name(name): # 문서의 이름이 올바른지 검사함
        if re.search('[/ ]{2,}', name):
            return False
        if re.search('^(?! ).+(?<!/| )$', name):
            return True
        return False

    def is_doc(name): # 문서가 존재하는지 검사함
        db = database.get_db()
        if db.execute('SELECT * FROM doc_list WHERE name=?', (name,)) is not None:
            return True
        else:
            return False

    # 문서 관련 페이지
    # 문서 보기
    @app.route('/')
    def index():
        if get_setting('app')['install']:
            return redirect('/doc/{0}'.format(get_setting('wiki')['main']), code=302)
        else:
            return redirect('/setting/install', code=302)

    @app.route('/doc/<path:doc_name>')
    def doc_request(doc_name):
        db = database.get_db()

        text = db.execute("SELECT html_data FROM doc join doc_list using (id) WHERE name = ?", (doc_name,)).fetchone()

        if text is None:
            return render_template('document/not_such_doc.html', subject=doc_name, setting=get_setting('wiki'),
                                   sidebar_list=get_current_list(), nav={'document': False})
        else:
            text = text['html_data']
            return render_template('document/view.html', subject=doc_name, text=text, setting=get_setting('wiki'),
                                   sidebar_list=get_current_list(), nav={'document': True})

    # 문서 리스트 보기
    @app.route('/docs', methods=['get'])
    def doc_list():
        method_display = {"recent_write": "최근에 작성한 순서", "recent_edit": "최근에 수정한 순서",
                          "가": "ㄱ/ㄲ", "나": "ㄴ", "다": "ㄷ", "라": "ㄹ", "마": "ㅁ", "바": "ㅂ/ㅃ",
                          "사": "ㅅ/ㅆ", "아": "ㅇ", "자": "ㅈ/ㅉ", "차": "ㅊ", "카": "ㅋ", "타": "ㅌ",
                          "파": "ㅍ", "하": "ㅎ", "a": "A", "b": "B", "c": "C", "d":"D", "e": "E",
                          "f": "F", "g": "G", "h": "H", "i": "I", "j": "J", "k": "K", "l": "L",
                          "m": "M", "n": "N", "o": "O", "p": "P", "q": "Q", "r": "R", "s": "S",
                          "t": "T", "u": "U", "v": "V", "w": "W", "x": "X", "y": "Y", "z": "Z",
                          "special": "특수문자"}
        hanguel = ['가','나','다','라','마','바','사','아','자','타','카','타','파','하', '힣']
        if not request.args.get('method'):
            method = 'recent_write'
        else:
            method = request.args.get('method')
        if not request.args.get('page_number'):
            page_number = 1
        else:
            page_number = int(request.args.get('page_number'))
        limit_point = (page_number - 1) * 30
        db = database.get_db()
        if method == 'recent_write':
            count = db.execute("SELECT count(*) as count FROM doc_list").fetchone()['count']
            list_data = db.execute("SELECT name FROM doc_list ORDER BY datetime(date) DESC LIMIT ? OFFSET ?", (30, limit_point))
        elif method == 'recent_edit':
            count = db.execute("SELECT count(*) as count FROM history").fetchone()['count']
            list_data = db.execute("SELECT name FROM (history join doc_list using (id)) as t ORDER BY datetime(t.date) DESC LIMIT ? OFFSET ?", (30, limit_point))
        elif method in hanguel: # 한글 일 경우
            start = hanguel.index(method)
            end = start + 1
            if method == '하': # 마지막일 경우
                count = db.execute("SELECT count(*) as count FROM doc_list WHERE name >= ? and name <= ?",
                                   (hanguel[start], hanguel[end])).fetchone()['count']
                list_data = db.execute("SELECT name FROM doc_list WHERE name >= ? and name <= ? LIMIT ? OFFSET ?",
                                       (hanguel[start], hanguel[end], 30, limit_point))
            else:
                count = list_data = db.execute("SELECT count(*) as count FROM doc_list WHERE name >= ? and name < ?",
                                               (hanguel[start], hanguel[end])).fetchone()['count']
                list_data = db.execute("SELECT name FROM doc_list WHERE name >= ? and name < ? LIMIT ? OFFSET ?",
                                       (hanguel[start], hanguel[end], 30, limit_point))
        else: #영문 또는 기타 문자임
            if method == 'special':
                count =\
                    db.execute("SELECT count(*) as count FROM doc_list WHERE not (name >= '가' and name <= '힣') and not (LOWER(name) >= 'a' and LOWER(name) <= 'z')").fetchone()['count']
                list_data =\
                    db.execute("SELECT name FROM doc_list WHERE not (name >= '가' and name <= '힣') and not (LOWER(name) >= 'a' and LOWER(name) <= 'z') LIMIT ? OFFSET ?", (30, limit_point))
            else:
                statement = method + '%'
                count = db.execute("SELECT count(*) as count FROM doc_list WHERE LOWER(name) LIKE ?", (statement,)).fetchone()['count']
                list_data = db.execute("SELECT name FROM doc_list WHERE LOWER(name) LIKE ? LIMIT ? OFFSET ?", (statement, 30, limit_point))

        page_numbers = []
        if count % 30 == 0:
            last_page = int(count / 30)
        else:
            last_page = int(count / 30) + 1
        for number in range(-4, 4):
            if 0 < page_number + number <= last_page:
                page_numbers.append(page_number + number)

        if list_data is not None:
            list_data = list_data.fetchall()

        return render_template('document/doc_list.html', setting=get_setting('wiki'), sidebar_list=get_current_list(),
                               nav={'document': False}, method=method, method_print=method_display[method],
                               list=list_data, page_numbers=page_numbers, page_number=page_number, last_page=last_page)

    # 문서 검색 기능
    @app.route('/search/<path:text>')
    def doc_search(text):
        search_result = {"same_name": False, "included_in_name": [], "included_in_text": {}}
        # 문서 제목과 정확히 일치
        db = database.get_db()
        result = db.execute("SELECT name FROM doc_list WHERE name = ?", (text,)).fetchone()
        if result is not None:
            search_result["same_name"] = True
        # 문서 제목에 검색어가 포함됨
        query_items = text.split(" ", maxsplit=5)
        for item in query_items:
            results = \
                db.execute("SELECT name FROM doc_list WHERE name like ?", ("%" + item + "%",)).fetchall()
            if results is not None:
                for result in results:
                    if result['name'] not in search_result["included_in_name"]:
                        search_result["included_in_name"].append(result['name'])
        # 문서 내용에 검색어가 포함됨
        search_text = text.replace(" ", "|")
        for item in query_items:
            results = \
                db.execute(
                    "SELECT name, markdown_data FROM doc_list join doc using (id) WHERE markdown_data like ?",
                    ("%" + item + "%",)).fetchall()
            if results is not None:
                for result in results:
                    if result['name'] not in search_result["included_in_text"]:
                        search_result["included_in_text"][result['name']] = ""
                        re_data = re.findall('(.{{0,50}}({0}).{{0,50}})+'.format(search_text), result['markdown_data'])
                        for data in re_data:
                            search_result["included_in_text"][result['name']] += " " + data[0]
        return render_template('document/doc_search.html', subject=text, setting=get_setting('wiki'),
                               sidebar_list=get_current_list(), nav={'document': False}, result=search_result)

    # 문서 부가 기능
    @app.route('/history/<path:doc_name>')
    def doc_history(doc_name):
        db = database.get_db()
        doc_id = db.execute("SELECT id FROM doc_list WHERE name=?", (doc_name,)).fetchone()

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
        doc_id = db.execute("SELECT id FROM doc_list WHERE name=?", (doc_name,)).fetchone()

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
        doc_name = db.execute("SELECT name FROM doc_list ORDER BY RANDOM() LIMIT 1").fetchone()
        if doc_name:
            doc_name = doc_name['name']
            return redirect("/doc/{0}".format(doc_name), code=302)
        else:
            sidebar_list = get_current_list()
            return render_template('error/404.html', setting=get_setting('wiki'), sidebar_list=sidebar_list,
                                   nav={'document': False})

    # 문서 쓰기
    @app.route('/write/<path:doc_name>')
    def doc_write(doc_name):
        if not is_doc_name(doc_name):
            return error_page('incorrect_doc')
        if 'id' not in session:
            return error_page('not_login')

        sidebar_list = get_current_list()

        db = database.get_db()
        doc_id = db.execute("SELECT id FROM doc_list WHERE name = ?", (doc_name,)).fetchone()
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
        if not is_doc_name(doc_name):
            return error_page('incorrect_doc')
        if 'id' not in session:
            return error_page('not_login')

        db = database.get_db()
        doc_id = db.execute("SELECT id FROM doc_list WHERE name=?", (doc_name,)).fetchone()
        if doc_id is not None:
            doc_id = doc_id['id']
            is_edit = True
        else:
            is_edit = False

        markdown_text = request.form['mytext']
        translator = translate.Translator(markdown_text)
        html_text = translator.compile()

        if not is_edit:
            id = db.execute("SELECT max(id) FROM doc_list").fetchone()['max(id)']
            if id is None:
                id = 0
            id += 1
            doc_list_list = (id, doc_name)
            doc_list = (id, html_text, markdown_text)
            history_list = (id, 1, markdown_text)
            db.execute("INSERT into doc_list VALUES(?, ?, datetime('now', 'localtime'))", doc_list_list)
            db.execute("INSERT into doc VALUES(?, ?, ?)", doc_list)
            db.execute("INSERT into history VALUES(?, ?, ?, datetime('now', 'localtime'))", history_list)
            db.commit()
            return redirect("/doc/{0}".format(doc_name), code=302)
        else:
            history_version = db.execute("SELECT max(version) FROM history where id = ?",
                                         (doc_id,)).fetchone()['max(version)'] + 1
            history_list = (doc_id, history_version, markdown_text)
            db.execute("INSERT into history VALUES(?, ?, ?, datetime('now', 'localtime'))", history_list)
            db.execute("UPDATE doc SET html_data = ? and markdown_data = ? WHERE id = ?", (html_text, markdown_text, doc_id))
            db.commit()
            return redirect("/doc/{0}".format(doc_name), code=302)

    # 문서 지우기
    @app.route('/remove/<path:doc_name>')
    def doc_remove(doc_name):
        if 'id' in session:
            db = database.get_db()
            # 으악... 캐스트 캐이드를 디비 열 때마다 켜줘야 한다는데, 파이썬으로는 조작도 안되고.. 허;;
            # 일일이 지우는 수 밖에;;
            doc_id = db.execute("SELECT id FROM doc_list WHERE name=?", (doc_name,)).fetchone()['id']
            db.execute("DELETE FROM doc_list WHERE id=?", (doc_id,))
            db.execute("DELETE FROM doc WHERE id=?", (doc_id,))
            db.execute("DELETE FROM history WHERE id=?", (doc_id,))
            db.commit()
            return redirect('/', code=302)
        else:
            return error_page('not_login')

    # 파일 업로드
    @app.route('/upload/<path:doc_name>')
    def file_upload(doc_name):
        if not is_doc(doc_name):
            return error_page('not_such_doc')
        if 'id' not in session:
            return error_page('not_login')

        sidebar_list = get_current_list()
        return render_template('document/file_upload.html', setting=get_setting('wiki'), subject=doc_name, sidebar_list=sidebar_list, nav={'document': False})

    @app.route('/upload', methods=['post'])
    def upload():
        if not is_doc(request.form['doc_name']):
            return error_page('not_such_doc')
        if 'id' not in session:
            return error_page('not_login')

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
        if not db.execute('SELECT * FROM doc_list WHERE name=?', (request.form['doc_name'],)):
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
        if 'id' not in session:
            return error_page('not_login')
        sidebar_list = get_current_list()
        return render_template('admin/set_blog.html', setting=get_setting('wiki'), sidebar_list=sidebar_list, nav={'document': False})

    @app.route('/setting/blog/save', methods=['post'])
    def set_blog_save():
        if 'id' not in session:
            return error_page('not_login')
        sidebar_list = get_current_list()
        data = {"name": request.form['name'], "information": request.form['information'],
                "main": request.form['main'], "disqus_url": request.form['disqus_url'],
                "wiki_url": request.form['wiki_url']}
        wiki_config.save(data)
        return redirect(url_for('set_blog'), code=302)

    @app.route('/setting/user')
    def set_user():
        if 'id' not in session:
            return error_page('not_login')
        sidebar_list = get_current_list()
        db = database.get_db()
        user = db.execute("SELECT * FROM user WHERE id=?", (session['id'],)).fetchone()
        return render_template('admin/set_user.html', setting=get_setting('wiki'), sidebar_list=sidebar_list, user=user, nav={'document': False})

    @app.route('/setting/user/save', methods=['post'])
    def set_user_save():
        if 'id' not in session:
            return error_page('not_login')
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
        hashed_password = db.execute("SELECT password FROM user WHERE id = ?",(request.form['id'],)).fetchone()

        if hashed_password is not None:
            hashed_password = hashed_password['password']
        else:
            return error_page('login')

        if bcrypt.checkpw(password, hashed_password):
            session.permanent = False
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
        return render_template('error/error.html', error=error, setting=get_setting('wiki'),
                               sidebar_list=get_current_list(), nav={'document': False})

    @app.errorhandler(500)
    @app.errorhandler(404)
    def page_not_found(e):
        sidebar_list = get_current_list()
        return render_template('error/404.html', setting=get_setting('wiki'),
                               sidebar_list=sidebar_list, nav={'document': False})

    return app

