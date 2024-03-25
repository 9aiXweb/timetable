from flask import Blueprint, flash, g, redirect \
, render_template, request, url_for, session, flash
from werkzeug.exceptions import abort
from datetime import datetime
import re

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("timetable", __name__)


def notify():
    today = datetime.now()
    today = today.strftime("%Y-%m-%d")
    # today_str = today.strftime("%Y-%m-%d")
    # today = datetime.strptime(today_str, "%Y-%m-%d")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT subject_name, deadline FROM assignment WHERE user_id = ?", (session["user_id"],))
    deadline_data = cursor.fetchall()
    
    for subject_name, deadline in deadline_data:
        deadline = datetime.strptime(deadline, "%Y-%m-%d")
        #deadline_num = deadline.split("-")
        date_difference = deadline - today
        if(deadline == today):
            flash(f"{subject_name}は提出期限です")
        elif(date_difference.days <= 3):
            flash(f"{subject_name}は{deadline}に提出期限です")



@bp.route("/", methods=("GET", "POST"))
@login_required
def index():
    delete_checked = False
    dayoftheweek = ["月", "火", "水", "木", "金", "土", "日"]

    notify()
    days_order = ["getu", "ka", "sui", "moku", "kin", "do", "niti"]
  #現在表示しているtimetableを取得
    if session.get("table_id") is not None:
        
        timetable_id = session["table_id"]

    else:
        db = get_db()
        cursor = db.cursor()
            # 最小のtable_idを取得するクエリを実行
        cursor.execute("SELECT MIN(table_id) FROM timetable_select WHERE user_id = ?", (session["user_id"],))
        
        # 結果を取得
        min_table_id = cursor.fetchone()[0]

        
        session["table_id"] = min_table_id
        timetable_id = session["table_id"]


        if min_table_id is None:
            return render_template("timetable/timetable_register.html")
   
    
    if request.method == "POST":
        if request.form.get('select_delete') is not None:
            delete_checked = True
        #チェックボックスによる教科の削除
        if request.form.get('subject_delete') is not None:
            
            check_list = []
            check_list = request.form.getlist('checkbox')
   
            if check_list:
    
                
                db = get_db()
             
                for subject in check_list:
                    
                    db.execute(
                    "DELETE FROM timetable WHERE time = ? AND table_id = ? AND table_id = ?", (subject, timetable_id, session["user_id"], )
                    ).fetchone()
                db.commit()
            delete_checked = False

            
        
        if request.form.get('action') is not None:
            action = request.form['action']
            pattern = re.compile(r"^(getu|ka|sui|moku|kin|do|niti)_[1-9]\d*$")
            if pattern.match(action):
                db = get_db()
                cursor = db.cursor()
                is_subject = db.execute(
                "SELECT * FROM timetable WHERE time = ? AND table_id = ? AND user_id = ? ", (action, int(timetable_id) , session["user_id"],)
                ).fetchone()

                #時間割に登録された教科を編集するための処理
                if(is_subject):
                    subject = is_subject["subject_name"]
                    subject_data = db.execute(
                    "SELECT * FROM subject WHERE subject_name = ? AND user_id = ? ", (subject, session["user_id"],)
                    ).fetchone()
                    assignments_data = db.execute(
                    "SELECT * FROM assignment WHERE subject_name = ? AND user_id = ? ", (subject , session["user_id"],)
                    ).fetchone()
                    return render_template("timetable/subject_register.html", subject_data=subject_data, assignments_data=assignments_data)
                
                cursor = db.cursor()
                cursor.execute("SELECT subject_name FROM subject WHERE user_id = ?", (session["user_id"],))
                subject_all = cursor.fetchall()
                db.close()
                session['time'] = action
                return render_template("timetable/subject_select.html", subject_all=subject_all)
        

        selected_subject = request.form.get('selected_subject')
        if selected_subject:
            
          
            """
            timeのデータを保存する必要がある
            1. subjectデータベースを取得.
            2. 選択された教科の色を取得.
            3. timetableでデータベースに登録する.

            html側でやること
            変数timetable_dataのcolorに応じてbackgroundcolorを変更.(style="background-color: {{}};")
            """
            db = get_db()         
            time = session['time']
            
            subject_data = db.execute("SELECT * FROM subject WHERE subject_name = ? AND user_id = ?", 
                       (selected_subject, session["user_id"])
                       ).fetchone()
            color = subject_data["color"]
            
            # if color is None:
            #     color = "#FFFFFF"

            db.execute("INSERT INTO timetable (time, subject_name, color, table_id, user_id) VALUES (?, ?, ?, ?, ?)", 
                       (time, selected_subject, color, timetable_id, session["user_id"],)
                       ).fetchone()
            db.commit()
            return redirect(url_for("index"))

   
        
    db = get_db()
    # cursor = db.cursor()
    # cursor.execute("SELECT time, subject_name FROM timetable WHERE table_id = timetable_id")
    # cursor.execute("SELECT time, subject_name, table_id  FROM timetable")
    # timetable_data = cursor.fetchall()
    timetable_select = db.execute(
            "SELECT vertical, horizontal, table_name FROM timetable_select WHERE table_id = ? AND user_id = ?", (timetable_id, session["user_id"],)
            ).fetchone()
    timetable_data = db.execute(
            "SELECT subject_name, time, color FROM timetable WHERE table_id = ? AND user_id = ?", (timetable_id, session["user_id"],)
            ).fetchall()   
    
    """
    [[getu_1, getu_2, ...],
    [ka_1, ka_2, ...],
    ]
    """

    vertical_length = int(timetable_select["vertical"])
    horizontal_length = int(timetable_select["horizontal"])


    if (vertical_length and horizontal_length) is None:
        vertical_length  = 7
        horizontal_length = 7  
        timetable_table = [[""] * 7 for _ in range(7)]  
        
    elif timetable_select is not None:
       
       
        if  timetable_data is not None and len(timetable_data) > 0:

            timetable_table = [[""] * vertical_length for _ in range(horizontal_length)]  
            
            

            # # # timetableデータを行列に埋め込む
            for n in range(1, vertical_length+1):
                for subject_name, time, color in timetable_data:
                    for day_index, day in enumerate(days_order):#曜日
                        if f"{day}_{n}" in time:
                            timetable_table[day_index][n-1] = subject_name
                            # timetable_table_color[day_index][n-1] = color
        else:
            
            timetable_table = [[""] * vertical_length for _ in range(horizontal_length)]  
            
            
        # else:
        #     flash("2")
        #     timetable_table = [[""] * 7 for _ in range(7)]  

       
    else:
        timetable_table = [[""] * 7 for _ in range(7)]
    #return render_template("timetable/index.html", days_order=None, timetable_data=None, tables=None, table_name=None)
    """ 
        print("--------------------------------------------------------------")
        print(timetable_table) 
        print("--------------------------------------------------------------")
        print(days_order)
        print("--------------------------------------------------------------")

        => OUTPUT
        --------------------------------------------------------------
        [['database', '', '', '', '', '', ''], ['', '', '', '', '', '', ''], 
        ['', '', 'AI', '', '', '', ''], ['', '', '', '', '', '', ''], 
        ['', '', '', '', '', '', ''], ['', '', '', '', '', '', ''], 
        ['', '', '', '', '', '', '']]
        --------------------------------------------------------------
        ['getu', 'ka', 'sui', 'moku', 'kin']
        --------------------------------------------------------------
        """

    db = get_db()
    timetables = db.execute(
    "SELECT table_id, table_name FROM timetable_select WHERE user_id = ?",
    (session["user_id"], )
    ).fetchall()
    
    subject_color = db.execute(
        "SELECT subject_name, color FROM subject WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    

    return render_template("timetable/index.html", days_order=days_order[:horizontal_length], 
                           timetable_data=timetable_table, tables=timetables, subject_color = subject_color,
                           table_name=timetable_select["table_name"], vertical_length=vertical_length,
                           dayoftheweek=dayoftheweek[:horizontal_length], delete_checked=delete_checked)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))

