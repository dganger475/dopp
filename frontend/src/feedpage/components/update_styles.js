// Script to update styles in the MatchPostCard component
// Run this script to make the following changes:
// 1. Make all image borders 1.5x thicker (from 3px to 4.5px)
// 2. Change all image border colors from white to black

const fs = require('fs');
const path = require('path');

// Path to the MatchPostCard component
const filePath = path.join(__dirname, 'MatchPostCard.jsx');

// Read the file
fs.readFile(filePath, 'utf8', (err, data) => {
  if (err) {
    console.error('Error reading file:', err);
    return;
  }

  // Replace all image borders
  let updatedContent = data;
  
  // Replace white borders with black borders and make them 1.5x thicker
  updatedContent = updatedContent.replace(/border: '3px solid #ffffff'/g, "border: '4.5px solid #000000'");
  updatedContent = updatedContent.replace(/border: '3px solid #fff'/g, "border: '4.5px solid #000000'");
  updatedContent = updatedContent.replace(/border: '2px solid #ffffff'/g, "border: '3px solid #000000'");
  updatedContent = updatedContent.replace(/border: '2px solid #fff'/g, "border: '3px solid #000000'");
  
  // Write the updated content back to the file
  fs.writeFile(filePath, updatedContent, 'utf8', (err) => {
    if (err) {
      console.error('Error writing file:', err);
      return;
    }
    console.log('Successfully updated image borders in MatchPostCard.jsx');
  });
});
