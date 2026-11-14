# ServiceBoard

ServiceBoard is a small Python and Flask application for tracking self-hosted services, their hosts, and runtime versions.

It provides a public service directory, an authenticated REST API, and a password-protected administrative web interface.

ServiceBoard is a personal learning project created to explore Python, Flask, SQLite, REST API development, authentication, and web application design.

**Status:** Experimental. Not currently intended for production use.

## Features

- Public web page listing services and their URLs
- REST API for creating, reading, updating, and deleting services
- Bearer-token authentication for API write operations
- Public API responses that hide host and runtime information
- Authenticated API responses containing full service information
- Password-protected administrative web interface
- CSRF protection for administrative forms
- SQLite database for persistent storage
- Automatic database schema migrations
- Configurable SQLite database path
- Service host and runtime version tracking
- Shared validation for API requests and administrative forms
- Automated tests using pytest

## Technology Stack

- **Python** — Application language
- **Flask** — Web framework
- **SQLite** — Database
- **Flask-WTF** — CSRF protection
- **Werkzeug** — Password hashing and verification
- **python-dotenv** — Environment variable configuration
- **pytest** — Automated testing

## Requirements

- Python 3.10 or newer
- pip
- A virtual environment is recommended

ServiceBoard is currently developed and tested using Python 3.14.

Other Python versions have not been extensively tested.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/JoyfulReaper/ServiceBoard.git
cd ServiceBoard
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment.

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

For development:

```bash
python -m pip install -r requirements-dev.txt
```

This installs the application dependencies and pytest.

For a runtime-only installation:

```bash
python -m pip install -r requirements.txt
```

The project uses two dependency files:

- `requirements.txt` — Dependencies required to run ServiceBoard
- `requirements-dev.txt` — Development dependencies, including pytest

Direct dependencies are pinned to versions tested during development.

## Configuration

ServiceBoard uses environment variables for authentication, session configuration, and database settings.

For local development, these can be stored in a `.env` file in the repository root.

The `.env` file is excluded from Git and must not be committed.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SERVICEBOARD_SECRET_KEY` | Yes | Secret used to sign Flask session cookies |
| `SERVICEBOARD_ADMIN_PASSWORD_HASH` | Yes | Hashed password for the administrator |
| `SERVICEBOARD_API_KEY` | Yes | Bearer token used for API authentication |
| `SERVICEBOARD_DATABASE_PATH` | No | Absolute path to an existing SQLite database |
| `SERVICEBOARD_ALLOW_INSECURE_COOKIES` | No | Set to `1` to allow session cookies over HTTP during local development |

### Example `.env`

```dotenv
SERVICEBOARD_SECRET_KEY=REPLACE_WITH_RANDOM_SECRET
SERVICEBOARD_ADMIN_PASSWORD_HASH=REPLACE_WITH_PASSWORD_HASH
SERVICEBOARD_API_KEY=REPLACE_WITH_DIFFERENT_RANDOM_KEY

# Local HTTP development only
SERVICEBOARD_ALLOW_INSECURE_COOKIES=1

