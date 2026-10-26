# ServiceBoard

A small REST API built with Python, Flask, and SQLite.

ServiceBoard is a learning project created to explore Python web development, REST API design, and database integration. It provides a simple API for storing and retrieving information about web services.

This is an experimental project intended for learning, not production use.

## Features

- REST API built with Flask
- SQLite database for persistent storage
- Retrieve all services
- Retrieve a service by ID
- Create new services
- Basic request validation and HTTP error responses
- Simple separation between API routes and database operations

## Technology Stack

- **Python** — Application language
- **Flask** — Web framework
- **SQLite** — Database (using Python's built-in `sqlite3` module)

## Getting Started

### Prerequisites

- Python 3
- pip

### Installation

Clone the repository:

```bash
git clone https://github.com/JoyfulReaper/ServiceBoard.git
cd ServiceBoard
```

Create a virtual environment:

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

Install Flask:

```bash
python -m pip install Flask
```

### Running the Application

Start the Flask development server:

```bash
python -m flask --app app run --debug
```

The API will be available at:

`http://127.0.0.1:5000`

The SQLite database (`data.db`) is automatically initialized in the current working directory when the application starts.

The Flask development server is intended for local development only.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Basic welcome message |
| GET | `/services` | Retrieve all services |
| GET | `/services/<id>` | Retrieve a service by ID |
| POST | `/services` | Create a new service |

### Example: Retrieve All Services

```http
GET /services
```

Response:

```json
[
  {
    "id": 1,
    "name": "Example Service",
    "url": "https://example.com"
  }
]
```

### Example: Create a Service

```http
POST /services
Content-Type: application/json
```

Request body:

```json
{
  "name": "Example Service",
  "url": "https://example.com"
}
```

A successful request returns HTTP `201 Created` with the newly created service, including its generated ID.

### Error Handling

The API currently handles some common errors:

- `400 Bad Request` — Invalid request data or missing required values
- `404 Not Found` — Requested service does not exist

## Project Structure

```text
ServiceBoard/
├── app.py          # Flask application and API routes
├── database.py     # SQLite operations
├── .gitignore
├── LICENSE
└── README.md
```

`data.db` is generated at runtime.

## Current Limitations

ServiceBoard is still an early learning project.

It currently does not include:

- Update or delete endpoints
- Authentication or authorization
- Automated tests
- A web frontend
- Comprehensive input validation
- Production deployment configuration

## License

ServiceBoard is licensed under the MIT License. See [LICENSE](LICENSE) for details.