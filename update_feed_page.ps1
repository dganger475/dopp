# PowerShell script to replace the old FeedPage.jsx with the new version
# Check if the new file exists
if (Test-Path "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage.jsx.new") {
    # Backup the old file
    Copy-Item "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage.jsx" "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage.jsx.bak" -Force
    
    # Replace the old file with the new one
    Move-Item "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage.jsx.new" "C:\Users\dumpy\Documents\Dopp\frontend\src\feedpage\FeedPage.jsx" -Force
    
    Write-Host "FeedPage.jsx has been successfully updated!"
} else {
    Write-Host "Error: The new file FeedPage.jsx.new does not exist."
}
