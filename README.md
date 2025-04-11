# Django REST Framework Ecommerce API

A fully-featured ecommerce REST API built with Django REST Framework, including product management, cart functionality, orders, user authentication, and Paystack payment integration.

## 📋 Features

- **Products Management**
  - Product CRUD with categories 
  - Search, filtering, and ordering
  - Stock management

- **User Authentication**
  - Token-based authentication
  - User profiles with shipping details

- **Shopping Cart**
  - Add/remove/update items
  - Calculate totals
  - Stock validation

- **Orders**
  - Order creation and management
  - Order history
  - Order status tracking

- **Checkout & Payment**
  - Seamless checkout process
  - Paystack payment integration
  - Payment verification
  - Webhook handling

## 🛠️ Tech Stack

- Django 5.0
- Django REST Framework
- SQLite (default, configurable)
- Paystack Payment API

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ecommerce-api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Paystack API keys**
   - Create a `.env` file in the project root
   - Add your Paystack keys:
     ```
     PAYSTACK_SECRET_KEY=sk_test_your_secret_key
     PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
     ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the server**
   ```bash
   python manage.py runserver
   ```

## 📚 API Endpoints

### Authentication
- `POST /api-token-auth/` - Obtain authentication token
- `GET /api/users/me/` - Get current user details

### Products
- `GET /api/products/` - List products
- `GET /api/products/{id}/` - Get product details
- `GET /api/products/categories/` - List categories

### Cart
- `GET /api/cart/` - Get user's cart
- `POST /api/cart/add/` - Add item to cart
- `POST /api/cart/update/` - Update cart item quantity
- `POST /api/cart/remove/` - Remove item from cart
- `POST /api/cart/clear/` - Clear cart

### Orders
- `GET /api/orders/` - List user's orders
- `GET /api/orders/{id}/` - Get order details
- `POST /api/orders/checkout-from-cart/` - Create order from cart

### Payments
- `POST /api/payments/initialize/` - Initialize payment
- `POST /api/payments/verify/` - Verify payment
- `POST /api/payments/webhook/` - Paystack webhook endpoint

## 💡 Usage Example

### Complete Purchase Flow

1. **Browse products**
   ```bash
   curl -X GET http://localhost:8000/api/products/
   ```

2. **Add product to cart**
   ```bash
   curl -X POST http://localhost:8000/api/cart/add/ \
     -H "Authorization: Token YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"product": 1, "quantity": 2}'
   ```

3. **View cart**
   ```bash
   curl -X GET http://localhost:8000/api/cart/ \
     -H "Authorization: Token YOUR_TOKEN"
   ```

4. **Checkout**
   ```bash
   curl -X POST http://localhost:8000/api/orders/checkout-from-cart/ \
     -H "Authorization: Token YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"shipping_address": "123 Main St, City", "phone": "1234567890"}'
   ```

5. **Initialize payment**
   ```bash
   curl -X POST http://localhost:8000/api/payments/initialize/ \
     -H "Authorization: Token YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"order_id": 1, "email": "customer@example.com"}'
   ```

## 🧪 Testing Paystack

Use Paystack test cards for testing:
- **Card Number**: 4084 0840 8408 4081
- **Expiry Date**: Any future date
- **CVV**: Any 3 digits
- **PIN**: Any 4 digits
- **OTP**: 123456

## 🔒 Security Best Practices

- Always use HTTPS in production
- Set up proper CORS settings
- Never commit .env files or secret keys
- Properly validate all user inputs
- Set up rate limiting for API endpoints

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🛣️ Roadmap

- [ ] Product reviews and ratings
- [ ] Discount coupons
- [ ] Multiple payment options
- [ ] Admin dashboard
- [ ] User wishlist

## 👥 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
