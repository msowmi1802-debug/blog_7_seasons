from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from datetime import datetime, timedelta
from database import create_tables, get_connection
from otp_utils import (
    generate_otp,
    save_otp,
    verify_user_otp,
)
from email_utils import send_otp_email

app = Flask(__name__)

app.config["SECRET_KEY"] = "7_seasons-secret-key"

create_tables()

from database import DATABASE
print("Database path:", DATABASE)
import re


def is_valid_password(password):
    """
    Validate password strength.
    """

    if len(password) < 8:

        return (
            False,
            "Password must be at least 8 characters long.",
        )

    if not re.search(r"[A-Z]", password):

        return (
            False,
            "Password must contain at least one uppercase letter.",
        )

    if not re.search(r"[a-z]", password):

        return (
            False,
            "Password must contain at least one lowercase letter.",
        )

    if not re.search(r"\d", password):

        return (
            False,
            "Password must contain at least one number.",
        )

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):

        return (
            False,
            "Password must contain at least one special character.",
        )

    return (
        True,
        "",
    )
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        password = request.form["password"]
        remember_me = request.form.get("remember_me")
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
         """
         SELECT * FROM users
         WHERE email = ?
         """,
              (
                   email,
                ),
        )

        user = cursor.fetchone()
        if user is None:

          conn.close()

          flash(
               "Email not found.",
               "error",
            )

          return redirect(url_for("login"))
        print("Stored Hash:", user["password"])
        print("Entered Password:", password)
        if not check_password_hash(
            user["password"],
            password,
       ):
         
         
         print("Password check failed")
         conn.close()


         flash(
              "Incorrect password.",
              "error",
            )

         return redirect(url_for("login"))
        if user["verified"] == 0:

           session["pending_email"] = user["email"]

           cursor.execute(
              """
              DELETE FROM otp_codes
              WHERE user_id = ?
               """,
             (user["id"],),
            )

           otp = generate_otp()

           save_otp(
              cursor,
              user["id"],
              otp,
            )

           send_otp_email(
             user["email"],
             otp,
            )

           conn.commit()
           conn.close()

           flash(
             "Your email is not verified. Please check your email for the OTP."  
             "A new OTP has been sent to your email.",
             "success",
            )

           return redirect(url_for("verify_otp"))
        if remember_me:

         session.permanent = True

        else:

            session.permanent = False
        app.permanent_session_lifetime = timedelta(days=30)
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        conn.close()

        flash(
          "Login successful!",
          "success",
       )

        return redirect(url_for("dashboard"))
    return render_template("login.html")
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email = ?
            """,
            (email,),
        )

        user = cursor.fetchone()

        if user is None:

            conn.close()

            flash(
                "Email not found.",
                "error",
            )

            return redirect(url_for("forgot_password"))

        otp = generate_otp()

        cursor.execute(
            """
            DELETE FROM otp_codes
            WHERE user_id = ?
            """,
            (user["id"],),
        )

        save_otp(
            cursor,
            user["id"],
            otp,
        )

        send_otp_email(
            email,
            otp,
        )

        conn.commit()
        conn.close()

        session["reset_email"] = email

        flash(
            "OTP sent successfully.",
            "success",
        )

        return redirect(url_for("reset_password"))

    return render_template("forgot_password.html")
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():

    if "reset_email" not in session:

        flash(
            "Session expired.",
            "error",
        )

        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        otp = request.form["otp"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error",
            )

            return redirect(url_for("reset_password"))

        is_valid, message = is_valid_password(password)

        if not is_valid:

            flash(message, "error")

            return redirect(url_for("reset_password"))

        email = session["reset_email"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        )

        user = cursor.fetchone()

        if not verify_user_otp(cursor, user["id"], otp):

            conn.close()

            flash(
                "Invalid or expired OTP.",
                "error",
            )

            return redirect(url_for("reset_password"))

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            UPDATE users
            SET password = ?
            WHERE id = ?
            """,
            (
                hashed_password,
                user["id"],
            ),
        )

        cursor.execute(
            """
            DELETE FROM otp_codes
            WHERE user_id = ?
            """,
            (user["id"],),
        )

        conn.commit()
        conn.close()

        session.pop("reset_email", None)

        flash(
            "Password reset successfully.",
            "success",
        )

        return redirect(url_for("login"))

    return render_template("reset_password.html")
