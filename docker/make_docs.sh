#!/bin/bash
set -e

# Build the documentation
cd /revolve
doxygen docs/Doxyfile

# Push the documentation on `gh-pages` branch
git config credential.helper 'cache --timeout=120'
git config user.email "<email>"
git config user.name "Documentation bot"
git add docs/
git commit -m "Update documentation via CircleCI [ci skip]"
git push -q https://${GITHUB_PERSONAL_TOKEN}@github.com/ci-group/revolve.git gh-pages
