from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.database import get_db

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("")
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=100),
    search: Optional[str] = None,
    segment: Optional[str] = None,
    channel: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    offset = (page - 1) * page_size
    params = {"limit": page_size, "offset": offset}
    filters = ["1=1"]

    if search:
        filters.append("(c.customer_ref ILIKE :search OR c.name ILIKE :search OR c.email ILIKE :search)")
        params["search"] = f"%{search}%"
    if segment:
        filters.append("c.segment = :segment")
        params["segment"] = segment
    if channel:
        filters.append("c.acquisition_channel = :channel")
        params["channel"] = channel
    if region:
        filters.append("c.region = :region")
        params["region"] = region

    where_clause = " AND ".join(filters)

    sql_count = text(f"SELECT COUNT(*) FROM customers c WHERE {where_clause}")
    total_count = db.execute(sql_count, params).scalar() or 0

    sql_data = text(f"""
        SELECT
            c.id,
            c.customer_ref,
            c.name,
            c.email,
            c.segment,
            c.acquisition_channel,
            c.region,
            c.signup_date,
            c.is_active,
            COUNT(t.id) AS total_orders,
            COALESCE(SUM(CASE WHEN t.is_refund = false AND t.status = 'completed' THEN t.amount ELSE 0 END), 0) AS total_spent,
            MAX(t.timestamp) AS last_order_date,
            p.risk_score,
            p.risk_category,
            p.priority_score
        FROM customers c
        LEFT JOIN transactions t ON c.id = t.customer_id
        LEFT JOIN (
            SELECT customer_id, risk_score, risk_category, priority_score
            FROM customer_risk_predictions
            WHERE id IN (SELECT MAX(id) FROM customer_risk_predictions GROUP BY customer_id)
        ) p ON c.id = p.customer_id
        WHERE {where_clause}
        GROUP BY c.id, c.customer_ref, c.name, c.email, c.segment, c.acquisition_channel, c.region, c.signup_date, c.is_active, p.risk_score, p.risk_category, p.priority_score
        ORDER BY total_spent DESC
        LIMIT :limit OFFSET :offset
    """)

    rows = db.execute(sql_data, params).mappings().all()

    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "customer_ref": r["customer_ref"],
            "name": r["name"],
            "email": r["email"],
            "segment": r["segment"],
            "acquisition_channel": r["acquisition_channel"],
            "region": r["region"],
            "signup_date": r["signup_date"].strftime("%Y-%m-%d") if r["signup_date"] else None,
            "is_active": r["is_active"],
            "total_orders": int(r["total_orders"]),
            "total_spent": round(float(r["total_spent"]), 2),
            "last_order_date": r["last_order_date"].strftime("%Y-%m-%d") if r["last_order_date"] else None,
            "risk_score": round(float(r["risk_score"]), 3) if r["risk_score"] is not None else None,
            "risk_category": r["risk_category"],
            "priority_score": round(float(r["priority_score"]), 1) if r["priority_score"] is not None else None
        })

    return {
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": (total_count + page_size - 1) // page_size,
        "customers": items
    }


@router.get("/{customer_id}")
def get_customer_detail(customer_id: int, db: Session = Depends(get_db)):
    sql_cust = text("""
        SELECT id, customer_ref, name, email, segment, acquisition_channel, region, signup_date, is_active
        FROM customers WHERE id = :cid
    """)
    cust = db.execute(sql_cust, {"cid": customer_id}).mappings().first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    sql_tx = text("""
        SELECT t.id, t.transaction_ref, t.timestamp, t.amount, t.status, t.payment_method, t.is_refund, c.name AS category_name
        FROM transactions t
        LEFT JOIN product_categories c ON t.category_id = c.id
        WHERE t.customer_id = :cid
        ORDER BY t.timestamp DESC
        LIMIT 50
    """)
    txs = [
        {
            "id": r["id"],
            "transaction_ref": r["transaction_ref"],
            "timestamp": r["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if r["timestamp"] else None,
            "amount": float(r["amount"]),
            "status": r["status"],
            "payment_method": r["payment_method"],
            "is_refund": r["is_refund"],
            "category": r["category_name"]
        }
        for r in db.execute(sql_tx, {"cid": customer_id}).mappings().all()
    ]

    sql_pred = text("""
        SELECT risk_score, risk_category, priority_score, contributing_features, created_at
        FROM customer_risk_predictions
        WHERE customer_id = :cid
        ORDER BY id DESC LIMIT 1
    """)
    pred = db.execute(sql_pred, {"cid": customer_id}).mappings().first()

    return {
        "customer": {
            "id": cust["id"],
            "customer_ref": cust["customer_ref"],
            "name": cust["name"],
            "email": cust["email"],
            "segment": cust["segment"],
            "acquisition_channel": cust["acquisition_channel"],
            "region": cust["region"],
            "signup_date": cust["signup_date"].strftime("%Y-%m-%d") if cust["signup_date"] else None,
            "is_active": cust["is_active"]
        },
        "transactions": txs,
        "recent_prediction": {
            "risk_score": float(pred["risk_score"]),
            "risk_category": pred["risk_category"],
            "priority_score": float(pred["priority_score"]),
            "details": pred["contributing_features"],
            "timestamp": pred["created_at"].strftime("%Y-%m-%d %H:%M")
        } if pred else None
    }
