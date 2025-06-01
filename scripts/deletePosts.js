const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Connect to the database
const db = new sqlite3.Database('faces.db', (err) => {
  if (err) {
    console.error('Error connecting to database:', err);
    return;
  }
  console.log('Connected to faces.db');

  // Get the first post ID
  db.get('SELECT id FROM posts ORDER BY id ASC LIMIT 1', [], (err, firstPost) => {
    if (err) {
      console.error('Error getting first post:', err);
      return;
    }

    if (!firstPost) {
      console.log('No posts found in database');
      return;
    }

    // Delete all posts except the first one
    db.run('DELETE FROM posts WHERE id != ?', [firstPost.id], function(err) {
      if (err) {
        console.error('Error deleting posts:', err);
      } else {
        console.log(`Deleted ${this.changes} posts. Kept post ID ${firstPost.id}`);
      }
      
      // Close the database connection
      db.close((err) => {
        if (err) {
          console.error('Error closing database:', err);
        } else {
          console.log('Database connection closed');
        }
      });
    });
  });
}); 