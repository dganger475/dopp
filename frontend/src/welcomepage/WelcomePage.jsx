import React from 'react';
import { Link } from 'react-router-dom';

// Import your Uizard components
// Make sure the relative paths are correct if they are in subfolders,
// but based on the list_dir output, they are in the same 'welcomepage' directory.
import UizardImage19 from './Image (19).jsx'; // Renaming for clarity
import UizardText31 from './Text (31).jsx';
import UizardText32 from './Text (32).jsx';
import UizardGetStartedButton from './get started button.jsx';

const WelcomePage = () => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: 'var(--dopple-blue)', // Main background
      color: 'var(--dopple-white)',          // Default text color on blue background
      padding: '20px',
      textAlign: 'center',
      boxSizing: 'border-box'
    }}>
      
      {/* You can use your Uizard image component here */}
      {/* If UizardImage19 is the logo: */}
      <div style={{ marginBottom: '30px' }}>
        <UizardImage19 /> 
      </div>
      {/* Or if it's a different image and you want the static logo: */}
      {/* <img src="/images/logo.png" alt="DoppleGanger Logo" style={{ height: '100px', width: '100px', marginBottom: '30px' }} /> */}

      {/* Headline Text from Uizard */}
      <div style={{ marginBottom: '20px' }}>
        <UizardText31 /> 
      </div>

      {/* Sub-headline or descriptive text from Uizard */}
      <div style={{ marginBottom: '30px', fontSize: '1.2em' }}>
        <UizardText32 />
      </div>

      {/* "Get Started" button from Uizard */}
      {/* You might need to wrap it or pass props if it needs to navigate */}
      <div style={{ marginBottom: '40px' }}>
        {/* If the button handles its own navigation or action: */}
        <UizardGetStartedButton />
        {/* Or if you need to make it a link: */}
        {/* <Link to="/register" style={{textDecoration: 'none'}}>
             <UizardGetStartedButton />
           </Link> */}
      </div>
      
      <p style={{ marginBottom: '20px', fontSize: '1em' }}>
        Already have an account?
      </p>

      <div style={{ display: 'flex', gap: '20px' }}>
        <Link to="/login" style={{
          padding: '12px 25px',
          backgroundColor: 'var(--dopple-black)',
          color: 'var(--dopple-white)',
          textDecoration: 'none',
          borderRadius: '5px',
          fontSize: '1.1em',
          border: '1px solid var(--dopple-black)'
        }}>
          Login
        </Link>
        <Link to="/register" style={{
          padding: '12px 25px',
          backgroundColor: 'var(--dopple-white)',
          color: 'var(--dopple-black)',
          textDecoration: 'none',
          borderRadius: '5px',
          fontSize: '1.1em',
          border: '1px solid var(--dopple-white)'
        }}>
          Register
        </Link>
      </div>

    </div>
  );
};

export default WelcomePage;
