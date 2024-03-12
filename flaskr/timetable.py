from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session
from flask import flash
from werkzeug.exceptions import abort
from datetime import datetime
import re

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("timetable", __name__)

def notify():
    # flash("notice")
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    today = datetime.strptime(today_str, "%Y-%m-%d")
    

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT subject_name, deadline FROM assignment")
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
def index():
    notify()
    days_order = ["getu", "ka", "sui", "moku", "kin"]
    timetable_table = [[""] * 7 for _ in range(7)]
    if request.method == "POST":
        
        if request.form.get('action') is not None:
            action = request.form['action']
            pattern = re.compile(r"^(getu|ka|sui|moku|kin)_[1-9]\d*$")
            if pattern.match(action):
                db = get_db()
                cursor = db.cursor()
                is_subject = db.execute(
                "SELECT * FROM timetable WHERE time = ?", (action,)
                ).fetchone()
                
                if(is_subject):
                    subject = is_subject["subject_name"]
                    subject_data = db.execute(
                    "SELECT * FROM subject WHERE subject_name = ?", (subject ,)
                    ).fetchone()
                    assignments_data = db.execute(
                    "SELECT * FROM assignment WHERE subject_name = ?", (subject ,)
                    ).fetchone()
                    return render_template("timetable/subject_register.html", subject_data=subject_data, assignments_data=assignments_data)
                
                cursor = db.cursor()
                cursor.execute("SELECT subject_name FROM subject")
                subject_all = cursor.fetchall()
                db.close()
                session['time'] = action
                return render_template("timetable/subject_select.html", subject_all=subject_all)
        selected_subject = request.form.get('selected_subject')
        if selected_subject:
          
            """
            timeのデータを保存する必要がある
            """
            db = get_db()         
            time = session['time']
            
            db.execute("INSERT INTO timetable (time, subject_name) VALUES (?, ?)", 
                       (time, selected_subject)
                       )
            db.commit()
            return redirect(url_for("index"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT time, subject_name FROM timetable")
    timetable_data = cursor.fetchall()
    db.close()
    """
    [[getu_1, getu_2, ...],
    [ka_1, ka_2, ...],
    ]
    """
    
    if timetable_data is not None:      

        # timetableデータを行列に埋め込む
        for n in range(0, len(days_order)+1):
            for time, subject_name in timetable_data:
                for day_index, day in enumerate(days_order):
                    if f"{day}_{n}" in time:
                        timetable_table[day_index][n-1] = subject_name
        
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

       

    if timetable_data is None:
        timetable_table = [[""] * 7 for _ in range(7)]
    return render_template("timetable/index.html", days_order=days_order, timetable_data=timetable_table)


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
# @login_required
def subject_register():
    """Create a new post for the current user."""
    if request.method == "POST":
        if request.form.get('subject_name') is None:
            return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)

        action = request.form['action']
        subject_name = request.form['subject_name']
        teacher = request.form['teacher']
        classroom = request.form['classroom']
        contents = request.form['contents']
        deadline = request.form['deadline']

        if action == 'delete':
            """
            assignmentまたはsubjectにsubjectが存在するとき, 削除してindex.htmlに戻る.
            databaseにsubject, assignmentが存在しないとき, index.htmlに戻る.
            """
            db = get_db()
            subject_data = db.execute(
            "SELECT * FROM subject WHERE subject_name = ?", (subject_name,)
            ).fetchone()
            assignment_data = db.execute(
            "SELECT * FROM assignment WHERE subject_name = ?", (subject_name,)
            ).fetchone()
            if subject_data["subject_name"] is subject_name:
                db.execute(
                "DELETE * FROM subject WHERE subject_name = ?", (subject_name,)
                 ).fetchone()
                db.commit()
            if assignment_data["subject_name"] is subject_name:
                db.execute(
                "DELETE * FROM assignment  WHERE subject_name = ?", (subject_name,)
                 ).fetchone()
                db.commit()
            return redirect(url_for("timetable.index"))
        elif action == 'save':
            """
            databaseにsubjectが存在するとき, 更新を行い, index.htmlに戻る.
            databaseにsubjectが存在しないとき, 新たにsubjectを登録してindex.htmlに戻る.
            """
            print("save")
            if not (teacher and subject_name and classroom):
                return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)
            db = get_db()
            db.execute("INSERT INTO subject (subject_name, teacher_name, classroom) VALUES (?, ?, ?)", 
                       (subject_name, teacher, classroom)
                       )
            if (contents and deadline):
                db.execute("INSERT INTO assignment (subject_name, contents, deadline) VALUES(?, ?, ?)",
                           (subject_name, contents, deadline)
                           )
            db.commit()
            return redirect(url_for("index"))
        elif action == 'timetable':
            return redirect(url_for("timetable.index"))
        else:
            return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)
    return render_template("timetable/subject_register.html", subject_data=None, assignments_data=None)


