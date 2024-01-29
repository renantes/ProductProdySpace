#!/bin/bash

# Define variables
REPO_DIR="Renantes/ProductProdySpace"
GH_PAGES_DIR="main"  # Name of the gh-pages branch
BUILD_DIR="_build"  # Temporary build directory

# Clone the repository and create the gh-pages branch
git clone https://github.com/$REPO_DIR $BUILD_DIR
cd $BUILD_DIR
git checkout --orphan $GH_PAGES_DIR
git reset --hard

# Build the Dash app
python app.py  # Replace with the command to run your Dash app and generate HTML

# Move the generated HTML files to the root of the gh-pages branch
mv -f *.html ../
cd ..
rm -rf $BUILD_DIR

# Commit and push changes to the gh-pages branch
git add *.html
git commit -m "Update Dash app"
git push origin $GH_PAGES_DIR

# Clean up
git checkout main  # Switch back to the main branch
