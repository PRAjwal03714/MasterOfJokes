from flask import Blueprint
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import flash
from .db import get_db
from flask import session
from werkzeug.exceptions import abort

bp = Blueprint("jokes", __name__, url_prefix="/jokes")
#edited this from blog.py from Flaskr tutorial and changed to jokes.py
@bp.route("/")
def index():
    if g.user is None:
        return redirect(url_for("auth.login"))
    
    db = get_db()
    jokes = db.execute(
        "SELECT j.id, j.title, COALESCE(AVG(r.rating), 0) AS avg_rating "
        "FROM joke j LEFT JOIN joke_rating r ON j.id = r.joke_id "
        "WHERE j.author_id = ? GROUP BY j.id",
        (g.user["id"],)
    ).fetchall()
    
    return render_template("jokes/my_jokes.html", jokes=jokes)

@bp.route("/leave", methods=("GET", "POST"))
def leave_a_joke():
    """Create a new joke for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        #Ensure title is does not exceed 10 words
        if len(title.split()) > 10:
            error = "Title should not exceed 10 words"
        
        #Check for duplicate title
        db = get_db()
        if db.execute("SELECT id FROM joke WHERE title = ? AND author_id = ?", (title, g.user["id"])).fetchone() is not None:
            error = f"Joke {title} is already taken."
        
        if error is None:
            db.execute(
                "INSERT INTO joke (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db.execute("UPDATE user SET joke_balance = joke_balance + 1 WHERE id = ?", (g.user["id"],))
            db.commit()
            return redirect(url_for("jokes.my_jokes"))
        
        flash(error)

    return render_template("jokes/leave_a_joke.html")

@bp.route("/my_jokes")
def my_jokes():
    db = get_db()
    jokes = db.execute(
        "SELECT j.id, j.title, COALESCE(AVG(r.rating), 0) AS avg_rating "
        "FROM joke j LEFT JOIN joke_rating r ON j.id = r.joke_id "
        "WHERE j.author_id = ? GROUP BY j.id", (g.user["id"],)
    ).fetchall()

    return render_template("jokes/my_jokes.html", jokes=jokes)

@bp.route("/take_joke")
def take_joke():
    db = get_db()

    # Fetch jokes not authored by the user and not yet taken by them
    jokes = db.execute(
        "SELECT j.id, j.title, u.nickname AS author, COALESCE(AVG(r.rating), 0) AS avg_rating "
        "FROM joke j "
        "JOIN user u ON j.author_id = u.id "
        "LEFT JOIN joke_rating r ON j.id = r.joke_id "
        "WHERE j.author_id != ? AND j.id NOT IN (SELECT joke_id FROM user_joke WHERE user_id = ?) "
        "GROUP BY j.id",
        (g.user["id"], g.user["id"])
    ).fetchall()

    # Render the available jokes for the user to take
    return render_template("jokes/take_joke.html", jokes=jokes)

@bp.route("/take_joke/<int:joke_id>", methods=("POST",))
def take_joke_action(joke_id):
    db = get_db()

    # Check if the user already took this joke
    taken = db.execute(
        "SELECT 1 FROM user_joke WHERE user_id = ? AND joke_id = ?", 
        (g.user["id"], joke_id)
    ).fetchone()

    if taken:
        flash("You have already taken this joke.")
        return redirect(url_for("jokes.take_joke"))

    # Ensure the user has enough joke balance
    if g.user["joke_balance"] > 0:
        # Decrement joke balance and mark the joke as taken
        db.execute("UPDATE user SET joke_balance = joke_balance - 1 WHERE id = ?", (g.user["id"],))
        db.execute("INSERT INTO user_joke (user_id, joke_id) VALUES (?, ?)", (g.user["id"], joke_id))
        db.commit()
    else:
        flash("You need to leave a joke to increase your joke balance before you can take a joke.")
        return redirect(url_for("jokes.my_jokes"))

    # Redirect to view the joke after taking it
    return redirect(url_for("jokes.view_joke", joke_id=joke_id))

@bp.route("/view/<int:joke_id>", methods=("GET", "POST"))
def view_joke(joke_id):
    db = get_db()
    joke = db.execute(
        "SELECT j.id, j.title, j.body, j.author_id, u.nickname AS author, COALESCE(AVG(r.rating), 0) AS avg_rating, j.created "
        "FROM joke j LEFT JOIN joke_rating r ON j.id = r.joke_id "
        "JOIN user u ON j.author_id = u.id WHERE j.id = ? GROUP BY j.id", (joke_id,)
    ).fetchone()

    if joke is None:
        abort(404, f"Joke id {joke_id} doesn't exist.")

    if request.method == "POST":
        if g.user["id"] == joke["author_id"]:
            return redirect(url_for("jokes.update_joke", joke_id=joke_id))

        rating = int(request.form["rating"])
        db.execute(
            "INSERT INTO joke_rating (joke_id, user_id, rating) VALUES (?, ?, ?)",
            (joke_id, g.user["id"], rating),
        )
        db.commit()
        return redirect(url_for("jokes.view_joke", joke_id=joke_id))

    return render_template("jokes/view_joke.html", joke=joke)

@bp.route("/update/<int:joke_id>", methods=("GET", "POST"))
def update_joke(joke_id):
    joke = get_joke(joke_id)

    if joke["author_id"] != g.user["id"]:
        abort(403)

    if request.method == "POST":
        body = request.form["body"]
        db = get_db()
        db.execute("UPDATE joke SET body = ? WHERE id = ?", (body, joke_id))
        db.commit()
        return redirect(url_for("jokes.view_joke", joke_id=joke_id))

    return render_template("jokes/update_joke.html", joke=joke)

@bp.route("/delete/<int:joke_id>", methods=("POST",))
def delete_joke(joke_id):
    joke = get_joke(joke_id)

    if joke["author_id"] != g.user["id"]:
        abort(403)

    db = get_db()
    db.execute("DELETE FROM joke WHERE id = ?", (joke_id,))
    db.commit()
    return redirect(url_for("jokes.my_jokes"))

def get_joke(joke_id):
    joke = get_db().execute(
        "SELECT j.id, j.body, j.author_id "
        "FROM joke j WHERE j.id = ?", (joke_id,)
    ).fetchone()

    if joke is None:
        abort(404, f"Joke id {joke_id} doesn't exist.")

    return joke