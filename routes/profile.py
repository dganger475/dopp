@profile.route("/create_default_image", methods=["POST"])
def create_default_image():
    """
    Create a default profile image if it doesn't exist.
    - If a file is uploaded, use it as the default image.
    - Otherwise, generate a simple default image with a blue background and a question mark.
    Returns JSON with success status and message.
    """
    try:
        # Check if the default image already exists
        default_image_path = os.path.join(
            current_app.root_path, "static", "default_profile.png"
        )

        if os.path.exists(default_image_path):
            return jsonify({"success": True, "message": "Default image already exists"})

        # If a file was uploaded, use that
        if "default_image" in request.files:
            file = request.files["default_image"]
            file.save(default_image_path)
            return jsonify(
                {"success": True, "message": "Default image created from uploaded file"}
            )

        # Otherwise, create a simple default image
        from PIL import Image, ImageDraw, ImageFont

        # Create a blank image with blue background
        img = Image.new("RGB", (200, 200), color=(78, 115, 223))
        d = ImageDraw.Draw(img)

        # Try to add a question mark
        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except IOError:
            font = ImageFont.load_default()

        # Draw a question mark in the center
        d.text((100, 100), "?", fill="white", font=font, anchor="mm")

        # Save the image
        img.save(default_image_path)

        return jsonify({"success": True, "message": "Default image created"})
    except Exception as e:
        current_app.logger.error(f"Error creating default image: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@profile.route("/profile_image/<path:filename>")
def serve_profile_image(filename):
    """
    Serve a profile image file. If the image is not found, return the default image.
    """
    try:
        # Try to find the image in various locations
        possible_paths = [
            os.path.join(current_app.root_path, "static", "profile_pics", filename),
            os.path.join(current_app.root_path, "static", "images", filename),
            os.path.join(current_app.root_path, "static", filename)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return send_file(path, mimetype='image/jpeg')
        
        # If image not found, return default image
        default_path = os.path.join(current_app.root_path, "static", "default_profile.png")
        if not os.path.exists(default_path):
            # Create default image if it doesn't exist
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a blank image with blue background
            img = Image.new("RGB", (200, 200), color=(78, 115, 223))
            d = ImageDraw.Draw(img)
            
            # Try to add a question mark
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except IOError:
                font = ImageFont.load_default()
            
            # Draw a question mark in the center
            d.text((100, 100), "?", fill="white", font=font, anchor="mm")
            
            # Save the image
            img.save(default_path)
        
        return send_file(default_path, mimetype='image/png')
        
    except Exception as e:
        current_app.logger.error(f"Error serving profile image {filename}: {e}")
        return jsonify({"error": "Failed to serve image"}), 500
