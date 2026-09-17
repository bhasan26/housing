# **whitworth-room-inventory**


_Replace with a brief description of your project or application._

---

**Unsure about DB setup or adding new components?**

> Checkout these example templates:
 https://whitgit.whitworth.edu/tutorials/whitcloud-tutorials-and-example-templates

# Project Status and Access
[![Pipeline Status](https://whitgit.whitworth.edu/2026/spring/CS-472-2/groupprojects/whitworth-room-inventory/whitworth-room-inventory-frontend/badges/release/pipeline.svg)](https://whitgit.whitworth.edu/2026/spring/CS-472-2/groupprojects/whitworth-room-inventory/whitworth-room-inventory-frontend/pipelines)

## Access  
When the `release` pipeline passes, your app will be accessible at:  
**https://whitworth-room-inventory.whitcloud.org**

- **On campus:** Add `whitworth-room-inventory.whitcloud.org` to your hosts file (e.g., `/etc/hosts` on Linux/Mac or `C:\Windows\System32\drivers\etc\hosts` on Windows) with the IP address of the server (e.g., 10.200.1.200 something-cool.whitcloud.org). See "How to Edit Your Hosts File" guides if needed.  
- **Off campus:** Access is restricted contact your professor or WhitCloud Admin.

---

# Deployment Workflow

1. **Push code to `release` branch:**  
   Triggers a deployment to production. The live site is always built from `release`.
2. **Keep branches in sync:**  
   After deployment, merge changes from `release` back into `main` to prevent drift.
3. **Monitor application status:**
   Use dashboard access to view your application's logs and database in production.

---

# Critical: Update Your Dockerfile

**Your Dockerfile MUST be updated whenever you change your application structure.** This is **not** optional - the pipeline may fail or your changes may not be present in production.

## When to Update Your Dockerfile:
- Adding new files or folders to your project
- Installing new dependencies or packages
- Changing your main application file names
- Using different ports in your application
- Adding system level dependencies
- Changing your tech stack or framework

## Common Issues:
- **Project type changed** (e.g., from static site to React app) -> Update base image and build steps
- **File not found type errors in pipeline** -> Add missing files to COPY commands
- **Module not found type errors** -> Update requirements.txt, package.json, or dependency files
- **Application won't start** -> Check EXPOSE ports and CMD/ENTRYPOINT commands

**Remember: The Dockerfile is part of your application code - treat it as such!**

---

# Microservice Architecture on WhitCloud

WhitCloud is built to support both **simple apps** and **microservices**:

## Repo Structure
- **frontend repo:**  
  For UI/static apps or simple client only deployments.  
  If you don’t need backend logic, just deploy to this repo.
- **backend repo:**  
  For APIs, business logic, or any app needing a database or server side processing.

## Typical Deployment Scenarios

### Simple Frontend Only App
- Work in the **frontend repo**.
- Push to `release` branch to deploy.
- App auto-builds and deploys no backend, no database.

### Microservice App
- Use both **frontend** and **backend** repos.
- Backend: Add API logic and handle all DB code/migrations in code.
- Push frontend and backend to their `release` branches.


---

# Database and Environment Variable Conventions

- **No raw SQL files in Production.**  
  Database schema/migrations must be code based (ORM, migration scripts, etc).
- **Do not hardcode production credentials.**  
  All DB details must be injected via environment variables.  
  Local development: use `.env` file (use a .gitignore file).  
  Production: values are auto injected (dynamically and securely) via WhitCloud deployment.
- **Specify what database is being used.**
  In the file ".database" put either mysql (default) or postgres.

## Use these exact variable names:
```env
DB_USERNAME
DB_PASSWORD
DB_DATABASE
DB_HOST
# Optionally:
DB_PORT

Never do this:
DB_USERNAME=my-user    # Do not hardcode.
DB_PASSWORD=password   #
DB_DATABASE=my-db      #
DB_HOST=host.com       #
```
Example usage (Python):
```python
import os
db_user = os.environ.get("DB_USERNAME")
db_pass = os.environ.get("DB_PASSWORD")
db_name = os.environ.get("DB_DATABASE")
db_host = os.environ.get("DB_HOST")
db_port = os.environ.get("DB_PORT", 3306)  # Optional
```

---

# Logging: Critical for Debugging and Operations

**Proper logging isn't optional, it's essential.** Without it, debugging production issues becomes guesswork.

## Why Logging Matters
- **Deployment Issues:** When containers fail to start, logs show exactly what's blocking (database connections, missing env vars, syntax errors)
- **Runtime Errors:** Track down crashes, performance bottlenecks, and user-reported bugs with precise error traces
- **Security & Monitoring:** Detect suspicious activity, track user actions, and monitor system health
- **Debugging Speed:** Hours of guesswork become minutes of targeted fixes when you can see what's actually happening

## What to Log (At Minimum)
```python
import logging
logger = logging.getLogger(__name__)

# Application lifecycle
logger.info("Application starting...")
logger.info("Database connection established")
logger.error("Failed to connect to external API: {error}")

# User actions
logger.info(f"User {user_id} logged in from {ip_address}")
logger.warning(f"Failed login attempt for {username}")

# System events
logger.info(f"Processing {count} items in queue")
logger.error(f"Payment processing failed: {transaction_id}")
```

## Production Logging Best Practices
- **Use structured logging** with consistent formats
- **Include timestamps, request IDs, and user context**
- **Log errors with full stack traces**
- **Never log sensitive data** (passwords, tokens, personal info)
- **Use appropriate log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)

**Bottom line:** If you can't see what your app is doing, you can't fix it when it breaks.

---

# Best Practices
Branching:
 Use main for development, merge to release to deploy, then sync back to main once you have a stable build.

### Security:
 Never commit secrets. Do not hardcode sensitive values in your codebase. Such as admin users, API keys, or database credentials.


# Need Help?
If issues arise, you need architecture guidance, or have questions about microservices, variables, deployments, database setup, or adding components:
- Review pipeline/application logs.
- Contact your professor or a WhitCloud admin (ntibbetts26@my.whitworth.edu / nictibbs97@live.com, cstrand26@my.whitworth.edu, kjones@whitworth.edu).



---

***Note:***

*This README is intentionally generic for any WhitCloud project. If you need specifics for your app or tech stack, reach out for guidance.*

---


