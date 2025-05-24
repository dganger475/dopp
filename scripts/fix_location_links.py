"""
Fix for the location page links in the DoppleGanger app.

This script modifies the URL route patterns to ensure the state cards work correctly.
"""
import os
import re


def fix_routes_file():
    """Update the routes file to add the correct prefixes."""
    routes_file = 'routes/face_matching.py'
    
    if not os.path.exists(routes_file):
        routes_file = os.path.join('c:\\Users\\1439\\Documents\\DopplegangerApp', 'routes/face_matching.py')
    
    if not os.path.exists(routes_file):
        print(f"Cannot find {routes_file}")
        return False
    
    try:
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Find and replace the decorator for the location_faces function
        # with the blueprint prefix properly applied
        pattern = r'@face_matching\.route\(\'\/location\/\<location\>\'\, methods=\[\'GET\'\]\)[\s\n]+@face_matching\.route\(\'\/explore\/location\/\<location\>\'\, methods=\[\'GET\'\]\)'
        replacement = "@face_matching.route('/location/<location>', methods=['GET'])"
        modified = re.sub(pattern, replacement, content)
        
        # Now add correct blueprint URL pattern
        pattern = r'def location_faces\(location\):'
        replacement = "@face_matching.route('/explore/location/<location>', methods=['GET'])\ndef location_faces(location):"
        
        # Remove any duplicate patterns that might have been created
        modified = re.sub(r'@face_matching\.route\(\'/explore/location/<location>\', methods=\[\'GET\'\]\)[\s\n]+@face_matching\.route\(\'/explore/location/<location>\', methods=\[\'GET\'\]\)', 
                         "@face_matching.route('/explore/location/<location>', methods=['GET'])", 
                         modified)
        
        # Replace the function with our fixed version
        with open(routes_file, 'w') as f:
            f.write(modified)
        
        print(f"Updated routes in {routes_file}")
        return True
    except Exception as e:
        print(f"Error updating routes: {e}")
        return False

def fix_template_links():
    """Fix links in the explore_location.html template."""
    template_file = 'templates/explore_location.html'
    
    if not os.path.exists(template_file):
        template_file = os.path.join('c:\\Users\\1439\\Documents\\DopplegangerApp', 'templates/explore_location.html')
    
    if not os.path.exists(template_file):
        print(f"Cannot find {template_file}")
        return False
    
    try:
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Fix the link to use the direct URL pattern instead of url_for
        if "url_for('face_matching.location_faces', location=location)" in content:
            content = content.replace(
                "url_for('face_matching.location_faces', location=location)",
                "'/faces/explore/location/' + location"
            )
            
            with open(template_file, 'w') as f:
                f.write(content)
            
            print(f"Updated links in {template_file}")
            return True
        else:
            print("No links to fix in template")
            return False
    except Exception as e:
        print(f"Error updating template: {e}")
        return False

def add_test_route():
    """Add a test route to the face_matching blueprint."""
    routes_file = 'routes/face_matching.py'
    
    if not os.path.exists(routes_file):
        routes_file = os.path.join('c:\\Users\\1439\\Documents\\DopplegangerApp', 'routes/face_matching.py')
    
    if not os.path.exists(routes_file):
        print(f"Cannot find {routes_file}")
        return False
    
    try:
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Check if the test route already exists
        if "def test_location_links():" in content:
            print("Test route already exists")
            return True
        
        # Add the test route after the last function
        test_route = """
@face_matching.route('/test_location_links')
def test_location_links():
    """Test page for location links."""
    return render_template('test_location_links.html')
"""
        
        # Make sure we're not adding duplicates
        if test_route.strip() not in content:
            content += test_route
            
            with open(routes_file, 'w') as f:
                f.write(content)
            
            print(f"Added test route to {routes_file}")
            return True
        else:
            print("Test route already present")
            return True
    except Exception as e:
        print(f"Error adding test route: {e}")
        return False

if __name__ == "__main__":
    print("Fixing location page links...")
    
    # Fix the route patterns
    fix_routes_file()
    
    # Fix template links
    fix_template_links()
    
    # Add test route
    add_test_route()
    
    print("Done! Restart the Flask app to apply changes.")
