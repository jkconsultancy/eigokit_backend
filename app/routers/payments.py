from fastapi import APIRouter
from app.database import supabase

router = APIRouter()


@router.post("/process")
async def process_payment(school_id: str, amount: float, payment_method: str):
    """Process a payment (would integrate with Stripe in production)"""
    # This is a placeholder - in production, integrate with Stripe
    payment_data = {
        "school_id": school_id,
        "amount": amount,
        "currency": "JPY",
        "payment_method": payment_method,
        "status": "paid"
    }
    
    result = supabase.table("payments").insert(payment_data).execute()
    return {"payment_id": result.data[0]["id"], "message": "Payment processed"}

