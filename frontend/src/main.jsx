import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import PlasmicHost from './plasmic-host.jsx';
import '@fortawesome/fontawesome-svg-core/styles.css'; // Import the CSS
import { config } from '@fortawesome/fontawesome-svg-core';
config.autoAddCss = false; // Tell Font Awesome to skip adding the CSS automatically since it's already imported

const path = window.location.pathname;

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {path === '/plasmic-host' ? <PlasmicHost /> : <App />}
  </React.StrictMode>
);