@app.route("/register", methods=["GET", "POST"])
def register():
  
    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            flash("Passwords do not match.", "error")

            return redirect(url_for("register"))
        is_valid, message = is_valid_password(password)

        if not is_valid:

             flash(
                 message,
                 "error",
                )

             return redirect(url_for("register"))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            conn.close()

            flash(
                "Email is already registered.",
                "error",
            )

            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users
            (name,email,password)

            VALUES
            (?,?,?)
            """,
            (
                name,
                email,
                hashed_password,
            ),
        )
        user_id = cursor.lastrowid

        otp = generate_otp()

        save_otp(cursor,user_id, otp)
        send_otp_email(email, otp)
        conn.commit()
        print("User committed successfully")
        conn.close()

        flash(
            "Account created successfully!",
            "success",
        )
        session["pending_email"] = email


        return redirect(url_for("verify_otp"))

    return render_template("register.html")
@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():

    if request.method == "POST":

        otp = request.form["otp"].strip()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
         """
          SELECT * FROM otp_codes
          WHERE otp = ?
         """,
         (otp,),
       )

        otp_record = cursor.fetchone()
        if otp_record is None:

            flash(
               "Invalid OTP.",
               "error",
            )

            conn.close()

            return redirect(url_for("verify_otp"))
        
        expires_at = datetime.fromisoformat(
         otp_record["expires_at"]
        )

        current_time = datetime.now()
        if current_time > expires_at:

         conn.close()

         flash(
             "OTP has expired.",
             "error",
            )

         return redirect(url_for("verify_otp"))
        cursor.execute(
            """
            UPDATE users
            SET verified = 1
            WHERE id = ?
          """,
          (
              otp_record["user_id"],
          ),
        ) 
        cursor.execute(
           """
           DELETE FROM otp_codes
           WHERE id = ?
         """,
           (
              otp_record["id"],
            ),
        )
        conn.commit()
        conn.close()
        flash(
          "Email verified successfully!",
          "success",
        )
        session.pop("pending_email", None)
        return redirect(url_for("login"))
    return render_template("verify_otp.html")
@app.route("/resend_otp")
def resend_otp():

    if "pending_email" not in session:

        flash(
            "Session expired. Please register again.",
            "error",
        )

        return redirect(url_for("register"))

    email = session["pending_email"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM users
        WHERE email = ?
        """,
        (email,),
    )

    user = cursor.fetchone()
    if user is None:
        flash(
            "User not found.",
            "error",
        )
        return redirect(url_for("register"))
    cursor.execute(
        """
        DELETE FROM otp_codes
        WHERE user_id = ?
        """,
        (user["id"],),
    )

    # Generate and send a new OTP
    otp = generate_otp()
    save_otp(cursor, user["id"], otp)
    send_otp_email(email, otp)
    conn.commit()
    conn.close()

    flash(
        "New OTP sent successfully!",
        "success",
    )
    return redirect(url_for("verify_otp"))
@app.route("/create_post", methods=["GET", "POST"])
def create_post():

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form["title"].strip()
        category = request.form["category"]
        visibility = request.form["visibility"]
        content = request.form["content"].strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO posts
            (
                user_id,
                title,
                content,
                category,
                visibility
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                title,
                content,
                category,
                visibility,
            ),
        )

        conn.commit()
        conn.close()

        flash(
            "Post created successfully!",
            "success",
        )

        return redirect(url_for("dashboard"))

    return render_template("create_post.html")
@app.route("/my_posts")
def my_posts():

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM posts
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],),
    )

    posts = cursor.fetchall()

    conn.close()

    return render_template(
        "my_posts.html",
        posts=posts,
    )
