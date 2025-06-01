# PowerShell script to apply the pure database approach

# 1. Backup original files
Write-Host "Creating backups of original files..."
Copy-Item "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage.jsx" "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage.jsx.bak" -Force
Copy-Item "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\components\MatchPostCard.jsx" "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\components\MatchPostCard.jsx.bak" -Force

# 2. Replace with the revised versions
Write-Host "Applying pure database approach..."
Copy-Item "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage_revised.jsx" "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage.jsx" -Force
Copy-Item "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\components\MatchPostCard_revised.jsx" "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\components\MatchPostCard.jsx" -Force

# 3. Clean up temporary files
Write-Host "Cleaning up temporary files..."
Remove-Item "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage_revised.jsx" -Force
Remove-Item "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\components\MatchPostCard_revised.jsx" -Force

Write-Host "Database approach successfully applied!"
Write-Host "Changes made:"
Write-Host "1. Removed all localStorage usage"
Write-Host "2. All likes and comments are now stored and retrieved directly from the database"
Write-Host "3. Fixed mobile view styling for the comment input and send button"
Write-Host "4. Added automatic feed refresh every 30 seconds to keep data fresh"
