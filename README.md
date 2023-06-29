# pylsat

A Python library for validating L402 (formerly known as LSAT) protocol for Lightning Network payments in a FastAPI application.

## Installation

To install pylsat, simply use pip:

```bash
pip install pylsat
```

## Usage
In your FastAPI application, you would use pylsat as middleware. First, initialize the L402Validator with the root key, price (in satoshis), expiry time (in seconds), and the function for generating invoices. Then, use it as a dependency in your route handlers.

Here is an example:
```python
from fastapi import FastAPI, BackgroundTasks, Depends, Request
from pylsat import L402Validator
import os

async def generate_invoice(sats, label, desc):
    # Implementation of function to generate invoice
    return {"bolt11": "Your generated bolt11 invoice"}

app = FastAPI()

validator = L402Validator(
    root_key=os.environ.get("MACAROON_ROOT_KEY"),
    price_sats=10,
    expiry_sec=60,
    generate_invoice_func=generate_invoice,
)

@app.post("/api/premium/endpoint", status_code=201)
async def premium_endpoint(background_tasks: BackgroundTasks, request: Request = Depends(validator)):
    # Your route handler logic here
    pass
```
With this setup, all requests to the "/api/premium/endpoint" route of your FastAPI application will be intercepted by the L402Validator middleware. If the request doesn't contain a valid LSAT in the Authorization header, the middleware will return a 402 Payment Required response with a Lightning invoice and a macaroon in the www-authenticate header.

The client can then pay the Lightning invoice, and resend the request with the Authorization header containing the macaroon and the preimage of the paid invoice.

The L402Validator middleware will verify the macaroon and the preimage, and allow the request to pass through to your FastAPI application if they are valid. If they are invalid, it will return a 403 Forbidden response.

Note: The function you provide for generate_invoice_func should return a dict with a bolt11 key containing the bolt11-encoded Lightning invoice. In a real application, you would use a Lightning node to generate the invoice.