# Optional: absolute path to an existing database
# SERVICEBOARD_DATABASE_PATH=C:/GitHub/ServiceBoard/data.db
```

Replace the placeholder values before starting ServiceBoard.

Do not reuse the same value for the session secret and API key.

### Generate Random Secrets

Python's `secrets` module can generate cryptographically secure random values.

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Run this command separately to generate values for:

- `SERVICEBOARD_SECRET_KEY`
- `SERVICEBOARD_API_KEY`

Keep both values private.

### Generate the Administrator Password Hash

ServiceBoard stores a password hash rather than a plaintext administrator password.

Generate a hash using Werkzeug:

```bash
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Admin password: ')))"
```

Enter the desired administrator password when prompted.

Copy the resulting hash into:

```dotenv
SERVICEBOARD_ADMIN_PASSWORD_HASH=YOUR_GENERATED_HASH
```

The administrator currently uses a single password. There is no user registration or multi-user account system.

### Session Cookies

Session cookies are configured with:

- `HttpOnly`
- `SameSite=Lax`
- `Secure` enabled by default
- An eight-hour permanent session lifetime

For local development over plain HTTP, set:

```dotenv
SERVICEBOARD_ALLOW_INSECURE_COOKIES=1
```

**Do not enable insecure cookies on a public deployment.**

Public deployments should use HTTPS and secure session cookies.

## Database Configuration

ServiceBoard uses SQLite for persistent storage.

By default, the database is located at:

```text
data.db
```

This path is relative to the application's current working directory.

The database and required tables are initialized automatically when the application starts.

### Configuring an Absolute Database Path

To use a specific database location, configure:

```dotenv
SERVICEBOARD_DATABASE_PATH=C:/GitHub/ServiceBoard/data.db
```

Linux example:

```dotenv
SERVICEBOARD_DATABASE_PATH=/var/lib/serviceboard/data.db
```

When `SERVICEBOARD_DATABASE_PATH` is configured:

1. The path must be absolute.
2. The database file must already exist.
3. ServiceBoard raises an error if the file does not exist.

These checks help prevent an incorrect path from silently creating a new, empty database.

If the variable is not configured, ServiceBoard continues to use the default `data.db` path.

### Database Migrations

ServiceBoard performs simple schema migrations during initialization.

Existing databases created with older versions are updated to include newer columns.

Migrations are designed to preserve existing service records.

The current service model includes:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | INTEGER | Yes | Unique service identifier |
| `name` | TEXT | Yes | Service name |
| `url` | TEXT | Yes | Service URL |
| `host` | TEXT | No | VPS or host running the service |
| `runtime_name` | TEXT | No | Runtime or framework name |
| `runtime_version` | TEXT | No | Runtime or framework version |

A runtime version requires a runtime name.

Example:

```json
{
    "id": 1,
    "name": "Packet Garden",
    "url": "https://garden.kgivler.com",
    "host": "FrontDesk",
    "runtime_name": "Microsoft.AspNetCore.App",
    "runtime_version": "10.0.15"
}
```

Currently, each service can have one runtime name and version.

Support for multiple runtimes per service may be added in the future.

## Running ServiceBoard

Start the Flask development server from the repository root:

```bash
python -m flask --app src.serviceboard.app run --debug
```

The application will be available at:

http://127.0.0.1:5000

Available pages include:

| URL | Description |
|---|---|
| `/` | Public service directory |
| `/login` | Administrator login |
| `/admin` | Administrative dashboard |
| `/services` | Services REST API |

When using Flask's CLI with python-dotenv installed, environment variables from `.env` are loaded automatically.

Other application servers may require environment variables to be configured separately.

**Important:** Flask's development server and interactive debugger must not be exposed publicly.

A production deployment should use an appropriate WSGI server and HTTPS.

See the [Flask deployment documentation](https://flask.palletsprojects.com/en/stable/deploying/).

## REST API

ServiceBoard provides a JSON REST API for managing services.

### API Endpoints

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| GET | `/services` | Optional | Retrieve all services |
| GET | `/services/<id>` | Optional | Retrieve a service by ID |
| POST | `/services` | Bearer token | Create a service |
| PUT | `/services/<id>` | Bearer token | Update a service |
| DELETE | `/services/<id>` | Bearer token | Delete a service |

### Authentication

API write operations require a bearer token.

Include the following HTTP header:

```http
Authorization: Bearer YOUR_API_KEY
```

The token must match the configured `SERVICEBOARD_API_KEY`.

Missing or invalid credentials on protected endpoints return HTTP 401 Unauthorized.

### Public and Authenticated Responses

GET requests can be made without authentication.

Public responses contain only:

- `id`
- `name`
- `url`

Host and runtime information is excluded from public responses.

For example:

```http
GET /services
```

Response:

```json
[
    {
        "id": 1,
        "name": "Packet Garden",
        "url": "https://garden.kgivler.com"
    }
]
```

Providing a valid bearer token returns the complete service information:

```http
GET /services
Authorization: Bearer YOUR_API_KEY
```

Response:

```json
[
    {
        "id": 1,
        "name": "Packet Garden",
        "url": "https://garden.kgivler.com",
        "host": "FrontDesk",
        "runtime_name": "Microsoft.AspNetCore.App",
        "runtime_version": "10.0.15"
    }
]
```

Requests containing an invalid bearer token return HTTP 401 rather than falling back to the public response.

Successful service-read responses include `Cache-Control: no-store`.

### Create a Service

Endpoint:

```http
POST /services
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

Example request body:

```json
{
    "name": "Packet Garden",
    "url": "https://garden.kgivler.com",
    "host": "FrontDesk",
    "runtime_name": "Microsoft.AspNetCore.App",
    "runtime_version": "10.0.15"
}
```

Required fields:

- `name`
- `url`

Optional fields:

- `host`
- `runtime_name`
- `runtime_version`

A successful request returns HTTP 201 Created with the newly created service, including its assigned ID.

### Update a Service

Endpoint:

