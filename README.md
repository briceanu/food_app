🍃 FastAPI Auth & CRUD Project

A secure and scalable FastAPI project with:

- JWT-based authentication (access & refresh tokens)
- Logout with token blacklisting (via Redis)
- Full CRUD support
- SQLAlchemy ORM
- Pydantic for data validation
- Environment variable management
- Git version control

---

## 🚀 Features

- ✅ **JWT Authentication**: Access and refresh tokens using [PyJWT](https://pyjwt.readthedocs.io/)
- 🔐 **Token Blacklisting**: Redis used to store blacklisted tokens on logout
- 📦 **CRUD Operations**: Easily extendable base for database models
- 🧩 **SQLAlchemy**: ORM for defining and interacting with relational data
- 📜 **Pydantic Models**: For request/response validation and typing
- ⚙️ **Environment Variables**: Loaded securely with `python-dotenv`
- 🗃️ **Git**: Managed via `.gitignore` and committed with clean structure

---

## 🛠️ Tech Stack

- **FastAPI** – Web framework
- **SQLAlchemy** – ORM
- **Pydantic** – Data validation
- **Redis** – Token blacklisting
- **PostgreSQL/MySQL** – Default database (can be switched)
- **Uvicorn** – ASGI server
- **dotenv** – For environment variables
- **XSS** - Protection against cross site scripting

---
