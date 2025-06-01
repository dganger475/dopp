"""
Card Helper Utilities

This module provides helper functions for creating standardized cards
across the application based on the universal card system.
"""


def create_user_card_context(
    user, link_url=None, is_highlighted=False, include_actions=False
):
    """
    Create context dictionary for a user card

    Args:
        user: User data dictionary or object
        link_url: URL to navigate to when card is clicked
        is_highlighted: Whether to add highlight border
        include_actions: Whether to include action buttons

    Returns:
        Dictionary with context for universal_card.html
    """
    # Handle both dictionary and object access patterns
    if isinstance(user, dict):
        get_attr = lambda obj, attr, default: obj.get(attr, default)
    else:
        get_attr = lambda obj, attr, default: getattr(obj, attr, default)

    # Create details list
    details = []

    location = get_attr(user, "location", None) or get_attr(user, "state", None)
    if location:
        details.append({"icon": "icon-location", "text": f"{location}"})

    age = get_attr(user, "age", None)
    if age:
        details.append({"icon": "icon-cake", "text": f"Age: {age}"})

    decade = get_attr(user, "decade", None)
    if decade:
        # Convert to format like "1990s" if it's just a year
        s_decade = str(decade)  # Ensure string for isdigit and slicing
        if s_decade.isdigit() and len(s_decade) == 4:
            decade = f"{s_decade[:3]}0s"
        details.append({"text": f"Decade: {decade}"})

    actions = []
    if include_actions:
        user_id = get_attr(user, "id", None)
        if user_id:
            actions.append(
                {
                    "type": "link",
                    "class": "primary",
                    "url": f"/profile/{user_id}",
                    "text": "View Profile",
                }
            )

    # Get image URL
    image_url = get_attr(user, "profile_image", None) or get_attr(
        user, "image_url", None
    )
    image_url = image_url or "/static/default_profile.png"

    # Get username for title
    username = get_attr(user, "username", None) or get_attr(user, "name", "User")

    return {
        "card_type": "user",
        "link_url": link_url,
        "image_url": image_url,
        "title": username,
        "subtitle": get_attr(user, "email", None),
        "details": details,
        "is_highlighted": is_highlighted,
        "actions": actions,
    }


def create_match_card_context(
    match, link_url=None, is_highlighted=True, include_actions=True
):
    """
    Create context dictionary for a match card

    Args:
        match: Match data dictionary
        link_url: URL to navigate to when card is clicked
        is_highlighted: Whether to add highlight border
        include_actions: Whether to include action buttons

    Returns:
        Dictionary with context for universal_card.html
    """
    # Create details list
    details = []

    # Location (state)
    if match.get("state"):
        details.append({"icon": "icon-location", "text": f'{match["state"]}'})

    # Decade
    if match.get("decade"):
        decade_val = match["decade"]
        # Convert to format like "1990s" if it's just a year
        s_decade_val = str(decade_val)  # Ensure string for isdigit and slicing
        if s_decade_val.isdigit() and len(s_decade_val) == 4:
            decade_val = f"{s_decade_val[:3]}0s"
        details.append({"text": f"Decade: {decade_val}"})

    # Actions
    actions = []
    if include_actions:
        match_id = match.get("match_id") or match.get("id")
        if match_id:
            # Add to collection button
            # TODO: Review if 'Add' and 'Share' actions should be distinct or if current identical /social/share_match endpoint is intended.
            actions.append(
                {
                    "type": "form",
                    "method": "POST",
                    "url": "/social/share_match",
                    "class": "primary",
                    "text": "Add",
                    "fields": [{"name": "match_id", "value": match_id}],
                }
            )

            # Share button
            actions.append(
                {
                    "type": "form",
                    "method": "POST",
                    "url": "/social/share_match",
                    "class": "primary",
                    "text": "Share",
                    "fields": [{"name": "match_id", "value": match_id}],
                }
            )

            # Delete button
            actions.append(
                {
                    "type": "link",
                    "url": f"/api/hide_match/{match_id}",
                    "class": "danger",
                    "text": "Delete",
                }
            )

            # Back button
            actions.append(
                {
                    "type": "link",
                    "url": "/profile",
                    "class": "secondary",
                    "text": "Back",
                }
            )

    # Generate appropriate image URL
    image_url = None
    if match.get("safe_image_path"):
        # Assuming safe_image_path is already a complete URL or a path usable by url_for if needed
        image_url = match["safe_image_path"]
    elif match.get("filename"):
        # Consider using url_for('static', filename=f'faces/{match["filename"]}') for robustness
        image_url = f"/static/faces/{match['filename']}"
    else:
        # Fallback to direct match image endpoint if we have an ID
        match_id = match.get("match_id") or match.get("id")
        if match_id:
            image_url = f"/direct-match-image/{match_id}"
        else:
            image_url = "/static/default_profile.png"

    # Get similarity score
    similarity = match.get("similarity") or match.get("faiss_score") or 0
    if isinstance(similarity, str) and similarity.endswith("%"):
        similarity = similarity[:-1]  # Remove % if present

    return {
        "card_type": "match",
        "link_url": link_url,
        "image_url": image_url,
        "title": match.get("name", "Match"),
        "subtitle": None,
        "match_percentage": similarity,
        "details": details,
        "is_highlighted": is_highlighted,
        "actions": actions,
    }
