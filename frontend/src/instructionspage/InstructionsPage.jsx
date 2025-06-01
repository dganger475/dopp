import React from 'react';
import './InstructionsPage.css';

const InstructionsPage = ({ onContinue }) => (
  <div className="instructions-page-reverse">
    <h1>How to Use DoppleGänger</h1>
    <ol>
      <li>Upload your profile photo.</li>
      <li>Discover your historical doppelgänger matches.</li>
      <li>Like, comment, and share posts in the feed.</li>
      <li>Connect with others and explore the community!</li>
    </ol>
    <button className="instructions-btn" onClick={onContinue}>Continue to Feed</button>
  </div>
);

export default InstructionsPage; 