"""
databaseのsubjectを更新する.
"""
@bp.route("/subject", methods=("GET", "POST"))
@login_required
def subject_register():
    """Create a new post for the current user."""
    if request.method == "POST":
        if (request.form.get('subject_name') and request.form.get('color')) is None:
        
            return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)

        action = request.form['action']
        subject_name = request.form['subject_name']
        teacher = request.form['teacher']
        classroom = request.form['classroom']
        contents = request.form['contents']
        deadline = request.form['deadline']
        color = request.form['color']


        db = get_db()
        subject_data = db.execute(
            "SELECT * FROM subject WHERE subject_name = ? AND user_id = ? ", (subject_name, session["user_id"], )
            ).fetchone()
        assignment_data = db.execute(
            "SELECT * FROM assignment WHERE subject_name = ? AND user_id = ? ", (subject_name, session["user_id"], )
            ).fetchone()
        timetable_data = db.execute(
            "SELECT * FROM timetable WHERE subject_name = ? AND user_id = ? ", (subject_name, session["user_id"], )
            ).fetchone()

        if action == 'delete':
            """
            assignmentまたはsubjectにsubjectが存在するとき, 削除してindex.htmlに戻る.
            databaseにsubject, assignmentが存在しないとき, index.htmlに戻る.
            """
            if subject_data is None:
                return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)
            elif subject_data["subject_name"] == subject_name:
                db.execute(
                "DELETE FROM subject WHERE subject_name = ? AND user_id = ? ", (subject_name, session["user_id"], )
                 ).fetchone()
                db.commit()

            if timetable_data["subject_name"] == subject_name:
                db.execute("DELETE FROM timetable WHERE subject_name = ? AND user_id = ?", (subject_name, session["user_id"], )).fetchone()
                db.commit()

            if assignment_data is None:
                return redirect(url_for("timetable.index"))
            elif assignment_data["subject_name"] == subject_name:
                db.execute(
                "DELETE FROM assignment  WHERE subject_name = ? AND user_id = ? ", (subject_name, session["user_id"], )
                 ).fetchone()
                db.commit()
            
            return redirect(url_for("timetable.index"))
        elif action == 'save':
            """
            databaseにsubjectが存在するとき, 更新を行い, index.htmlに戻る.
            databaseにsubjectが存在しないとき, 新たにsubjectを登録してindex.htmlに戻る.
            """
            print("save")
            
            #入力されて以内場合
            # if not (teacher and subject_name and classroom):
            #     return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)

            #教科の編集
            if subject_data is not None:
                db.execute("UPDATE subject SET teacher_name = ?, classroom = ?, color = ? WHERE subject_name = ? AND user_id = ?",
                            (teacher, classroom, color, subject_name, session["user_id"])
                            )
            #elif(subject_name and teacher and classroom and color):
            elif(subject_name and color):
                db.execute("INSERT INTO subject (subject_name, teacher_name, classroom, user_id, color) VALUES (?, ?, ?, ?, ?)", 
                        (subject_name, teacher, classroom, session["user_id"], color)
                        )
            else:

                db.execute("INSERT INTO subject (subject_name, user_id) VALUES (?, ?)", 
                (subject_name, session["user_id"], )
                )

            #課題の編集
            if (contents and deadline) and (assignment_data is not None):
                db.execute("UPDATE assignment SET contents = ? , deadline = ? WHERE subject_name = ? AND user_id = ?",
                            (contents, deadline, subject_name, session["user_id"] )
                            )
            elif(contents and deadline):
                db.execute("INSERT INTO assignment (subject_name, contents, deadline, user_id) VALUES(?, ?, ?, ?)",
                            (subject_name, contents, deadline, session["user_id"])
                            )
            db.commit()
            return redirect(url_for("index"))
        elif action == 'timetable':
            return redirect(url_for("timetable.index"))
        else:
            return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)
    return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)