@app.route("/post/<int:post_id>")
def view_post(post_id):

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM posts
        WHERE id = ?
        AND user_id = ?
        """,
        (
            post_id,
            session["user_id"],
        ),
    )

    post = cursor.fetchone()

    conn.close()

    if post is None:

        flash(
            "Post not found.",
            "error",
        )

        return redirect(url_for("my_posts"))

    return render_template(
        "view_post.html",
        post=post,
    )
@app.route("/public_post/<int:post_id>")
def public_post(post_id):

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            posts.*,
            users.name
        FROM posts

        JOIN users
        ON posts.user_id = users.id

        WHERE posts.id = ?
        AND posts.visibility = ?
        """,
        (
            post_id,
            "public",
        ),
    )

    post = cursor.fetchone()
    cursor.execute(
       """
       SELECT COUNT(*)
       FROM likes
       WHERE post_id = ?
       """,
      (post_id,),
    )

    like_count = cursor.fetchone()[0]

    cursor.execute(
       """
       SELECT *
       FROM likes
       WHERE user_id = ?
       AND post_id = ?
       """,
       (
          session["user_id"],
          post_id,
        ),
    )

    liked = cursor.fetchone() is not None
    cursor.execute(
      """
      SELECT
         comments.*,
         users.name
     FROM comments

     JOIN users
     ON comments.user_id = users.id

     WHERE post_id = ?

     ORDER BY created_at ASC
     """,
     (post_id,),
    )

    comments = cursor.fetchall()
    conn.close()

    if post is None:

        flash(
            "Post not found.",
            "error",
        )

        return redirect(url_for("public_feed"))
    return render_template(
      "public_post.html",
       post=post,
       like_count=like_count,
       liked=liked,
       comments=comments, 
    )
@app.route("/like_post/<int:post_id>", methods=["POST"])
def like_post(post_id):
    print("========== LIKE ROUTE ==========")
    print("User ID:", session.get("user_id"))
    print("Post ID:", post_id)
    print("Inserting like...")
    print("Committed successfully")
    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM likes
        WHERE user_id = ?
        AND post_id = ?
        """,
        (
            session["user_id"],
            post_id,
        ),
    )

    like = cursor.fetchone()

    if like:

        cursor.execute(
            """
            DELETE FROM likes
            WHERE user_id = ?
            AND post_id = ?
            """,
            (
                session["user_id"],
                post_id,
            ),
        )

    else:

        cursor.execute(
            """
            INSERT INTO likes
            (user_id, post_id)

            VALUES (?, ?)
            """,
            (
                session["user_id"],
                post_id,
            ),
        )

    conn.commit()
    conn.close()

    return redirect(url_for("public_post", post_id=post_id))
@app.route("/add_comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    comment = request.form["comment"].strip()

    if comment == "":

        flash(
            "Comment cannot be empty.",
            "error",
        )

        return redirect(url_for("public_post", post_id=post_id))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO comments
        (user_id, post_id, comment)

        VALUES (?, ?, ?)
        """,
        (
            session["user_id"],
            post_id,
            comment,
        ),
    )

    conn.commit()
    conn.close()

    flash(
        "Comment added successfully!",
        "success",
    )

    return redirect(url_for("public_post", post_id=post_id))
