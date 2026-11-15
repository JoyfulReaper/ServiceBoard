# ServiceBoard

ServiceBoard is a small Python and Flask application for tracking self-hosted services, their hosts, deployment methods, and runtime versions.

It provides:

- A public directory of services
- A private administrative interface
- An authenticated REST API
- SQLite persistence
- Public/private visibility controls
- Sorting and filtering of registered services

ServiceBoard is a personal learning project created to explore Python, Flask, SQLite, REST APIs, authentication, database migrations, automated testing, and web application development.

**Status:** Experimental. Not currently intended for production use.

## Features

### Service Management

- Create, view, update, and delete services
- Store service names, URLs, and descriptions
- Track the VPS or host running each service
- Track deployment methods such as Docker and systemd
- Record runtime names and versions
- Configure services as public or private
- Preserve existing service records during database migrations

### Public Directory

- Responsive, dark-themed service directory
- Service cards displaying names, URLs, and descriptions
- Only publicly visible services are displayed
- Private infrastructure metadata is excluded
- Empty-state message when no public services exist

### Administrative Interface

- Password-protected administration
- Create, edit, and delete services
- Public/private visibility checkbox
- Public and Private status badges
- Delete confirmation page
- Shared responsive layout and styling
- CSRF protection for administrative forms
- Session-based authentication

The service listing supports sorting by:

- Service name
- Host
- Deployment type
- Runtime

Services can be filtered by:

- Public/private visibility
- Host
- Deployment type
- Runtime

Filters can be combined.

Filter options are generated from existing service records.

The administrative interface distinguishes between an empty database and filters that produce no matching services.

### REST API

- JSON endpoints for service management
- Bearer-token authentication for write operations
- Optional authentication for read operations
- Public responses containing only approved fields
- Authenticated access to private services and metadata
- Request validation and appropriate HTTP status codes
- Protection against unauthorized modifications

### Persistence and Testing

- SQLite database
- Automatic schema initialization and migrations
- Configurable database location
- Existing data preserved during supported migrations
- Automated tests using pytest
- Isolated temporary databases for tests

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application language |
| Flask | Web framework and routing |
| SQLite | Persistent data storage |
| Jinja2 | HTML templates |
| Flask-WTF | CSRF protection |
| Werkzeug | Password hashing and authentication utilities |
| python-dotenv | Local environment configuration |
| pytest | Automated testing |

The application uses Python's built-in `sqlite3` module rather than an ORM.

This is intentional: ServiceBoard is also an opportunity to learn SQL and database access directly.

## Requirements

- Python 3.10 or newer
- pip
- A Python virtual environment is recommended

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

Activate the environment.

Windows PowerShell:

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

- `requirements.txt` contains runtime dependencies.
- `requirements-dev.txt` includes runtime dependencies and development tools.

Dependencies are pinned to versions tested during development.

## Configuration

ServiceBoard uses environment variables for authentication, session configuration, and database settings.

For local development, these can be stored in a `.env` file in the repository root.

**Never commit `.env` or actual credentials to Git.**

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SERVICEBOARD_SECRET_KEY` | Yes | Secret used to sign Flask session cookies |
| `SERVICEBOARD_ADMIN_PASSWORD_HASH` | Yes | Hashed administrator password |
| `SERVICEBOARD_API_KEY` | Yes | Bearer token for API authentication |
| `SERVICEBOARD_DATABASE_PATH` | No | Absolute path to an existing SQLite database |
| `SERVICEBOARD_ALLOW_INSECURE_COOKIES` | No | Set to `1` for local HTTP development |

### Example `.env`

```dotenv
SERVICEBOARD_SECRET_KEY=REPLACE_WITH_RANDOM_SECRET
SERVICEBOARD_ADMIN_PASSWORD_HASH=REPLACE_WITH_PASSWORD_HASH
SERVICEBOARD_API_KEY=REPLACE_WITH_DIFFERENT_RANDOM_KEY

