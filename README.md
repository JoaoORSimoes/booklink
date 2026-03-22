#Developed with assistance from AI tools and in collaboration with colleagues

- Francisco Cardoso
- Helder Gonçalves
- Joao Hossi
- Joao Simoes

# BookLink
This project was built with a microservices architecture and allows users to search the catalog, reserve and borrow books, manage returns, and process fines.

## Features
- Catalog search and book metadata management
- User authentication and account management  
- Loan, return, and reservation handling
- Fine and payment processing
- Command-line interaction
- Docker-based deployment

## Microservices
- **Catalog service**: Books, authors, availability, search
- **User service**: Authentication, accounts (students/staff)
- **Loans & Reservations**: Borrowing, returns, waitlists
- **Payments service**: Fines and late fees

## Technologies
- Python
- Docker & Docker compose

## Architecture
The system is divided into independent services that communicate with each other via REST/RPC to manage library operations in a scalable and maintainable way.
