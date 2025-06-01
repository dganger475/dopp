import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test endpoints
BASE_URL = 'http://localhost:5000'
PROFILE_URL = f'{BASE_URL}/api/profile/data'

def test_profile_endpoint():
    """Test the profile data endpoint with detailed logging."""
    logger.info(f"Testing profile endpoint: {PROFILE_URL}")
    
    # First test OPTIONS request (preflight)
    try:
        logger.info("Sending OPTIONS request...")
        options_response = requests.options(
            PROFILE_URL,
            headers={
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        
        logger.info(f"OPTIONS Response Status: {options_response.status_code}")
        logger.info(f"OPTIONS Response Headers: {dict(options_response.headers)}")
        
        # Check for CORS headers
        if 'Access-Control-Allow-Origin' in options_response.headers:
            logger.info("✅ CORS preflight headers present")
        else:
            logger.error("❌ CORS preflight headers missing")
    
    except Exception as e:
        logger.error(f"Error during OPTIONS request: {e}")
    
    # Now test GET request
    try:
        logger.info("\nSending GET request...")
        response = requests.get(
            PROFILE_URL,
            headers={
                'Origin': 'http://localhost:5173',
                'Content-Type': 'application/json'
            },
            cookies={}  # Add session cookies here if needed
        )
        
        logger.info(f"GET Response Status: {response.status_code}")
        logger.info(f"GET Response Headers: {dict(response.headers)}")
        
        # Check for CORS headers
        if 'Access-Control-Allow-Origin' in response.headers:
            logger.info("✅ CORS response headers present")
        else:
            logger.error("❌ CORS response headers missing")
        
        # Try to parse the response body
        try:
            body = response.json()
            logger.info(f"Response Body: {json.dumps(body, indent=2)}")
        except Exception as e:
            logger.error(f"Could not parse response as JSON: {e}")
            logger.info(f"Raw Response: {response.text[:500]}...")
    
    except Exception as e:
        logger.error(f"Error during GET request: {e}")

if __name__ == "__main__":
    test_profile_endpoint()