# Local HTTP development only
SERVICEBOARD_ALLOW_INSECURE_COOKIES=1

# Optional: absolute path to an existing SQLite database
# SERVICEBOARD_DATABASE_PATH=C:/GitHub/ServiceBoard/data.db
```

Replace the placeholder values before starting ServiceBoard.

Do not reuse the same secret for session signing and API authentication.

### Generate Random Secrets

Python's `secrets` module can generate cryptographically secure random values.

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Run this separately to generate values for:

- `SERVICEBOARD_SECRET_KEY`
- `SERVICEBOARD_API_KEY`

Keep both values private.

### Generate the Administrator Password Hash

ServiceBoard stores a password hash rather than a plaintext administrator password.

Generate a hash using Werkzeug:

```bash
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Admin password: ')))"
```

Enter the administrator password when prompted.

Copy the resulting hash into:

```dotenv
SERVICEBOARD_ADMIN_PASSWORD_HASH=YOUR_GENERATED_HASH
```

ServiceBoard currently supports one administrator password.

There is no user registration or multi-user account system.

### Session Cookies

Administrative sessions use Flask's signed session cookies.

Session configuration includes:

- `HttpOnly` cookies
- `SameSite=Lax`
- `Secure` cookies enabled by default
- An eight-hour permanent session lifetime

For local development over HTTP:

```dotenv
SERVICEBOARD_ALLOW_INSECURE_COOKIES=1
```

**Do not enable insecure cookies on a public deployment.**

Public deployments should use HTTPS and secure session cookies.

## Database

ServiceBoard uses SQLite for persistent storage.

By default, the database is located at:

```text
data.db
```

This path is relative to the application's current working directory.

The database and required tables are initialized automatically when the application starts.

### Configuring a Database Path

Set:

```dotenv
SERVICEBOARD_DATABASE_PATH=C:/GitHub/ServiceBoard/data.db
```

Linux example:

```dotenv
SERVICEBOARD_DATABASE_PATH=/var/lib/serviceboard/data.db
```

When a custom database path is configured:

1. The path must be absolute.
2. The database file must already exist.
3. ServiceBoard raises an error if the file does not exist.

These checks prevent an incorrect configured path from silently creating a new, empty database.

When no custom path is configured, ServiceBoard uses the default `data.db`.

### Service Model

The `services` table contains:

| Field | SQLite Type | Required | Description |
|---|---|---|---|
| `id` | INTEGER | Yes | Unique service identifier |
| `name` | TEXT | Yes | Service name |
| `url` | TEXT | Yes | Service URL |
| `description` | TEXT | No | Description of the service |
| `host` | TEXT | No | VPS or host running the service |
| `deployment_type` | TEXT | No | Deployment method |
| `runtime_name` | TEXT | No | Runtime or framework name |
| `runtime_version` | TEXT | No | Runtime or framework version |
| `is_public` | INTEGER | Yes | Public/private visibility |

SQLite stores visibility as an integer:

- `1` = Public
- `0` = Private

The `is_public` column is defined as:

```sql
is_public INTEGER NOT NULL DEFAULT 1
```

New services default to public unless otherwise specified.

A runtime version requires a runtime name.

### Example Service

An authenticated API response might contain:

```json
{
    "id": 1,
    "name": "SmolSearch",
    "url": "https://search.example.com",
    "description": "A search engine for the small web",
    "host": "Clanker",
    "deployment_type": "docker",
    "runtime_name": "Microsoft.AspNetCore.App",
    "runtime_version": "10.0.15",
    "is_public": true
}
```

Currently, each service can have one runtime name and version.

Support for multiple runtimes per service may be added in the future.

### Database Migrations

ServiceBoard performs simple schema migrations during initialization.

Existing databases created with older versions are updated to include missing columns.

Supported migrations preserve existing service records.

When migrating an older database that does not contain `is_public`, existing services default to public.

Previously configured visibility values are preserved during subsequent initialization.

Migrations are covered by automated tests.

These migrations are intentionally simple and do not use a separate migration framework.

## Running ServiceBoard

Start the Flask development server from the repository root:

```bash
python -m flask --app src.serviceboard.app run --debug
```

The application will be available at:

http://127.0.0.1:5000

### Available Pages

| URL | Description |
|---|---|
| `/` | Public service directory |
| `/login` | Administrator login |
| `/admin` | Administrative dashboard |
| `/services` | Services REST API |
| `/services/<id>` | Individual service API |
| `/admin/services/<id>/edit` | Edit a service |
| `/admin/services/<id>/delete` | Delete confirmation |

Administrative pages require authentication.

When using Flask's CLI with python-dotenv installed, environment variables from `.env` are loaded automatically.

Other application servers may require environment variables to be configured separately.

**Important:** Flask's development server and interactive debugger must not be exposed publicly.

Production deployments should use an appropriate WSGI server and HTTPS.

See the [Flask deployment documentation](https://flask.palletsprojects.com/en/stable/deploying/).

## Public Service Directory

The homepage displays services configured as public.

Each public service card may contain:

- Service name
- Description
- URL

The public directory does not display:

- Host information
- Deployment type
- Runtime name
- Runtime version
- Private services

Service visibility is controlled through the administrative interface or authenticated API.

A service marked private remains in the database and administrative interface but is excluded from the public directory.

## REST API

ServiceBoard provides a JSON REST API for managing services.

### API Endpoints

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| GET | `/services` | Optional | List visible services |
| GET | `/services/<id>` | Optional | Retrieve an individual service |
| POST | `/services` | Bearer token | Create a service |
| PUT | `/services/<id>` | Bearer token | Update a service |
| DELETE | `/services/<id>` | Bearer token | Delete a service |

### Authentication

API authentication uses a bearer token.

Include:

```http
Authorization: Bearer YOUR_API_KEY
```

The token must match `SERVICEBOARD_API_KEY`.

ServiceBoard uses constant-time comparison when validating API credentials.

API write operations require authentication.

Read operations support both anonymous and authenticated requests.

Requests containing an invalid bearer token return HTTP 401 rather than falling back to anonymous access.

Protected endpoints also return HTTP 401 for missing or invalid credentials.

The administrative web interface uses separate session-cookie authentication.

### Public API Responses

Anonymous requests can retrieve public services.

For example:

```http
GET /services
```

Response:

```json
[
    {
        "id": 1,
        "name": "SmolSearch",
        "url": "https://search.example.com",
        "description": "A search engine for the small web"
    }
]
```

Public API responses contain only:

- `id`
- `name`
- `url`
- `description`

Private fields are excluded.

Private services are also excluded entirely.

### Private Service Access

An unauthenticated request for a private service returns HTTP 404:

```http
GET /services/2
```

Response:

```json
{
    "error": "Service not found"
}
```

This prevents anonymous callers from retrieving private service details by guessing IDs.

The private service still exists and remains available to authorized clients.

### Authenticated API Responses

Providing a valid bearer token allows access to all services, including private ones.

```http
GET /services
Authorization: Bearer YOUR_API_KEY
```

Authenticated responses include the complete service information.

For example:

```json
[
    {
        "id": 2,
        "name": "Internal Dashboard",
        "url": "https://internal.example.com",
        "description": "Infrastructure administration dashboard",
        "host": "DeepDish",
        "deployment_type": "systemd",
        "runtime_name": "Microsoft.AspNetCore.App",
        "runtime_version": "10.0.15",
        "is_public": false
    }
]
```

Successful service-read responses include:

```http
Cache-Control: no-store
```

### Create a Service

Endpoint:

```http
POST /services
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