@bp.route("/table", methods=("GET", "POST"))
@login_required
def timetable_register():
    """Create a new post for the current user."""
    if request.method == "POST":
        if request.form.get('table_name')  is None:
            return render_template("timetable/timetable_register.html")

        action = request.form["action"]
        table_name = request.form['table_name']
        vertical = request.form['vertical']
        horizontal = request.form['horizontal']

        if action == 'delete':
            """
            assignmentまたはsubjectにsubjectが存在するとき, 削除してindex.htmlに戻る.
            databaseにsubject, assignmentが存在しないとき, index.htmlに戻る.
            """
            db = get_db()
            table_data = db.execute(
            "SELECT * FROM timetable_select WHERE table_name = ? AND user_id = ?", (table_name, session["user_id"], )
            ).fetchone()


            if table_data["table_name"] == table_name:
               
                db.execute(
                "DELETE FROM timetable_select WHERE table_name = ? AND user_id = ?", (table_name, session["user_id"], )
                 ).fetchone()
                db.commit()
                db.execute(
                "DELETE  FROM timetable WHERE table_id = ? AND user_id = ?", (table_data["table_id"], session["user_id"], )
                 ).fetchone()
                db.commit()

                if table_data["table_id"] == session["table_id"]:
                    
                    session["table_id"] = None

            return redirect(url_for("timetable.index"))
        elif action == 'save':
            """
            databaseにsubjectが存在するとき, 更新を行い, index.htmlに戻る.
            databaseにsubjectが存在しないとき, 新たにsubjectを登録してindex.htmlに戻る.
            """
            
            if not (table_name and vertical and horizontal):
                return render_template("timetable/timetable_register.html")
            elif not (1 <= int(horizontal) and int(horizontal)<= 7):
                return render_template("timetable/timetable_register.html")
            db = get_db()
            db.execute("INSERT INTO timetable_select (table_name, vertical, horizontal, user_id) VALUES (?, ?, ?, ?)", 
                       (table_name , int(vertical) , int(horizontal), session["user_id"])
                       )

            db.commit()

            
            return redirect(url_for("index"))

        else:
            
            return render_template("timetable/timetable_register.html")
    return render_template("timetable/timetable_register.html")

@bp.route("/select_table", methods=("POST",))
@login_required
def select_table():
    if not request.form.get("table_id"):
        return redirect("/")
    action = request.form["action"]
    table_id = int(request.form["table_id"])
    
    if action == "select":
        print("select timetable")
        session["table_id"] = table_id
        return redirect("/")
    elif action == "delete":
        "databaseにtimetableが存在するとき選択したtimetableを削除する"
        db = get_db()
        timetable_select_data = db.execute(
            "SELECT * FROM timetable_select WHERE table_id = ? AND user_id = ?", (table_id, session["user_id"])
            ).fetchone()
        if timetable_select_data is not None and len(timetable_select_data)>0:
            db.execute("DELETE FROM timetable WHERE table_id = ? AND user_id = ?", (table_id, session["user_id"])).fetchone()
            db.commit()
            db.execute("DELETE FROM timetable_select WHERE table_id = ? AND user_id = ?", (table_id, session["user_id"])).fetchone()
            db.commit()

        #現在表示しているtableを削除した場合
        if session["table_id"] == table_id:
            session["table_id"] = None
        return redirect("/")
        
  