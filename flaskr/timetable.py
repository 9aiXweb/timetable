from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("timetable", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("timetable/index.html")


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
            return render_template("timetable/subject_register.html")

        action = request.form['action']
        subject_name = request.form['subject_name']
        teacher = request.form['teacher']
        classroom = request.form['classroom']

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
            if not (teacher and subject_name and classroom):
                return render_template("timetable/subject_register.html")
            db = get_db()
            db.execute(
                "INSERT subject SET teacher_name = ?, subject_name = ?, classroom = ?", (teacher, subject_name, classroom)
            )
            db.commit()
            return redirect(url_for("timetable.index"))
        elif action == 'assignment':
            """
            assignment_register.htmlへ移動する.
            """
            return render_template("timetable/assignment_register.html")
        elif action == 'timetable':
            return redirect(url_for("timetable.index"))
        else:
            return render_template("timetable/subject_register.html")
    return render_template("timetable/subject_register.html")