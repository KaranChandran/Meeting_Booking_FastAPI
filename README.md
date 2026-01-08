##Meeting Booking FastAPI

A **simple Meeting Booking Management API** built with **FastAPI** and **SQLite**, designed to help users schedule meetings with **proper date and time validation**. It ensures meetings **cannot be booked in the past** or **outside working hours (08:00–20:00)** — perfect for a basic scheduler backend.

---

## Features

*  Schedule meetings with **date and time validation**
*  Prevent bookings in the past
*  Restrict booking times to **08:00–20:00**
*  Built with FastAPI (Python) and SQLite
*  Automatically generated API docs via Swagger/UI

---

## Table of Contents

* [Demo](#-demo)
* [Tech Stack](#-tech-stack)
* [Installation](#-installation)
* [Usage](#-usage)
* [API Endpoints](#-api-endpoints)
* [Testing](#-testing)
* [Contributing](#-contributing)
* [License](#-license)

---

## Demo

Once running locally, you can try out the interactive API docs:

* **Swagger UI** — `http://127.0.0.1:8000/docs`
* **Redoc** — `http://127.0.0.1:8000/redoc`

These interfaces let you test all API endpoints without external tools.

---

## Tech Stack

| Technology   | Purpose               |
| ------------ | --------------------- |
| **FastAPI**  | Backend web framework |
| **SQLite**   | Database              |
| **Python**   | Language              |
| **Pydantic** | Data validation       |
| **Uvicorn**  | ASGI server           |

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/KaranRavichandhiran/Meeting_Booking_FastAPI.git
   cd Meeting_Booking_FastAPI
   ```

2. **Create and activate Python virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   # venv\Scripts\activate    # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Start the FastAPI server**

   ```bash
   uvicorn app.main:app --reload
   ```

---

## Usage

With the server running, send HTTP requests to:

```
http://127.0.0.1:8000
```

Explore all endpoints interactively using Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## API Endpoints

| Method   | Path             | Description                  |
| -------- | ---------------- | ---------------------------- |
| `POST`   | `/bookings/`     | Create a new meeting booking |
| `GET`    | `/bookings/`     | List all bookings            |
| `GET`    | `/bookings/{id}` | Retrieve booking by ID       |
| `DELETE` | `/bookings/{id}` | Delete a specific booking    |

> *Note:* Endpoints may vary depending on how routes are defined in your app code.

---

## Testing

To run tests (if tests are included):

```bash
pytest
```

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a new branch (`feature/xyz`)
3. Make your changes
4. Create a Pull Request

---

## License

This project is open-source and available under the **MIT License** — feel free to use and customize it!
*(Add your LICENSE file if not already present)*

---
