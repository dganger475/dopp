import os
import re


def add_delete_buttons():
    """Add delete buttons to the matches.html template"""
    template_path = os.path.join('templates', 'matches.html')
    
    # Read the current template
    with open(template_path, 'r') as file:
        content = file.read()
    
    # Patterns to look for
    claimed_profile_pattern = r'<div class="match-actions">\s+<button class="action-btn compare-btn"[^>]+>\s+<i class="fas fa-sync-alt"></i>\s+</button>\s+<button class="action-btn share-btn"[^>]+>\s+<i class="fas fa-share-alt"></i>\s+</button>\s+<button class="action-btn connect-btn"[^>]+>\s+<i class="fas fa-user-plus"></i>\s+</button>\s+</div>'
    
    unclaimed_match_pattern = r'<div class="match-actions">\s+<button class="action-btn compare-btn"[^>]+>\s+<i class="fas fa-sync-alt"></i>\s+</button>\s+<a href="{{ url_for\(\'face_matching.claim_profile\', filename=match.filename\) }}" class="action-btn">\s+<i class="fas fa-flag"></i>\s+</a>\s+</div>'
    
    # Replacement with delete buttons
    claimed_profile_replacement = '''<div class="match-actions">
                                        <button class="action-btn compare-btn" data-bs-toggle="modal" data-bs-target="#compareModal" 
                                                data-match-img="/static/extracted_faces/{{ profile.face_filename }}" 
                                                data-relationship="{{ profile.relationship }}" 
                                                data-caption="{{ profile.caption }}">
                                            <i class="fas fa-sync-alt"></i>
                                        </button>
                                        <button class="action-btn share-btn" data-bs-toggle="modal" data-bs-target="#shareModal"
                                                data-match-img="/static/extracted_faces/{{ profile.face_filename }}" 
                                                data-relationship="{{ profile.relationship }}">
                                            <i class="fas fa-share-alt"></i>
                                        </button>
                                        <button class="action-btn connect-btn" title="Connect with others who match with this profile">
                                            <i class="fas fa-user-plus"></i>
                                        </button>
                                        <a href="{{ url_for('face_matching.unclaim_profile', filename=profile.face_filename) }}" 
                                           class="action-btn" title="Remove this claimed profile"
                                           onclick="return confirm('Are you sure you want to unclaim this profile?');">
                                            <i class="fas fa-trash"></i>
                                        </a>
                                    </div>'''
    
    unclaimed_match_replacement = '''<div class="match-actions">
                                        <button class="action-btn compare-btn" data-bs-toggle="modal" data-bs-target="#compareModal" 
                                                data-match-img="/static/extracted_faces/{{ match.filename }}" 
                                                data-relationship="Mystery Match" 
                                                data-caption="Unclaimed match">
                                            <i class="fas fa-sync-alt"></i>
                                        </button>
                                        <a href="{{ url_for('face_matching.claim_profile', filename=match.filename) }}" class="action-btn">
                                            <i class="fas fa-flag"></i>
                                        </a>
                                        <a href="{{ url_for('face_matching.delete_match', match_filename=match.filename) }}" 
                                           class="action-btn" title="Remove this match from your profile"
                                           onclick="return confirm('Are you sure you want to remove this match?');">
                                            <i class="fas fa-trash"></i>
                                        </a>
                                    </div>'''
    
    # Fix the data-match-img paths throughout the template to use extracted_faces instead of faces
    content = content.replace('data-match-img="/static/faces/', 'data-match-img="/static/extracted_faces/')
    
    # Add delete buttons - modify claimed profiles
    modified_content = re.sub(claimed_profile_pattern, claimed_profile_replacement, content, flags=re.DOTALL)
    
    # Add delete buttons - modify unclaimed matches
    final_content = re.sub(unclaimed_match_pattern, unclaimed_match_replacement, modified_content, flags=re.DOTALL)
    
    # Write the modified template back
    with open(template_path, 'w') as file:
        file.write(final_content)
    
    print("Successfully added delete buttons to the matches template")

if __name__ == "__main__":
    add_delete_buttons()
