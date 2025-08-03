# Warehouse Manager

A comprehensive web-based Warehouse Management System (WMS) designed to streamline inventory control, track stock movements, and generate insightful reports. This project showcases a full-stack application built with a Python/Flask backend, a MySQL database, and a dynamic, responsive frontend.

-----

### ✨ Key Features

This application provides a robust set of features for effective warehouse management:

  * **📦 Products Management:** Full CRUD (Create, Read, Update, Delete) functionality for products. Each product has a name, category, unit of measurement, storage location, and minimum stock level.
  * **📂 Category Management:** Organize products into custom categories, making filtering and management more intuitive.
  * **📊 Inventory Tracking:**
      * **Incoming Shipments:** Register the arrival of new stock, updating inventory levels automatically.
      * **Outgoing Shipments:** Record dispatches, with checks to prevent shipping more items than are available.
      * **Journal Operations Log:** A complete, filterable history of all stock movements (incoming/outgoing), including dates, quantities, and associated documents.
  * **🔍 Dynamic Filtering & Search:**
      * Quickly find products by name, category, or location.
      * Filter items that are in stock, out of stock, or below their minimum required level.
  * **📈 Advanced Reporting:**
      * **Current Stock Levels:** Get a complete overview of all items in the warehouse.
      * **Low Stock Alerts:** Instantly identify products that need to be reordered.
      * **Movement History:** Generate reports on all operations within a specific date range.
      * **Individual Product Ledger:** Track the complete movement history for a single product.
  * **📄 Export Functionality:**
      * Export any report to **CSV** for analysis in spreadsheet software.
      * Generate and download **PDF** versions of reports for printing or archiving.
  * **🔐 User Authentication:** A secure login system to protect access to the warehouse data.
  * **🚀 RESTful API:** A structured backend API that handles all data operations.

-----

### 🛠️ Tech Stack

This project leverages a modern and reliable technology stack:

  * **Backend:**
      * **Python 3**
      * **Flask** 
      * **MySQL Connector** 
      * **FPDF2** 
  * **Frontend:**
      * **HTML5**
      * **CSS3**
      * **Bootstrap**
      * **JavaScript** 
  * **Database:**
      * **MySQL**

-----

### 🚀 Getting Started

Follow these instructions to get a local copy of the project up and running for development and testing purposes.

#### Prerequisites

  * **Python 3.9** or newer.
  * **MySQL Server** installed and running.
  * `git` for cloning the repository.

#### Installation & Setup

1.  **Clone the repository:**

    ```sh
    git clone https://your-repository-url.git
    cd wms-back
    ```

2.  **Create and activate a virtual environment:**

      * On Windows:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```
      * On macOS/Linux:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install the required dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up the database:**
    a. Log in to your MySQL server and create a new database.

    ```sql
    CREATE DATABASE warehouse;
    ```

    b. **Configure database credentials.** Open the `bd_work.py` file and update the `get_db_connection` function with your MySQL host, user, and password.

    ```python
    # in bd_work.py
    connection = mysql.connector.connect(
        host='localhost',       # Your MySQL host
        database='warehouse',   # The database you created
        user='root',            # Your MySQL username
        password='YOUR_SECRET_PASSWORD' # Your MySQL password
    )
    ```

    c. **Create the database tables.** Run the provided debug script to automatically set up the required tables.

    ```sh
    python debugfunc.py
    ```

5.  **Run the Flask application:**

    ```sh
    flask run
    # Or for development mode:
    # python app.py
    ```

6.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:5000`.

      * **Login:** `admin`
      * **Password:** `123`

-----

### 📝 API Endpoints Overview

The application is powered by a RESTful API. Here are some of the primary endpoints:

  * `GET /api/products`: Retrieve a list of all products.
  * `POST /api/products`: Add a new product.
  * `PUT /api/products/<id>`: Update an existing product.
  * `DELETE /api/products/<id>`: Delete a product.
  * `GET /api/categories`: Retrieve all categories.
  * `POST /api/categories`: Add a new category.
  * `POST /api/operations/register`: Register a new operation (incoming/outgoing).
  * `GET /api/reports/<report_type>`: Generate a report in JSON format.
  * `GET /api/reports/<report_type>/pdf`: Generate a report as a PDF file.

-----

### 🔮 Future Improvements

This project has a solid foundation, but there are many opportunities for future development:

  * **Enhanced Authentication:** Implement password hashing and a more robust user session management system (e.g., using `Flask-Login`).
  * **User Roles & Permissions:** Add different user roles with varying levels of access.
  * **Dashboard with Visualizations:** Create a main dashboard with charts and graphs (e.g., using Chart.js) to visualize key metrics.
  * **Containerization:** Use Docker and Docker Compose to simplify deployment and ensure consistent environments.
  * **Environment Variables:** Move sensitive data like database credentials and secret keys out of the code and into environment variables.


