from urllib.parse import quote

from app.core.config import settings


def build_upi_uri(
    amount_inr: float,
    transaction_note: str,
    transaction_ref: str,
) -> str:
    """
    Standard UPI payment URI.

    This can be opened by:
        Google Pay
        PhonePe
        Paytm
        BHIM
        Other supported UPI apps

    No Razorpay/payment gateway is used.
    """

    params = {
        "pa": settings.upi_vpa,
        "pn": settings.upi_payee_name,
        "am": f"{amount_inr:.2f}",
        "cu": "INR",
        "tn": transaction_note,
        "tr": transaction_ref,
    }

    query = "&".join(
        f"{key}={quote(str(value), safe='')}"
        for key, value in params.items()
    )

    return f"upi://pay?{query}"


def calculate_discount(
    amount_inr: float,
    discount_type: str,
    discount_value: float,
) -> float:
    """
    Calculate coupon discount.

    Never allows the final amount to become negative.
    """

    amount = float(amount_inr)
    value = float(discount_value)

    discount_type = discount_type.upper()

    if discount_type == "PERCENT":
        if value < 0 or value > 100:
            raise ValueError(
                "Percentage discount must be between 0 and 100."
            )

        discount = amount * value / 100

    elif discount_type == "FIXED":
        if value < 0:
            raise ValueError(
                "Fixed discount cannot be negative."
            )

        discount = value

    else:
        raise ValueError(
            "Invalid discount type."
        )

    return round(
        min(discount, amount),
        2,
    )


def calculate_final_amount(
    amount_inr: float,
    discount_inr: float,
) -> float:
    return round(
        max(
            float(amount_inr)
            - float(discount_inr),
            0,
        ),
        2,
    )