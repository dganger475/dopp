import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from forms.admin_forms import AdminLoginForm, AdminMatchForm

admin = Blueprint("admin", __name__)

ADMIN_USERNAME = "Bossman11"
ADMIN_PASSWORD = "Adidas112"


# Admin login
@admin.route("/login", methods=["GET", "POST"])
def admin_login():
    form = AdminLoginForm()
    error = None
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin.admin_dashboard"))
        else:
            error = "Invalid username or password."
    return render_template("admin_login.html", form=form, error=error)


# Admin dashboard

# Feed style update (stub, to be implemented)
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class StyleForm(FlaskForm):
    feed_text_color = StringField("Feed Text Color")
    feed_bg_color = StringField("Feed Background Color")
    submit = SubmitField("Update Feed Style")


@admin.route("/", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin.admin_login"))
    style_form = StyleForm()
    match_form = AdminMatchForm()
    match_result = None
    if style_form.submit.data and style_form.validate_on_submit():
        # Handle feed style update logic here
        flash("Feed style updated (not yet implemented).")
    if match_form.submit.data and match_form.validate_on_submit():
        file = match_form.admin_image.data
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join("static", "admin_uploads")
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            match_result = {
                "image_url": "/" + file_path.replace("\\", "/"),
                "details": "Face matching result would go here.",
            }
    return render_template(
        "admin_dashboard.html",
        style_form=style_form,
        match_form=match_form,
        match_result=match_result,
    )


# Admin-only match search
@admin.route("/admin/find_match", methods=["GET", "POST"])
def admin_find_match():
    if not session.get("is_admin"):
        return redirect(url_for("admin.admin_login"))
    style_form = StyleForm()
    match_form = AdminMatchForm()
    match_result = None
    match_results = None
    match_result_image = None
    if match_form.validate_on_submit():
        file = match_form.admin_image.data
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join("static", "admin_uploads")
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            match_result_image = "/" + file_path.replace("\\", "/")
            match_results = get_top_50_matches(file_path)
    return render_template(
        "admin_dashboard.html",
        style_form=style_form,
        match_form=match_form,
        match_results=match_results,
        match_result_image=match_result_image,
    )


# --- REAL FACE MATCHING LOGIC ---
from utils.similarity import query_faces_directly


def get_top_50_matches(image_path):
    """
    Uses the real backend to get the top 50 most similar faces for the uploaded image.
    Ensures every match has a correct image_url for /static/extracted_faces/{filename}.
    """
    results = query_faces_directly(image_path, top_k=50)
    formatted = []
    for match in results:
        filename = match.get("filename") or (
            match.get("image_url", "").split("/")[-1]
            if match.get("image_url")
            else None
        )
        image_url = f"/static/extracted_faces/{filename}" if filename else ""
        formatted.append(
            {
                "image_url": image_url,
                "name": match.get("name", filename or "Unknown"),
                "similarity_score": round(match.get("similarity", 0), 3),
            }
        )
    return formatted


# Admin logout
@admin.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.admin_login"))
