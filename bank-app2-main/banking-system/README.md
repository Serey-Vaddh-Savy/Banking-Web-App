# Banking System Project

This is a web application for a banking system built using Flask. It provides various features for customers and administrators to manage banking operations effectively.

## Features

- **Customer Registration**: New users can create an account by providing their username and password.
- **User Login**: Registered users can log in to access their banking accounts.
- **Balance Checking**: Users can view their current account balance.
- **Money Transfer**: Customers can transfer money to other accounts.
- **Stock Trading**: Users can engage in stock trading activities.
- **Complaint Submission**: Customers can submit complaints regarding issues or bugs in the application.
- **Admin Functionalities**: Admins can manage customer complaints and oversee operations through a dedicated dashboard.

## Project Structure

```
banking-system
├── app.py
├── templates
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── balance.html
│   ├── transfer.html
│   ├── trade.html
│   ├── complaint.html
│   ├── admin_dashboard.html
│   └── admin_complaints.html
├── static
│   ├── css
│   │   └── styles.css
│   ├── js
│   │   └── scripts.js
│   └── assets
├── database
│   └── bank.db
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Install the required dependencies using the command:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Open your web browser and go to `http://127.0.0.1:5000` to access the application.

## Usage

- Register a new account to start using the banking features.
- Log in with your credentials to access your account.
- Use the navigation links to check your balance, transfer money, trade stocks, or submit complaints.
- Admins can log in to manage customer complaints and oversee operations.

## License

This project is licensed under the MIT License.