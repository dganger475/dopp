"""
Configure Backblaze B2 CORS settings for the application.
"""

import os
import json
import b2sdk.v2 as b2
from dotenv import load_dotenv

def configure_b2_cors():
    """Configure CORS settings for B2 bucket."""
    # Load environment variables
    load_dotenv()
    
    # Get B2 credentials
    application_key_id = os.getenv('B2_APPLICATION_KEY_ID')
    application_key = os.getenv('B2_APPLICATION_KEY')
    bucket_name = os.getenv('B2_BUCKET_NAME')
    
    if not all([application_key_id, application_key, bucket_name]):
        raise ValueError("B2 credentials not properly configured in .env file")
    
    # Initialize B2 client
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    b2_api.authorize_account("production", application_key_id, application_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)
    
    # Define CORS rules
    cors_rules = [
        {
            "corsRuleName": "AllowAppAccess",
            "allowedOrigins": [
                "http://localhost:3000",  # Development
                "http://localhost:5000",  # Development
                "https://yourdomain.com",  # Production - replace with your domain
                "https://www.yourdomain.com"  # Production - replace with your domain
            ],
            "allowedOperations": [
                "b2_download_file_by_name",
                "b2_download_file_by_id"
            ],
            "allowedHeaders": ["*"],
            "exposeHeaders": ["*"],
            "maxAgeSeconds": 3600  # 1 hour
        }
    ]
    
    # Update bucket CORS rules
    bucket.update_cors_rules(cors_rules)
    print(f"Successfully configured CORS rules for bucket: {bucket_name}")
    
    # Print current CORS rules for verification
    current_rules = bucket.get_cors_rules()
    print("\nCurrent CORS rules:")
    print(json.dumps(current_rules, indent=2))

if __name__ == "__main__":
    configure_b2_cors() 