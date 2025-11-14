# Ekhane.bd - Multi-Shop Ecommerce Platform Blueprint

## Project Overview
A multi-tenant SaaS ecommerce platform where retail business owners can create their own online stores with custom subdomains, choose from multiple templates, and accept payments through bKash and Cash on Delivery.

**Target Market:** Bangladesh
**Tech Stack:** Python Django, Bootstrap 5, PostgreSQL/SQLite, Redis, bKash Payment Gateway
**Architecture:** Multi-tenant with subdomain-based store separation

---

## Current Status

### ✅ Already Implemented
- Custom User model (email-based authentication)
- Store model with trial period (7 days)
- Registration UI with real-time validation
- Email service with OTP support
- Subdomain validation (profanity, reserved names)
- Multi-language support (English/Bangla)
- Redis caching infrastructure

### ❌ Not Yet Implemented
- Registration backend processing
- Product catalog system
- Shopping cart & checkout
- Payment gateway integration
- Subdomain routing middleware
- Template selection system
- Order management
- Store owner dashboard

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Main Domain                          │
│                   (www.ekhane.bd)                        │
├─────────────────────────────────────────────────────────┤
│  - Landing Page                                          │
│  - Registration/Login                                    │
│  - Template Showcase                                     │
│  - Pricing Plans                                         │
│  - Global Admin Panel                                    │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Subdomain 1 │  │  Subdomain 2 │  │  Subdomain N │
│shop1.ekhane  │  │shop2.ekhane  │  │shopN.ekhane  │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ Storefront   │  │ Storefront   │  │ Storefront   │
│ (Template A) │  │ (Template B) │  │ (Template C) │
│              │  │              │  │              │
│ - Products   │  │ - Products   │  │ - Products   │
│ - Cart       │  │ - Cart       │  │ - Cart       │
│ - Checkout   │  │ - Checkout   │  │ - Checkout   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
        ┌─────────────────────────────────┐
        │   Store Owner Dashboard          │
        │   (dashboard.ekhane.bd/login)    │
        ├─────────────────────────────────┤
        │  - Product Management            │
        │  - Order Management              │
        │  - Template Selection            │
        │  - Payment Settings              │
        │  - Analytics                     │
        └─────────────────────────────────┘
```

---

## Database Schema

### Phase 1: Core Models (Already Exists)

```python
User:
  - username (EmailField, unique)
  - email (EmailField)
  - phone (CharField)
  - password (hashed)

Store:
  - owner (OneToOne → User)
  - store_name (CharField)
  - subdomain (CharField, unique)
  - status (draft/active/expired)
  - trial_end (DateField)
  - created_at (DateTimeField)
```

### Phase 2: Product & Category Models

```python
Category:
  - store (ForeignKey → Store)
  - name (CharField)
  - slug (SlugField)
  - description (TextField)
  - parent (ForeignKey → self, nullable)
  - is_active (BooleanField)
  - created_at (DateTimeField)

Product:
  - store (ForeignKey → Store)
  - category (ForeignKey → Category)
  - name (CharField)
  - slug (SlugField)
  - description (TextField)
  - price (DecimalField)
  - sale_price (DecimalField, nullable)
  - sku (CharField, unique per store)
  - stock_quantity (IntegerField)
  - is_active (BooleanField)
  - created_at (DateTimeField)
  - updated_at (DateTimeField)

ProductImage:
  - product (ForeignKey → Product)
  - image (ImageField)
  - is_primary (BooleanField)
  - order (IntegerField)
```

### Phase 3: Order & Cart Models

```python
Customer:
  - store (ForeignKey → Store)
  - name (CharField)
  - email (EmailField)
  - phone (CharField)
  - created_at (DateTimeField)

Cart:
  - customer (ForeignKey → Customer, nullable)
  - session_key (CharField)
  - created_at (DateTimeField)

CartItem:
  - cart (ForeignKey → Cart)
  - product (ForeignKey → Product)
  - quantity (IntegerField)
  - price (DecimalField)

Order:
  - store (ForeignKey → Store)
  - customer (ForeignKey → Customer)
  - order_number (CharField, unique)
  - status (pending/confirmed/processing/shipped/delivered/cancelled)
  - payment_method (bkash/cod)
  - payment_status (pending/paid/failed)
  - subtotal (DecimalField)
  - shipping_cost (DecimalField)
  - total (DecimalField)
  - shipping_address (JSONField)
  - notes (TextField)
  - created_at (DateTimeField)
  - updated_at (DateTimeField)

OrderItem:
  - order (ForeignKey → Order)
  - product (ForeignKey → Product)
  - quantity (IntegerField)
  - price (DecimalField)
  - total (DecimalField)
