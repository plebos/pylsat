import asyncio
from fastapi import HTTPException
from starlette.requests import Request
from pymacaroons import Macaroon, Verifier
import datetime
import hashlib
import uuid
from bolt11.core import decode


class L402Validator:
    """
    Middleware for validating L402 (Lightning Service Authentication Tokens) in a FastAPI application.
    
    Attributes:
        root_key: The root key for generating and verifying macaroons.
        price_sats: The price (in satoshis) for accessing the API endpoint.
        expiry_sec: The expiration time (in seconds) for the macaroon.
        generate_invoice: A function for generating Lightning Network invoices.
        verified_macaroons: A dictionary for caching verified macaroons to ensure they are used only once.
        cleanup_interval: The interval (in seconds) at which expired macaroons are cleaned up from the cache.
    """
    def __init__(self, root_key: str, price_sats: int, expiry_sec: int, generate_invoice_func):
        """
        Initializes the L402Validator with the root key, price, expiry time, and invoice generation function.
        Starts the cleanup task for expired macaroons.
        """
        
        self.root_key = root_key
        self.price_sats = price_sats
        self.expiry_sec = expiry_sec
        self.generate_invoice = generate_invoice_func
        self.verified_macaroons = {}  # Cache to store verified macaroons
        self.cleanup_interval = 60 * 10  # Cleanup interval in seconds (10 minutes)
        asyncio.create_task(self.cleanup_expired_macaroons())  # Start the cleanup task

    async def cleanup_expired_macaroons(self):
        """
        Periodically cleanup expired macaroons from the cache.
        """
        while True:
            await asyncio.sleep(self.cleanup_interval)  # Wait for the cleanup interval
            # Create a list of expired macaroons
            expired_macaroons = [id for id, expiry in self.verified_macaroons.items() if datetime.datetime.now().isoformat() > expiry]
            # Remove expired macaroons from the cache
            for id in expired_macaroons:
                del self.verified_macaroons[id]

    
    async def __call__(self, request: Request):
        l402_key = request.headers.get('Authorization')
        if l402_key is None or not l402_key.startswith('LSAT '):

            try:
                label = str(uuid.uuid4()) 
                invoice = await self.generate_invoice(self.price_sats, f'LSAT_{label}', f'payment for endpoint')  # function to generate invoice
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Couldn't generate invoice. Reason: {str(e)}")

            encoded_invoice = invoice['bolt11']    
            decoded_invoice = decode(encoded_invoice)
            payment_hash = decoded_invoice.tags['p']
            print(payment_hash)
            macaroon = Macaroon(identifier=payment_hash, key=self.root_key)

            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=self.expiry_sec)
            macaroon.add_first_party_caveat(f"expires = {expiry_time.isoformat()}")
            macaroon.add_first_party_caveat(f"payment_hash = {payment_hash}")
            encoded_macaroon = macaroon.serialize()
            
            raise HTTPException(
                status_code=402,
                detail="Payment Required",
                headers={"content-type": "application/json",
                         "www-authenticate": f'LSAT macaroon="{encoded_macaroon}",invoice="{encoded_invoice}"'}
            )

        try:
            macaroon, preimage = l402_key.lstrip('LSAT ').split(':')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid L402 key format")

        try:
            macaroon = Macaroon.deserialize(macaroon)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Couldn't deserialize macaroon. Reason: {str(e)}")

        verifier = Verifier()
        
        verifier.satisfy_general(lambda caveat: caveat.split(' = ')[0] == 'expires' and datetime.datetime.now().isoformat() <= caveat.split(' = ')[1])
        print(hashlib.sha256(bytes.fromhex(preimage)).hexdigest())
        verifier.satisfy_general(lambda caveat: caveat.split(' = ')[0] == 'payment_hash' and hashlib.sha256(bytes.fromhex(preimage)).hexdigest() == caveat.split(' = ')[1])
        try:
            if not verifier.verify(macaroon, self.root_key):
                raise HTTPException(status_code=403, detail="Forbidden: Invalid macaroon or preimage")
        except Exception as e:
            raise HTTPException(status_code=403, detail=f"Forbidden: {str(e)}")

        if macaroon.identifier in self.verified_macaroons:
            raise HTTPException(status_code=403, detail=f"Forbidden: Macaroon is only valid once")

        # If verification is successful, add macaroon to cache with its expiry time
        for caveat in macaroon.caveats:
            if caveat.caveat_id.split(' = ')[0] == 'expires':
                self.verified_macaroons[macaroon.identifier] = caveat.caveat_id.split(' = ')[1]

        return request  # Add this line
