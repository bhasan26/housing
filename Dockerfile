# WhitCloud Dockerfile
# =====================================================================
#                             DOCKERFILE                       
# =====================================================================
# WHAT IS THIS FILE?
# A Dockerfile is a set of instructions for building a Docker container
# that will help run your website. Like a recipe that can be used anywhere, so
# your site can run the same way on any machine.

# WHAT DOES IT DO?
# 1. Uses a lightweight NGINX server.
# 2. Copies all your website files into the container
# 3. Sets everything up to serve your site automatically

# HOW TO USE THIS FILE:
# 1. Place all website files in the same folder as this Dockerfile
# 2. Keep the name as "Dockerfile" (case sensitive)
# 3. **CRITICAL: Update this file when your application structure changes**

# =====================================================================
#                         FILE ORGANIZATION
# =====================================================================
# Your files should be organized like this (example structure):
# Project/              ->  Container Location/
# ├── Dockerfile               
# ├── index.html           ->  /usr/share/nginx/html/index.html
# ├── css/                 ->  /usr/share/nginx/html/css/
# │   └── styles.css      ->  /usr/share/nginx/html/css/styles.css
# ├── js/                 ->  /usr/share/nginx/html/js/
# │   └── script.js       ->  /usr/share/nginx/html/js/script.js
# └── images/             ->  /usr/share/nginx/html/images/
#     └── logo.png        ->  /usr/share/nginx/html/images/logo.png

# =====================================================================
#                       1. BASE IMAGE SETUP
# =====================================================================
# Pull the official NGINX image based on Alpine linux.
FROM nginx:alpine

ARG BASE_IMAGE
ENV BASE_IMAGE=${BASE_IMAGE}

# =====================================================================
#                    2. WEBSITE DIRECTORY SETUP
# =====================================================================
# Defines where your website files will be stored in the container.
# This uses NGINX's default location but it can be changed if needed.
ARG APP_DIR=/usr/share/nginx/html

# =====================================================================
#                     3. COPY WEBSITE FILES
# =====================================================================
# Copy everything from your current directory into the container.
# This preserves your exact folder structure inside the container.
COPY . $APP_DIR

EXPOSE 8080
# =====================================================================
#                       TROUBLESHOOTING
# =====================================================================
# COMMON ISSUES & FIXES:

# 1. Files Missing/Not Updating?
#    - Check files are in same folder as Dockerfile
#    - Rebuild container (push and rerun pipeline) after any file changes
#    - Verify correct folder structure (see example above)

# 2. Website Not Loading?
#    - Verify index.html exists and is in correct location
#    - Make sure file paths in your HTML match your structure

# 3. Changes Not Appearing?
#    - Always rebuild (push and re-run) after changing files
#    - Clear browser cache or try incognito mode