```http
PUT /services/1
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

Example request:

```json
{
    "name": "Packet Garden",
    "url": "https://garden.kgivler.com",
    "host": "DeepDish",
    "runtime_name": "Microsoft.AspNetCore.App",
    "runtime_version": "10.0.16"
}
```

A successful update returns HTTP 200 with the updated service.

PUT requires both `name` and `url`.

Optional fields omitted from the request are set to `null`.

If the service does not exist, the API returns HTTP 404.

### Delete a Service

Endpoint:

```http
DELETE /services/1
Authorization: Bearer YOUR_API_KEY
```

A successful deletion returns:

```http
204 No Content
```

The response body is empty.

Deleting a nonexistent service returns HTTP 404.

### Validation

ServiceBoard validates incoming data before modifying the database.

Current validation rules include:

- Requests must contain valid JSON objects.
- Service names must be strings.
- Service URLs must be strings.
- Names and URLs cannot be empty or whitespace-only.
- Optional fields must contain strings or `null`.
- Empty optional strings are normalized to `null`.
- A runtime version cannot be provided without a runtime name.

Validation errors return HTTP 400 with an error message.

Example:

```json
{
    "error": "Runtime name required when runtime version is provided"
}
```

URL scheme validation, field-length limits, and additional input restrictions may be added later.

## Administrative Web Interface

ServiceBoard includes a password-protected administrative interface.

Visit:

http://127.0.0.1:5000/login

After logging in, the administrator can:

- View all services
- View host and runtime information
- Create services
- Edit existing services
- Delete services using a confirmation page
- Log out

Administrative forms use CSRF tokens to protect against cross-site request forgery.

The administrative interface uses Flask session-cookie authentication.

The REST API uses bearer-token authentication.

These authentication mechanisms are separate.

### Administrative Routes

| Method | Endpoint | Description |
|---|---|---|
| GET | `/login` | Display login form |
| POST | `/login` | Authenticate administrator |
| GET | `/admin` | Display admin dashboard |
| POST | `/admin/services` | Create service |
| GET | `/admin/services/<id>/edit` | Display edit form |
| POST | `/admin/services/<id>/edit` | Update service |
| GET | `/admin/services/<id>/delete` | Display delete confirmation |
| POST | `/admin/services/<id>/delete` | Delete service |
| POST | `/logout` | End administrator session |

There is currently one administrator password and no account-management system.

## Testing

ServiceBoard uses pytest for automated testing.

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run all tests:

```bash
python -m pytest
```

Run with verbose output:

```bash
python -m pytest -v
```

Or use the quieter output format:

```bash
python -m pytest -q
```

### Test Coverage

The tests currently cover:

**Database operations**

- Creating services
- Retrieving services
- Updating services
- Deleting services
- Handling nonexistent services
- Database schema migrations
- Preserving existing records during initialization
- Configurable database paths
- Rejecting nonexistent configured database paths

**REST API**

- Public service responses
- Authenticated service responses
- Invalid bearer tokens
- Authenticated CRUD operations
- Unauthorized modification attempts
- Request validation

**Administrative interface**

- Access restrictions
- Successful login
- Incorrect passwords
- CSRF protection
- Session persistence
- Logout
- Creating services
- Editing services
- Deleting services
- Validation failures

Tests use temporary SQLite databases to avoid modifying the application's actual database.

## Project Structure

```text
ServiceBoard/
├── .gitignore
├── .env                       # Local configuration (not tracked)
├── .venv/                     # Virtual environment (not tracked)
├── data.db                    # Default SQLite database (not tracked)
├── LICENSE
├── README.md
├── requirements.txt
├── requirements-dev.txt
│
├── src/
│   └── serviceboard/
│       ├── __init__.py
│       ├── app.py             # Flask routes and validation
│       ├── auth.py            # Authentication decorators
│       ├── database.py        # SQLite operations
│       │
│       └── templates/
│           ├── index.html
│           ├── login.html
│           ├── admin.html
│           ├── edit_service.html
│           └── delete_service.html
│
└── tests/
    ├── conftest.py            # Test fixtures
    ├── test_database.py
    ├── test_api.py
    └── test_admin.py
```

## Current Limitations

ServiceBoard is still an experimental learning project.

Current limitations include:

- Single administrator password
- No multi-user account management
- No login rate limiting
- One runtime per service
- No automated vulnerability checking
- No automatic discovery of services
- No service health monitoring
- Limited URL and input validation
- Basic HTML interface without significant styling
- No production deployment configuration

These limitations may be addressed as development continues.

## Roadmap

Potential future improvements include:

### Service Deployment Types

Track how each service is deployed or managed.

Possible values include:

- Docker
- systemd
- Manual/Other

A future `deployment_type` field could help distinguish containerized services from services managed directly by the operating system.

### Runtime Tracking Improvements

- Support multiple runtimes per service
- Improve runtime name and version handling
- Identify outdated runtime versions
- Integrate runtime vulnerability advisories
- Display vulnerability information in the admin interface

### Administrative Interface

- Improve styling and layout
- Add filtering and sorting
- Group services by host
- Group services by deployment type
- Improve validation messages

### Infrastructure Integration

- Optional integration with service discovery tools
- Import service information from existing infrastructure
- Investigate Docker and systemd service discovery
- Optional integration with monitoring systems

### Security and Reliability

- Add login rate limiting
- Improve input validation
- Add database backup documentation
- Document production deployment
- Expand automated testing as new features are introduced

The roadmap is tentative and may change as the project evolves.

## License

ServiceBoard is licensed under the MIT License.

See [LICENSE](LICENSE) for details.