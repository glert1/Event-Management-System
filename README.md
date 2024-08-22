# Event Management System

This is a web-based Event Management System built with Python and Flask, designed to streamline the process of managing events, bookings, and users.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.x
- Flask
- MySQL

## Setup Environment

1. **Install Python and Flask**
   - Download and install Python from [python.org](https://www.python.org/downloads/).
   - Install Flask by running the following command:
     ```bash
     pip install Flask
     ```

2. **Install MySQL and Set Up Database**
   - Download and install MySQL from [mysql.com](https://dev.mysql.com/downloads/installer/).
   - Set up the database by running the `events.sql` script located in the `database` folder.

3. **Create a Virtual Environment and Install Required Packages**
   - Create a virtual environment:
     ```bash
     python3 -m venv venv
     ```
   - Activate the virtual environment:
     - On Windows:
       ```bash
       venv\Scripts\activate
       ```
     - On MacOS/Linux:
       ```bash
       source venv/bin/activate
       ```
   - Install required packages using:
     ```bash
     pip install -r requirements.txt
     ```

## Database Configuration

1. **Configure the Database Connection**
   - Open the `events.sql` file located in the `database` folder and execute it to set up the necessary tables and data.
   - Create the tables first, then insert data into the tables, and finally, add the necessary constraints.

2. **Update Database Credentials in the Application**
   - Open the `app.py` file.
   - Replace `your_password` with your MySQL server password. If your MySQL host and username are different, update them accordingly.
   - Refer to the screenshot in our report for detailed guidance on the code changes.

## Running the Application

1. **Start the Application**
   - Navigate to the `event-management-system-app` folder in your terminal.
   - Run the application using:
     ```bash
     python3 app.py
     ```
   - If `python3` doesn’t work, try:
     ```bash
     python app.py
     ```

## Accessing the Application

1. **Open in Browser**
   - Open your web browser and navigate to `http://127.0.0.1:5000`.

2. **Login Information**
   - To login as an Admin, use:
     - **Username:** `admin`
     - **Password:** `admin`
   - To login as a Manager, use:
     - **Username:** `manager`
     - **Password:** `manager`
   - To login as a Customer:
     - Use the email from the customer table as the email.
     - Use the customer’s phone number as the password.
     - Alternatively, you can create a new customer account using the ‘Buy Tickets’ form.
