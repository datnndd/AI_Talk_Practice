from __future__ import annotations

from app.modules.payments.models import PaymentTransaction
from app.modules.payments.schemas.admin_payment import AdminPaymentTransactionRead


def serialize_admin_payment_transaction(payment: PaymentTransaction) -> AdminPaymentTransactionRead:
    user = payment.user
    return AdminPaymentTransactionRead.model_validate(
        {
            "id": payment.id,
            "user_id": payment.user_id,
            "user_email": user.email if user else "",
            "user_display_name": user.display_name if user else None,
            "provider": payment.provider,
            "plan": payment.plan,
            "plan_code": payment.plan_code,
            "duration_days": payment.duration_days,
            "original_amount": payment.original_amount,
            "discount_amount": payment.discount_amount,
            "promo_code": payment.promo_code,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "order_code": payment.order_code,
            "external_checkout_id": payment.external_checkout_id,
            "external_transaction_id": payment.external_transaction_id,
            "payment_url": payment.payment_url,
            "failure_reason": payment.failure_reason,
            "provider_payload": payment.provider_payload,
            "paid_at": payment.paid_at,
            "expires_at": payment.expires_at,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
        }
    )
