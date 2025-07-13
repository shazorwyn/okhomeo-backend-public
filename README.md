# OKHomeo – Backend

This is the **backend API** for **OKHomeo**, a full-stack web application built for a homeopathic medical store. The backend powers user authentication, product and order management, and payment integration with Razorpay.

> ⚠️ This repository is a public duplicate of the private production backend linked with Railway. It is intended for demonstration and portfolio purposes.

---

## 🌐 Live Deployment

* **Backend URL**: [https://okhomeo-backend.up.railway.app](https://okhomeo-backend.up.railway.app) *(deployed via Railway, platform-provided domain)*

---

## 🚀 Features

* RESTful APIs for store and clinic modules using Django REST Framework
* JWT-based authentication using HttpOnly cookies for secure sessions
* Role-based access control for patients, doctors, and staff members
* Razorpay integration for secure payments with retry and cancellation support
* Order system with transactional integrity and real-time status updates
* Product and cart management with review system
* Contact API for clinic communication
* MySQL-based production database setup with scalable config

---

## 🧰 Tech Stack

* Django 5
* Django REST Framework
* MySQL
* JWT (via `djangorestframework-simplejwt`)
* Razorpay SDK
* Railway (deployment)

---

## 📦 API Overview

### 🔐 Authentication & Contact

* `POST /auth/login/` – Login
* `POST /auth/logout/` – Logout
* `POST /contact/` – Contact admin

### 🛍️ Store – Products & Reviews

* `GET /api/store/products/` – List all products
* `GET /api/store/products/{id}/` – Product details
* `GET /api/store/products/{product_id}/reviews/` – List product reviews
* `POST /api/store/products/{product_id}/reviews/` – Submit a review
* `POST /api/store/products/{product_id}/reviews/{id}/` – Edit a review

### 🛒 Cart Management

* `POST /api/store/cart/` – Add item to cart
* `GET /api/store/cart/{cart_id}/` – View cart
* `GET /api/store/cart/{cart_id}/items/` – List items in cart
* `DELETE /api/store/cart/{cart_id}/items/{id}/` – Remove item from cart

### 📦 Orders

* `POST /api/store/orders/` – Place an order
* `GET /api/store/orders/` – View order history
* `POST /api/store/orders/{id}/cancel/` – Cancel an order
* `POST /api/store/orders/{id}/verify-payment/` – Verify Razorpay payment
* `POST /api/store/orders/{id}/retry-payment/` – Retry Razorpay payment

### 🏥 Clinic – Treatments & Medicines

* `GET /api/clinic/medicines/` – List all medicines
* `GET /api/clinic/medicines/{id}/` – Medicine details
* `GET /api/clinic/treatments/` – List treatments
* `GET /api/clinic/treatments/{id}/` – Treatment details

---

## 🤝 Contribution

This project was built collaboratively by two developers working on the same system. Due to the initial local development setup, version control was introduced later, and the project was separately pushed to public repositories for portfolio purposes.

**Key Contributions:**

* Designed and implemented modular Django apps for store and clinic operations
* Developed and secured RESTful APIs using Django REST Framework
* Implemented JWT-based authentication with role-level permissions
* Integrated Razorpay for payments with cancellation and retry logic
* Ensured transactional safety during order placement and updates
* Modeled MySQL schema with clean relational design and migrations
* Coordinated production deployment with Railway, using .env configs and platform services

---

## 👥 Contributors

* [Adarsh Kumar Gupta](https://github.com/spookycent) – Full-stack Development (Backend, Razorpay Integration)
* [Aditya Kumar Gupta](https://github.com/shazorwyn) – Full-stack Development (Backend, Deployment)
