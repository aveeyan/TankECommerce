# TankECommerce

TankECommerce is a dummy e-commerce website that demonstrates the concept of an online store. The website is themed around tank models based on the popular game *World of Tanks*. It includes basic e-commerce features like shopping cart functionality, payment gateway integration, and an admin dashboard.

## Features

- **Payment Gateway**: Integrated with Stripe for payment processing.
- **Shopping Cart**: Add items to the cart, manage quantities, and proceed to checkout.
- **Admin Dashboard**: Admins can manage the store, view orders, and manage inventory.
- **Inventory Management System**: Admins can add, edit, or delete items from the store.
- **Order Management System**: (Coming soon)
- **User & Admin Login**: Separate logins for customers and admins.
- **Searching and Categorization Filters**: Helps customers find items based on different categories.
- **Sorting Filters**: Allows customers to sort items (currently being fixed).

## Setup Instructions

### 1. Install Dependencies

To get started, install the required dependencies by running:

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

Once the dependencies are installed, initialize the database by running the following command:

```bash
python3 db_create.py
```

### 3. Run the Server

To start the server, use the following command:

```bash
flask run
```

Your website should now be live and accessible in your browser.

## Testing Credentials

### Admin Login:
- **Username**: `admin`
- **Password**: `admin123`

### Payment Testing:
- **Successful Payment**: `4242424242424242` (For payment success, use any random expiry date, CVC, and postal code.)
- **Failed Payment**: `4000000000000000` (For payment failure, use any random expiry date, CVC, and postal code.)

## Screenshots

Here are some screenshots demonstrating the functionality of the website:

1. ![Screenshot 1](https://github.com/user-attachments/assets/df425ddf-ad21-428d-abd1-cfd010c6d4e6)
2. ![Screenshot 2](https://github.com/user-attachments/assets/2100fd12-573f-47ae-be73-450cfb9512d4)
3. ![Screenshot 3](https://github.com/user-attachments/assets/9c0c97a1-3b30-456d-84a0-e1172b8c43c7)
4. ![Screenshot 4](https://github.com/user-attachments/assets/2235154e-bda3-4e43-8b73-e5e1b5e71560)
5. ![Screenshot 5](https://github.com/user-attachments/assets/0668f46c-249d-435e-991d-ac8d37acfb2a)

## Future Features
- Order Management System (Coming soon)
