import hashlib
import hmac
import razorpay
from django.conf import settings
from django.utils import timezone
from .models import Order

client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))


def refund_payment(order: Order):
    if not order.can_be_refunded():
        return {"success": False, "error": "Order is not eligible for refund."}
    try:
        response = client.payment.refund(
            order.razorpay_payment_id,
            {
                "amount": int(order.total_price * 100),
            },
        )

        return {"success": True, "refund": response}

    except razorpay.errors.BadRequestError as e:
        return {"success": False, "error": str(e)}

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def verify_razorpay_signature(data: dict, order: Order):
    expected_signature = hmac.new(
        key=bytes(settings.RAZORPAY_KEY_SECRET, "utf-8"),
        msg=bytes(
            data["razorpay_order_id"] + "|" + data["razorpay_payment_id"], "utf-8"
        ),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if expected_signature == data["razorpay_signature"]:
        order.razorpay_payment_id = data["razorpay_payment_id"]
        order.razorpay_signature = data["razorpay_signature"]
        order.payment_status = Order.PAYMENT_STATUS_SUCCESSFUL
        order.save()
        return True
    else:
        order.payment_status = Order.PAYMENT_STATUS_UNSUCCESSFUL
        order.save()
        return False


def create_razorpay_order(order: Order):
    response = client.order.create(
        {
            "amount": int(order.total_price * 100),
            "currency": "INR",
            "payment_capture": 1,
            "notes": {"order_id": str(order.id)},
        }
    )
    return response