Example request:

```json
{
    "name": "Packet Garden",
    "url": "https://garden.kgivler.com",
    "description": "An interactive network visualization",
    "host": "Clanker",
    "deployment_type": "docker",
    "runtime_name": "Microsoft.AspNetCore.App",
    "runtime_version": "10.0.15",
    "is_public": true
}
```

Required fields:

- `name`
- `url`

Optional fields:

- `description`
- `host`
- `deployment_type`
- `runtime_name`
- `runtime_version`
- `is_public`

When omitted during creation, `is_public` defaults to `true`.

A successful request returns HTTP 201 Created with the new service, including its assigned ID.

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
    "description": "Updated description",
    "host": "DeepDish",
    "deployment_type": "systemd",
    "runtime_name": "Microsoft.AspNetCore.App",
    "runtime_version": "10.0.15",
    "is_public": false
}
```

PUT requires both `name` and `url`.

Optional text fields omitted from the request are set to `null`.

**Visibility behaves differently:**

- `is_public: true` makes the service public.
- `is_public: false` makes the service private.
- Omitting `is_public` preserves the existing visibility.

A successful update returns HTTP 200.

Updating a nonexistent service returns HTTP 404.

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

Deleting a ServiceBoard record does not stop, restart, or delete the underlying service.

### Validation

ServiceBoard validates incoming data before modifying the database.

Current validation rules include:

- Requests must contain valid JSON objects.
- Service names must be strings.
- Service URLs must be strings.
- Names and URLs cannot be empty or whitespace-only.
- Optional text fields must contain strings or `null`.
- Empty optional strings are normalized to `null`.
- Runtime versions require a runtime name.
- `is_public`, when provided, must be a JSON Boolean.

Valid:

```json
{
    "is_public": false
}
```

Invalid:

```json
{
    "is_public": "false"
}
```

Validation failures return HTTP 400 with an error message.

Example:

```json
{
    "error": "Runtime name required when runtime version is provided"
}
```

URL scheme validation, field-length limits, and additional input restrictions are not yet implemented.

## Administrative Web Interface

ServiceBoard includes a password-protected administrative interface.

Visit:

http://127.0.0.1:5000/login

After logging in, the administrator can:

- View all registered services
- Create new services
- Edit existing services
- Delete services through a confirmation page
- View private infrastructure metadata
- Change service visibility
- Sort and filter services
- Log out

### Public and Private Services

The Create and Edit forms include a **Show publicly** checkbox.

When creating a service, the checkbox is checked by default.

When editing a service, the checkbox reflects its stored visibility.

Unchecking the box makes the service private.

The administrative listing displays Public and Private badges.

Private services remain visible to the administrator.

### Sorting

The administrative listing can be sorted by:

- Name
- Host
- Deployment type
- Runtime

Sorting is performed after filtering.

### Filtering

The administrative interface supports filtering by:

- Visibility: All, Public, or Private
- Host
- Deployment type
- Runtime

Multiple filters can be applied simultaneously.

For example:

```text
/admin?host=Clanker&deployment=docker&visibility=private
```

This displays private Docker services registered on Clanker.

Host, deployment, and runtime options are generated from existing service records.

Selected filters are preserved in the dropdowns.

Invalid filter values fall back to their default selections.

Filtering is currently performed in Python after retrieving the service records from SQLite.

This approach is sufficient for the application's intended small-scale use.

### Empty States

The administrative interface distinguishes between:

- No services registered
- No services matching the selected filters

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

Administrative forms use CSRF tokens.

Unauthenticated attempts to access protected administrative pages are redirected to the login page.

The administrative interface uses Flask session-cookie authentication.

The REST API uses bearer-token authentication.

These mechanisms are separate.

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

Or use quiet output:

```bash
python -m pytest -q
```

### Test Coverage

Tests cover the following areas.

#### Database

- Creating services
- Retrieving services
- Updating services
- Deleting services
- Handling nonexistent services
- Schema migrations
- Preserving existing records
- Custom database paths
- Rejecting invalid database paths
- Service descriptions
- Deployment types
- Public/private visibility
- Preserving visibility during updates

#### REST API

- Public service responses
- Authenticated service responses
- Private service access restrictions
- Invalid bearer tokens
- Authenticated CRUD operations
- Unauthorized modification attempts
- Request validation
- Invalid visibility values
- Preserving visibility during updates
- Correct HTTP response codes

#### Administrative Interface

- Authentication requirements
- Successful login
- Incorrect passwords
- CSRF protection
- Session handling
- Logout
- Creating services
- Editing services
- Deleting services
- Public/private visibility controls
- Visibility badges
- Shared page layouts
- Host filtering
- Deployment-type filtering
- Runtime filtering
- Visibility filtering
- Combined filters
- Sorting
- Empty-state messages
- Validation-error rendering

Tests use temporary SQLite databases to avoid modifying the application's actual database.

The Flask test client verifies routes, HTTP responses, authentication behavior, and generated HTML.

Visual layout should also be checked manually in a browser.

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
│       ├── app.py             # Flask routes, validation, and admin filtering
│       ├── auth.py            # Authentication helpers and decorators
│       ├── database.py        # SQLite operations and migrations
│       │
│       ├── static/
│       │   └── style.css     # Shared responsive styling
│       │
│       └── templates/
│           ├── base.html
│           ├── index.html
│           ├── login.html
│           ├── admin.html
│           ├── edit_service.html
│           └── delete_service.html
│
└── tests/
    ├── conftest.py
    ├── test_database.py
    ├── test_api.py
    └── test_admin.py
```

