# Just to be safe, here is the script again for your fresh terminal:
$RepoURL = "https://github.com/Wo0ki3-Trader/Day_Trader.git"

# Initialize and Push
git init
git remote add origin $RepoURL
git add .
git commit -m "Initial commit: Quant Edge Command Center"
git branch -M main
git push -u origin main