```

### Phase 4: Payment Models

```python
Payment:
  - order (OneToOne → Order)
  - payment_method (CharField)
  - transaction_id (CharField, nullable)
  - amount (DecimalField)
  - status (pending/completed/failed)
  - bkash_payment_id (CharField, nullable)
  - bkash_trx_id (CharField, nullable)
  - created_at (DateTimeField)
  - updated_at (DateTimeField)
```

### Phase 5: Template & Store Settings

```python
Template:
  - name (CharField)
  - slug (SlugField)
  - description (TextField)
  - thumbnail (ImageField)
  - preview_url (URLField)
  - is_active (BooleanField)
  - is_premium (BooleanField)

StoreSettings:
  - store (OneToOne → Store)
  - template (ForeignKey → Template)
  - logo (ImageField, nullable)
  - banner (ImageField, nullable)
  - primary_color (CharField)
  - secondary_color (CharField)
  - currency (CharField, default="BDT")
  - language (CharField, default="bn")
  - bkash_enabled (BooleanField)
  - bkash_merchant_number (CharField)
  - bkash_api_key (CharField, encrypted)
  - cod_enabled (BooleanField)
  - shipping_cost (DecimalField)
  - free_shipping_threshold (DecimalField, nullable)
```

---

## Implementation Phases

### **PHASE 1: Complete Registration & Authentication** (Week 1)

#### 1.1 Complete Registration Backend
- Implement POST handler in `signup()` view
- Create User and Store records
- Send OTP for email verification
- Create OTP verification page
- Implement email verification flow
- Auto-login after successful registration
- Create welcome email template

#### 1.2 Login/Logout System
- Create login view with email/password
- Session management
- Password reset functionality
- "Remember me" feature

#### 1.3 Admin Panel Configuration
- Register models in Django admin
- Customize admin interface
- Add list filters and search

**Deliverables:**
- Working registration with email verification
- Login/logout functionality
- Password reset flow
- Django admin configured

---

### **PHASE 2: Store Owner Dashboard** (Week 1-2)

#### 2.1 Dashboard Layout
- Create base dashboard template (Bootstrap)
- Sidebar navigation:
  - Dashboard (overview)
  - Products
  - Orders
  - Customers
  - Settings
  - Analytics
- Top navigation with store switcher
- Responsive design

#### 2.2 Dashboard Overview Page
- Sales statistics (today, this week, this month)
- Recent orders list
- Low stock alerts
- Quick action buttons
- Trial period countdown (if applicable)

#### 2.3 Store Settings Page
- Store information (name, description, contact)
- Logo and banner upload
- Template selection (Phase 9)
- Payment settings (bKash credentials)
- Shipping settings
- Color scheme customization

**Deliverables:**
- Dashboard template with navigation
- Overview page with statistics
- Settings page for store configuration

---

### **PHASE 3: Product Management System** (Week 2-3)

#### 3.1 Category Management
- Create Category model
- Category CRUD operations
- Nested categories support
- Category listing page
- Category form with validation

#### 3.2 Product Management
- Create Product and ProductImage models
- Product listing page (datatable with search/filter)
- Add/Edit product form:
  - Basic info (name, description, SKU)
  - Pricing (regular price, sale price)
  - Inventory (stock quantity)
  - Multiple image upload
  - Category selection
  - Product status toggle
- Bulk actions (delete, activate/deactivate)
- Product import/export (CSV)

#### 3.3 Image Management
- Multiple image upload with drag-drop
- Set primary image
- Image reordering
- Image compression/optimization
- Cloudinary or local storage

**Deliverables:**
- Category CRUD system
- Product CRUD with image upload
- Product listing with filters
- CSV import/export

---

### **PHASE 4: Customer-Facing Storefront** (Week 3-4)

#### 4.1 Template 1: Modern Minimalist (Default)
- Clean, modern design
- Header with logo, navigation, search, cart icon
- Hero section with banner image
- Featured products grid
- Categories section
- Footer with store info

#### 4.2 Template 2: Classic Ecommerce
- Traditional ecommerce layout
- Mega menu navigation
- Sidebar filters
- Product grid with quick view
- Promotional banners

#### 4.3 Template 3: Boutique Style
- Fashion/boutique focused design
- Large hero images
- Minimal navigation
- Product showcase with hover effects
- Instagram integration section

#### 4.4 Core Storefront Pages (All Templates)
- **Homepage:** Featured products, categories, banners
- **Product Listing:** Grid/list view, filters, sorting, pagination
- **Product Detail:** Images gallery, description, price, add to cart
- **Search Results:** Search functionality with filters
- **About Us:** Store description (editable by owner)
- **Contact:** Contact form

#### 4.5 Responsive Design
- Mobile-first approach
- Tablet and desktop breakpoints
- Touch-friendly navigation

**Deliverables:**
- 3 complete storefront templates
- All core pages functional
- Responsive design
- Template switching capability

---

### **PHASE 5: Shopping Cart & Wishlist** (Week 4)

#### 5.1 Cart Functionality
- Add to cart (AJAX)
- Cart page with item list
- Update quantity
- Remove items
- Cart subtotal calculation
- Cart icon with item count
- Session-based cart for guests
- Persistent cart for logged-in customers

#### 5.2 Wishlist (Optional - Future)
- Add to wishlist
- Wishlist page
- Move to cart from wishlist

**Deliverables:**
- Working cart system
- Cart page
- Add/update/remove functionality
- Cart widget in header

---

### **PHASE 6: Checkout & Order Management** (Week 5)

#### 6.1 Checkout Process
- Checkout page with form:
  - Customer information (name, email, phone)
  - Shipping address (division, district, area, full address)
  - Order notes
  - Payment method selection (bKash/COD)
- Order summary sidebar
- Form validation
- Create order on submission

#### 6.2 Order Confirmation
- Order confirmation page
- Order number display
- Payment instructions (if bKash)
- Email notification to customer and store owner

#### 6.3 Store Owner Order Management
- Order listing page in dashboard
- Order status filters
- Order detail view:
  - Customer information
  - Products ordered
  - Payment status
  - Shipping address
  - Order timeline
- Update order status
- Print invoice
- Order notes

#### 6.4 Customer Order Tracking (Optional)
- Order tracking page (public)
- Track by order number + email/phone

**Deliverables:**
- Complete checkout flow
- Order creation and confirmation
- Order management dashboard
- Email notifications

---

### **PHASE 7: Payment Integration** (Week 5-6)

#### 7.1 Cash on Delivery (COD)
- COD option in checkout
- Mark order as "pending payment"
- COD instructions on confirmation page
- Manual payment confirmation by store owner

#### 7.2 bKash Payment Gateway Integration
- bKash Merchant API integration
- Environment setup (sandbox + production)
- Payment flow:
  1. Customer selects bKash
  2. Redirect to bKash payment page
  3. bKash payment completion
  4. Callback handling
  5. Payment verification
  6. Order status update
- Payment model to store transactions
- Webhook for payment notifications
- Refund functionality (manual via dashboard)

#### 7.3 Payment Settings in Dashboard
- bKash credentials configuration
- Enable/disable payment methods
- Test mode toggle
- Transaction history

**Deliverables:**
- COD fully functional
- bKash integration (sandbox + production)
- Payment verification and callbacks
- Transaction logging

---

### **PHASE 8: Subdomain Routing & Multi-Tenancy** (Week 6)

#### 8.1 Subdomain Middleware
- Create middleware to detect subdomain
- Extract store from subdomain
- Set current store in request object
- Handle invalid subdomains (404)

#### 8.2 Template Resolution
- Serve correct template based on store settings
- Template context processor for store data
- Dynamic color scheme loading

#### 8.3 URL Routing
- Separate URL patterns for:
  - Main domain (landing, registration)
  - Store dashboard (dashboard.ekhane.bd or main domain /dashboard/)
  - Store storefronts (subdomain.ekhane.bd)

#### 8.4 DNS Configuration Guide
- Wildcard DNS setup instructions
- Local development configuration (hosts file)
- Production deployment guide

**Deliverables:**
- Subdomain routing working
- Multi-tenant isolation
- Template switching
- Deployment documentation

---

### **PHASE 9: Template Selection System** (Week 7)

#### 9.1 Template Management
- Create Template model
- Seed database with 3 initial templates
- Template preview page (public)
- Template thumbnails and screenshots

#### 9.2 Template Selection in Dashboard
- Template gallery in settings
- Live preview modal
- One-click template switching
- Confirmation before switching

#### 9.3 Template Customization
- Color picker for primary/secondary colors
- Font selection (Google Fonts)
- Custom CSS editor (advanced users)
- Logo and banner upload per template

**Deliverables:**
- 3 production-ready templates
- Template selection interface
- Customization options
- Preview functionality

---

### **PHASE 10: Admin Features & Analytics** (Week 7-8)

#### 10.1 Store Analytics Dashboard
- Sales charts (daily, weekly, monthly)
- Product performance (best sellers, low stock)
- Customer insights (new vs returning)
- Revenue reports
- Order status breakdown

#### 10.2 Global Super Admin
- View all stores
- Store approval/suspension
- Platform analytics
- User management
- Template management

#### 10.3 Additional Features
- Coupon/discount system
- Customer reviews and ratings
- Email marketing (newsletter)
- SEO settings (meta tags, sitemap)
- Social media integration
- Multi-language product descriptions
- Inventory alerts

**Deliverables:**
- Analytics dashboard
- Super admin panel
- Coupon system
- Review system

---

## Technical Requirements

### Backend
- **Framework:** Django 5.2.7
- **Database:** PostgreSQL (production), SQLite (development)
- **Cache:** Redis (sessions, caching, queues)
- **Task Queue:** Celery (email sending, reports)
- **Storage:** AWS S3 or Cloudinary (images)
- **Authentication:** Django built-in + OTP

### Frontend
- **CSS Framework:** Bootstrap 5.3.3
- **JavaScript:** Vanilla JS + Alpine.js (lightweight reactivity)
- **AJAX:** Fetch API
- **Icons:** Bootstrap Icons or Font Awesome
- **Charts:** Chart.js (analytics)

### Payment
- **bKash:** Official Merchant API (Tokenized)
- **COD:** Manual processing

### Deployment
- **Hosting:** DigitalOcean, AWS, or Heroku
- **Web Server:** Gunicorn + Nginx
- **SSL:** Let's Encrypt (free SSL)
- **Domain:** Wildcard DNS (*.ekhane.bd)

---

## Security Considerations

1. **Data Isolation:** Each store's data must be isolated (filter by store in all queries)
2. **CSRF Protection:** Enable Django CSRF for all forms
3. **SQL Injection:** Use Django ORM (no raw SQL)
4. **XSS Prevention:** Auto-escaping in templates
5. **Payment Security:**
   - Never store card details
   - Encrypt bKash API keys
   - Use HTTPS for all payment pages
6. **File Upload:** Validate file types, scan for malware
7. **Rate Limiting:** Prevent brute force on login/OTP
8. **Environment Variables:** Store secrets in .env file

---

## Testing Strategy

### Unit Tests
- Model methods
- Utility functions (email, OTP, validation)
- Payment processing

### Integration Tests
- Registration flow
- Login/logout
- Cart operations
- Checkout process
- Payment callbacks

### Manual Testing
- Cross-browser testing (Chrome, Firefox, Safari, Edge)
- Mobile testing (iOS, Android)
- Payment testing (sandbox)
- Subdomain routing

---

## Deployment Checklist

- [ ] Set `DEBUG = False` in production
- [ ] Configure PostgreSQL database
- [ ] Set up Redis server
- [ ] Configure email backend (Gmail or SendGrid)
- [ ] Set up Celery workers
- [ ] Configure static/media file serving
- [ ] Set up wildcard DNS (*.ekhane.bd)
- [ ] Obtain SSL certificates
- [ ] Configure Nginx reverse proxy
- [ ] Set up bKash production credentials
- [ ] Enable database backups
- [ ] Set up monitoring (Sentry for errors)
- [ ] Configure logging
- [ ] Load testing

---

## Timeline Summary

| Phase | Description | Duration |
|-------|-------------|----------|
| 1 | Registration & Auth | 1 week |
| 2 | Store Dashboard | 1 week |
| 3 | Product Management | 1-2 weeks |
| 4 | Storefront Templates | 1-2 weeks |
| 5 | Shopping Cart | 1 week |
| 6 | Checkout & Orders | 1 week |
| 7 | Payment Integration | 1-2 weeks |
| 8 | Subdomain Routing | 1 week |
| 9 | Template Selection | 1 week |
| 10 | Analytics & Admin | 1-2 weeks |

**Total Estimated Time:** 10-14 weeks (2.5-3.5 months)

---

## Success Metrics

- Store owners can register and create stores in < 5 minutes
- Products can be added in < 2 minutes
- Checkout completes in < 3 steps
- Page load time < 3 seconds
- Mobile responsive on all devices
- 99.9% uptime
- Zero payment failures
- Positive user feedback

---

## Future Enhancements (Post-Launch)

- Mobile app (Flutter or React Native)
- Advanced analytics (Google Analytics integration)
- Multi-language product support
- Inventory management with suppliers
- Dropshipping integration
- Print-on-demand services
- Marketing automation
- Loyalty program
- Subscription products
- Multi-currency support
- Advanced shipping options (third-party courier integration)
- AI-powered product recommendations
- Chat support (live chat widget)

---

## Conclusion

This blueprint provides a comprehensive roadmap for building a production-ready multi-shop ecommerce platform tailored for the Bangladesh market. The phased approach ensures systematic development with clear milestones and deliverables.

**Next Steps:**
1. Review and approve blueprint
2. Set up development environment
3. Begin Phase 1 implementation
4. Weekly progress reviews
5. User testing after each phase
