import React from 'react';
import PageLayout from '../components/PageLayout';

const PrivacyPage = () => {
  return (
    <PageLayout>
      <div style={{ 
        maxWidth: 800, 
        margin: '2rem auto', 
        padding: '2rem', 
        background: '#fff', 
        borderRadius: 12, 
        boxShadow: '0 2px 12px rgba(0,0,0,0.07)',
        color: '#333'
      }}>
        <h1 style={{ 
          fontSize: '2rem', 
          marginBottom: '1.5rem', 
          color: '#1b74e4',
          textAlign: 'center'
        }}>
          Privacy Policy
        </h1>
        <div style={{ 
          whiteSpace: 'pre-wrap', 
          lineHeight: 1.6,
          fontSize: '1rem'
        }}>
          {`1. Who We Are
Doppleganger Social Network is developed by Jacob Layton and operated from:
📍 2135 NW 13th St Unit 35, Gresham, OR 97030
📧 dganger475@gmail.com

2. What We Collect
When you register or use the app, we may collect:

a. Information You Provide
Name (for your profile)

Face Image Uploads (used to find look-alikes)

Optional tags (state, decade, gender, etc.)

b. Automatic Data
Anonymous usage data and logs

Device type and general technical info

3. What We Do With It
We use this information to:

Generate face match results

Let others match against your uploaded image

Power search filters and improve app quality

Respond to support or takedown requests

We do not sell or share your data with outside companies.

4. Public Yearbook Images
All base images in our system were taken from publicly available yearbooks, which are understood to be in the public domain.
We take the following steps to ensure privacy:

Strip identifying metadata (school, year, location)

Do not label or tag any face images

Use facial embeddings (not full images) for comparisons

5. User Uploads and Database Inclusion
When you upload a face:

It is converted into a numerical face vector used for matching

Your face vector is added to the database, allowing others to match with it

Your original photo is securely stored, but not visible to other users

6. Recognition and Labeling
Only you can identify yourself in results

The App does not identify, label, or claim identities

No personal information is embedded into search results

7. Data Security
We protect your data by:

Using secure storage and face encoding systems

Limiting internal access

Never embedding names directly into image data

However, no system is foolproof. You use the app at your own risk.

8. Removal and Your Rights
You can:

Request deletion of your image, name, or embedding

Ask what data we hold on you

Withdraw consent at any time

📧 Contact: dganger475@gmail.com
We typically respond and process removals within 72 hours.

9. Children's Privacy
This app is not for children under 13. We also attempt to avoid displaying images of minors by filtering yearbooks for adult content where possible.

10. Updates
We may revise this policy at any time. Check back periodically to stay informed.

Questions?
Contact: dganger475@gmail.com
© 2025 Doppleganger Social Network. All rights reserved.`}
        </div>
      </div>
    </PageLayout>
  );
};

export default PrivacyPage; 