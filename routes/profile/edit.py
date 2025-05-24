from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, flash, current_app
import os, traceback, secrets, time
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from models.user import User
from forms.profile_forms import ProfileEditForm
from .helpers import save_image
from utils.face.indexing import index_profile_face
import wtforms

edit_profile_bp = Blueprint('edit_profile', __name__)

@edit_profile_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile_view():
    user = current_user
    form = ProfileEditForm()

    if request.method == "POST":
        current_app.logger.info(f"POST request received for user: {user.id}")
        current_app.logger.info(f"Form data: {request.form}")
        current_app.logger.info(f"File data: {request.files}")
        if form.validate_on_submit():
            try:
                updates = {}
                changed_fields = []

                # Ensure this list matches the fields in ProfileEditForm and User model where applicable
                form_fields_to_iterate = [
                    "username", "first_name", "last_name", "email", "birthdate",
                    "bio", "current_location_city", "current_location_state",
                    "hometown", "website", "interests"
                    # Note: profile_photo is handled separately as it's a file
                ]

                for field_name in form_fields_to_iterate:
                    # Check if the form object actually has this field
                    if hasattr(form, field_name):
                        form_field_obj = getattr(form, field_name)
                        new_value = form_field_obj.data
                        current_value = getattr(user, field_name, None)
                        
                        # Special handling for DateField to convert to string if needed by model
                        if isinstance(form_field_obj, wtforms.fields.DateField) and new_value is not None:
                            new_value = new_value.isoformat() # Or str(new_value)

                        if new_value is not None and new_value != current_value:
                            updates[field_name] = new_value
                            changed_fields.append(field_name)
                    else:
                        current_app.logger.warning(f"Form field '{field_name}' not found in ProfileEditForm. Skipping.")

                profile_photo_file = request.files.get("profile_photo") # Matches name in React form
                if profile_photo_file and profile_photo_file.filename:
                    folder = "static/profile_pics"
                    # The save_image function should return the filename to be stored
                    profile_filename = save_image(profile_photo_file, folder, is_profile=True, user_id=user.id)
                    if profile_filename:
                        updates["profile_image"] = profile_filename # User model uses profile_image
                        changed_fields.append("profile_image")
                        try:
                            indexed_face_filename = index_profile_face(
                                filename=profile_filename, 
                                user_id=user.id, 
                                username=user.username
                            )
                            if not indexed_face_filename:
                                flash("Profile photo saved, but there was an issue making it fully searchable.", "warning")
                        except Exception as e:
                            current_app.logger.error(f"Error during index_profile_face: {e}")
                            flash("Profile photo saved, but there was an issue making it fully searchable.", "warning")

                cover_photo = request.files.get("cover_photo")
                if cover_photo and cover_photo.filename:
                    folder = current_app.config.get('COVER_PHOTOS_FOLDER', 'static/cover_photos')
                    cover_filename = save_image(cover_photo, folder, is_profile=False, user_id=user.id)
                    if cover_filename:
                        updates["cover_photo"] = cover_filename
                        changed_fields.append("cover_photo")

                if updates:
                    user.update(**updates)
                    flash("Profile updated successfully!", "success")
                else:
                    flash("No changes were made to your profile.", "info")

                return redirect(url_for("profile_view.view_profile"))

            except Exception as e:
                current_app.logger.error(f"Error updating profile: {e}", exc_info=True)
                flash("An error occurred while updating your profile. Please try again.", "error")

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", "error")

    return render_template("edit_profile.html", form=form, user=user)