## Current Limitations

ServiceBoard remains an experimental learning project.

Current limitations include:

- Single administrator password
- No multi-user account management
- No login rate limiting
- Limited URL and input validation
- No enforced URL scheme allowlist
- No configurable field-length limits
- One runtime per service
- Free-form host and deployment names
- No API pagination
- No automated service discovery
- No service health monitoring
- No automatic vulnerability detection
- No container update scanning
- No production deployment configuration
- No documented automated database backup process

ServiceBoard does not currently verify whether registered services are running or whether their runtime versions are current.

It is primarily a service registry.

## Roadmap

The roadmap is tentative and may change as development continues.

### Service Metadata

- Support multiple runtimes per service
- Normalize host and deployment-type values
- Improve runtime name and version handling
- Add additional optional service metadata

### Runtime and Vulnerability Information

- Identify potentially outdated runtime versions
- Investigate runtime lifecycle information
- Explore vulnerability advisory integration
- Display relevant security information in the administrative interface

Automated vulnerability matching would require reliable package, runtime, and version identification. ServiceBoard does not currently perform that analysis.

### Administrative Improvements

- Improve form validation messages
- Preserve entered form values after validation failures
- Add additional administrative usability improvements
- Consider grouping services by host or deployment type

### Infrastructure Integration

- Investigate importing service information from existing infrastructure
- Explore Docker and systemd service discovery
- Consider optional integration with HappyDocker
- Avoid duplicating monitoring and scanning functionality already provided by other tools

### Security and Reliability

- Add login rate limiting
- Validate URL schemes and restrict unsafe URLs
- Add configurable input-length limits
- Improve database backup documentation
- Document production deployment requirements
- Expand automated testing
- Consider pagination if the service registry grows significantly

## Project Philosophy

ServiceBoard is intentionally small.

Its primary purpose is to provide a practical project for learning Python and Flask while maintaining a useful directory of self-hosted services.

The project favors:

- Straightforward Python code
- Minimal dependencies
- Explicit SQL and SQLite operations
- Small, understandable functions
- Automated tests
- Incremental development
- Practical features over unnecessary abstraction

The goal is to keep the application understandable and maintainable while learning how its components work.

## License

ServiceBoard is licensed under the MIT License.

See [LICENSE](LICENSE) for details.