@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM comments
        WHERE id = ?
        AND user_id = ?
        """,
        (
            comment_id,
            session["user_id"],
        ),
    )

    comment = cursor.fetchone()

    if comment is None:

        conn.close()

        flash(
            "Comment not found.",
            "error",
        )

        return redirect(url_for("public_feed"))

    post_id = comment["post_id"]

    cursor.execute(
        """
        DELETE FROM comments
        WHERE id = ?
        """,
        (comment_id,),
    )

    conn.commit()
    conn.close()

    flash(
        "Comment deleted successfully!",
        "success",
    )

    return redirect(url_for("public_post", post_id=post_id))

@app.route("/profile/<int:user_id>")
def profile(user_id):

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    # Get user information
    cursor.execute(
        """
        SELECT
            id,
            name,
            email
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )

    user = cursor.fetchone()

    if user is None:

        conn.close()

        flash(
            "User not found.",
            "error",
        )

        return redirect(url_for("public_feed"))

    # Get only PUBLIC posts
    cursor.execute(
        """
        SELECT *
        FROM posts
        WHERE user_id = ?
        AND visibility = 'public'
        ORDER BY created_at DESC
        """,
        (user_id,),
    )

    public_posts = cursor.fetchall()

    # Count public posts
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM posts
        WHERE user_id = ?
        AND visibility = 'public'
        """,
        (user_id,),
    )

    public_post_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        public_posts=public_posts,
        public_post_count=public_post_count,
    )

@app.route("/public_feed")
def public_feed(post_id=None):

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            posts.*,
            users.name
        FROM posts

        JOIN users
        ON posts.user_id = users.id

        WHERE visibility = ?

        ORDER BY created_at DESC
        """,
        ("public",),
    )

    posts = cursor.fetchall()

    conn.close()

    return render_template(
        "public_feed.html",
        posts=posts,
    )
@app.route("/search")
def search():

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    keyword = request.args.get("q", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            posts.*,
            users.name
        FROM posts

        JOIN users
        ON posts.user_id = users.id

        WHERE posts.visibility = 'public'

        AND (

            posts.title LIKE ?

            OR posts.category LIKE ?

            OR users.name LIKE ?

        )

        ORDER BY posts.created_at DESC
        """,
        (
            f"%{keyword}%",
            f"%{keyword}%",
            f"%{keyword}%",
        ),
    )

    posts = cursor.fetchall()

    conn.close()

    return render_template(
        "search.html",
        posts=posts,
        keyword=keyword,
    )
@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM posts
        WHERE id = ?
        AND user_id = ?
        """,
        (
            post_id,
            session["user_id"],
        ),
    )

    post = cursor.fetchone()

    if post is None:

        conn.close()

        flash(
            "Post not found.",
            "error",
        )

        return redirect(url_for("my_posts"))

    if request.method == "POST":

        title = request.form["title"].strip()
        category = request.form["category"]
        visibility = request.form["visibility"]
        content = request.form["content"].strip()

        cursor.execute(
            """
            UPDATE posts

            SET
                title = ?,
                category = ?,
                visibility = ?,
                content = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                title,
                category,
                visibility,
                content,
                post_id,
            ),
        )

        conn.commit()
        conn.close()

        flash(
            "Post updated successfully!",
            "success",
        )

        return redirect(url_for("my_posts"))

    conn.close()

    return render_template(
        "edit_post.html",
        post=post,
    )
@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM posts
        WHERE id = ?
        AND user_id = ?
        """,
        (
            post_id,
            session["user_id"],
        ),
    )

    conn.commit()
    conn.close()

    flash(
        "Post deleted successfully!",
        "success",
    )

    return redirect(url_for("my_posts"))
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        flash(
            "Please log in first.",
            "error",
        )

        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    # Total Posts
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM posts
        WHERE user_id = ?
        """,
        (session["user_id"],),
    )

    total_posts = cursor.fetchone()[0]

    # Diary Posts
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM posts
        WHERE user_id = ?
        AND category = ?
        """,
        (
            session["user_id"],
            "Diary",
        ),
    )

    diary_posts = cursor.fetchone()[0]

    # Public Posts
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM posts
        WHERE user_id = ?
        AND visibility = ?
        """,
        (
            session["user_id"],
            "public",
        ),
    )

    public_posts = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_posts=total_posts,
        diary_posts=diary_posts,
        public_posts=public_posts,
    )
@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully.",
        "success",
    )

    return redirect(url_for("login"))
if __name__ == "__main__":
 
# Render sets a PORT environment variable; fallback to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    # You must bind to 0.0.0.0 so the container is accessible externally
    app.run(host="0.0.0.0", port=port)
    create_tables()

    app.run(debug=True)