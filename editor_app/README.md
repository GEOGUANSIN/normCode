# NormCode Editor

The `editor_app` is a web-based IDE for creating, visualizing, and debugging NormCode plans. It provides a rich, interactive interface for managing "repository sets," which are collections of concepts and inferences that form the building blocks of a NormCode plan.

This application is composed of two main parts:
- A **FastAPI backend** that serves the API for managing and executing NormCode repositories.
- A **React frontend** that provides the user interface for interacting with the backend.

## Architecture

The editor operates on a client-server model:
- The **React frontend** is a single-page application that runs in the browser, providing a dynamic and responsive UI.
- The **FastAPI backend** exposes a RESTful API that the frontend consumes to manage data and trigger NormCode plan executions. All data is stored in the `editor_app/data` directory.

For more detailed information on each component, please refer to their respective README files:
- [Frontend README](frontend/README.md)
- [Backend README](backend/README.md)

## Getting Started

Follow these steps to set up and run the entire NormCode Editor application.

### 1. Backend Setup (FastAPI)

First, set up the Python environment and install the required dependencies for the backend.

1.  **Navigate to the backend directory:**
    ```powershell
    cd editor_app/backend
    ```

2.  **Create and activate a Python virtual environment:**
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```

### 2. Frontend Setup (React)

Next, set up the Node.js environment and install the dependencies for the frontend.

1.  **Navigate to the frontend directory:**
    ```powershell
    cd editor_app/frontend
    ```

2.  **Install the npm dependencies:**
    ```powershell
    npm install
    ```

## Running the Application

To run the editor, you will need to start both the backend and frontend servers. It is recommended to run them in separate terminals.

### 1. Run the Backend Server

-   In a terminal from the `editor_app/backend` directory (with the virtual environment activated), run the following command:
    ```powershell
    uvicorn main:app --reload --port 8001
    ```
-   The backend API will be running at `http://127.0.0.1:8001`.

### 2. Run the Frontend Server

-   In a second terminal, from the `editor_app/frontend` directory, run the following command:
    ```powershell
    npm run dev
    ```
-   The frontend application will be available at `http://localhost:5173`. The Vite development server will automatically proxy API requests to the backend.

Once both servers are running, you can access the NormCode Editor by opening `http://localhost:5173` in your web browser.
