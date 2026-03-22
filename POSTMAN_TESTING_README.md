# 🧪 BookLink API Testing with Postman

## 📋 Files Created

1. **`BookLink_API_Tests.postman_collection.json`** - Complete test collection
2. **`BookLink_Local_Environment.postman_environment.json`** - Environment variables

## 🚀 How to Import and Use

### Step 1: Import Collection
1. Open Postman
2. Click **"Import"** button (top left)
3. Select **"Upload Files"**
4. Choose `BookLink_API_Tests.postman_collection.json`
5. Click **"Import"**

### Step 2: Import Environment
1. Click **Settings** icon (gear) → **"Manage Environments"**
2. Click **"Import"**
3. Select `BookLink_Local_Environment.postman_environment.json`
4. Click **"Import"**
5. Select **"BookLink Local Environment"** from dropdown

### Step 3: Start Your Services
Make sure Docker containers are running:
```bash
cd /path/to/BookLink
docker-compose up -d
```

Verify services are running:
```bash
docker-compose ps
```

## 📁 Test Organization

```
📁 BookLink API Tests
├── 🔧 Setup & Health Checks
│   ├── Health Check - User Service
│   ├── Health Check - Catalog Service
│   ├── Health Check - Reservation Service
│   └── Health Check - Payment Service
├── 👥 User Service
│   ├── Create Student User
│   ├── Create Admin User
│   ├── List All Users
│   └── Get User by ID
├── 📚 Catalog Service
│   ├── Create Book - Clean Code
│   ├── Create Book - Design Patterns
│   ├── List All Books
│   ├── List Books with Exemplars
│   ├── Search Books
│   ├── Create Exemplar for Clean Code
│   ├── Create Second Exemplar
│   └── List All Exemplars
├── 🎫 Reservation Service
│   ├── Create Reservation
│   ├── Create Multi-Item Reservation
│   ├── List All Reservations
│   ├── List User Reservations
│   ├── Get Reservation by ID
│   ├── Notify Next User for Exemplar
│   ├── Fulfill Reservation Item
│   └── Cancel Reservation
├── 💳 Payment Service
│   ├── Create Payment
│   ├── List All Payments
│   └── Get Payment by ID
├── 🧪 Integration Tests
│   ├── Complete Booking Flow
│   ├── Flow: Notify User
│   ├── Flow: Process Payment
│   └── Flow: Fulfill Reservation
└── ❌ Error Handling Tests
    ├── Create User - Missing Fields
    ├── Get Non-existent User
    └── Create Reservation - Invalid User
```

## 🎯 Running Tests

### Option 1: Run Individual Tests
1. Click on any test in the collection
2. Click **"Send"**
3. Check the **"Test Results"** tab for automated validations

### Option 2: Run Entire Collection
1. Right-click on **"BookLink API Tests"** collection
2. Click **"Run collection"**
3. Select tests to run (or leave all selected)
4. Click **"Start Run"**

### Option 3: Run by Folder
- Right-click any folder (e.g., "User Service")
- Click **"Run folder"**

## 🔄 Test Flow

### Recommended Order:
1. **Setup & Health Checks** - Verify all services are running
2. **User Service** - Create users first
3. **Catalog Service** - Create books and exemplars
4. **Reservation Service** - Create and manage reservations
5. **Payment Service** - Process payments
6. **Integration Tests** - Test complete workflows
7. **Error Handling Tests** - Test error scenarios

## 📊 Automatic Features

### ✅ Automated Validations
- Status code checks
- Response structure validation
- Business logic verification

### 🔗 Variable Chaining
- User IDs automatically saved and reused
- Book/Exemplar IDs passed between tests
- Reservation IDs tracked across workflows

### 📝 Console Logging
- Test results logged to console
- Important IDs displayed for debugging
- Response times tracked

## 🐛 Troubleshooting

### Services Not Running
```bash
# Check service status
docker-compose ps

# Start services
docker-compose up -d

# Check logs
docker-compose logs [service-name]
```

### Port Conflicts
If you see connection errors, verify ports:
- User Service: `localhost:6000`
- Catalog Service: `localhost:7001` 
- Reservation Service: `localhost:3100`
- Payment Service: `localhost:4000`

### Environment Variables
If tests fail, check environment variables are set:
1. Click environment dropdown
2. Select "BookLink Local Environment"
3. Verify all BASE_URL_* variables are set

## 📈 Advanced Usage

### Custom Scripts
Each test includes validation scripts. You can:
- Modify existing validations
- Add custom assertions
- Extract additional data

### Monitoring
Use Postman Monitor to:
- Run tests automatically
- Track API performance
- Get alerts on failures

### Documentation
Auto-generate API documentation:
1. Right-click collection
2. "View Documentation"
3. Share with team

## 🎉 Success Indicators

✅ **All Health Checks Pass** - Services are running
✅ **Users Created** - Authentication layer working  
✅ **Books/Exemplars Created** - Catalog service functional
✅ **Reservations Work** - Booking system operational
✅ **Payments Process** - Payment system working
✅ **Integration Flow Completes** - End-to-end system works

## 🔧 Customization

### Adding New Tests
1. Right-click folder → "Add Request"
2. Configure method, URL, headers, body
3. Add test scripts for validation

### Modifying Environment
1. Manage Environments → Select environment
2. Add/modify variables
3. Use `{{variable_name}}` in requests

Your BookLink API is now fully testable! 🚀
