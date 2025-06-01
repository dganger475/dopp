import React from 'react';
import PageLayout from '../components/PageLayout';

const TermsPage = () => {
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
          Terms and Conditions
        </h1>
        <div style={{ 
          whiteSpace: 'pre-wrap', 
          lineHeight: 1.6,
          fontSize: '1rem'
        }}>
          {`🧾 Terms and Conditions for Doppleganger Social Network
Effective Date: May 30, 2025
Developer: Jacob Layton
Contact: dganger475@gmail.com
Address: 2135 NW 13th St Unit 35, Gresham, OR 97030
Domain: doppleganger.us

Welcome to the Doppleganger Social Network ("App", "we", "our", or "us"). By using this App, you agree to the following terms, which are legally binding. If you do not agree, do not use the App.

1. Purpose of the App
This App allows users to upload face images and discover similar-looking faces from a large visual database. It is designed for entertainment and exploration of facial resemblance.

2. Data Sources and Anonymity
The App uses face images sourced from public yearbooks, which were freely accessible in digital archives.
To protect individual privacy:

School names, years, locations, and identifying metadata have been removed.

Faces in the database are not labeled, tagged, or named.

Users may only recognize themselves or others by visual similarity — no identification is made by the App itself.

3. User-Provided Content
When you create an account or upload a photo, you agree to the following:

Your face image will be processed and added to the App's searchable database, allowing future users to match with it.

Your name and optional demographic info (age, state, decade, gender) may be collected for display or filtering purposes.

You affirm that you own the rights to any image you upload.

4. Identification Policy
Only registered users may recognize their own image in the App.

The App does not identify, name, or label any face-match results.

Any resemblance is visual and not a confirmation of identity.

Matches are not identity confirmations and should not be used as such.

5. Prohibited Uses
You agree not to:

Attempt to de-anonymize or expose individuals in match results

Upload unlawful, harmful, or explicit content

Use the App to harass, impersonate, or harm others

Use the App for doxxing or impersonation

Violation may result in account suspension and legal action.

6. DMCA and Takedown Requests
Registered DMCA Agent: Jacob Layton, Registration Number: DMCA-1063614

If you find your face in the app and wish to have it removed:

📧 Email: dganger475@gmail.com
Include a screenshot or photo for reference.
We will review and remove the content within 72 hours.

7. Ownership and Rights
All original software, content, and design elements of the App are the property of Jacob Layton.
Unauthorized reproduction or redistribution is strictly prohibited.

8. Disclaimer and Limitation of Liability
The App is provided "as is" for informational and entertainment purposes.

We make no guarantees about the accuracy of face matches.

We are not responsible for user actions, misuse of images, or third-party access.

9. Governing Law
These Terms are governed by the laws of the State of Oregon, USA.

© 2025 Doppleganger Social Network. All rights reserved.`}
        </div>
      </div>
    </PageLayout>
  );
};

export default TermsPage; 