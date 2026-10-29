import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.models import (
    Customer, ProductCategory, Transaction, CustomerActivity, DatasetBatch, IngestionRejection
)


class IngestionEngine:
    """Robust, transactional ingestion engine with validation, rejection tracking, and metadata."""

    def __init__(self, db: Session):
        self.db = db

    def ingest_payload(
        self,
        payload: Dict[str, Any],
        source_type: str = "synthetic"
    ) -> Dict[str, Any]:
        """Ingest complete dataset dictionary (categories, customers, transactions, activities)."""
        batch_ref = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        batch = DatasetBatch(
            batch_ref=batch_ref,
            source_type=source_type,
            records_received=0,
            records_accepted=0,
            records_rejected=0,
            status="processing"
        )
        self.db.add(batch)
        self.db.flush()

        rejections = []
        accepted_txs = 0

        # 1. Upsert Categories
        cat_map: Dict[str, int] = {}
        for cat_data in payload.get("categories", []):
            code = str(cat_data.get("code", "")).strip()
            if not code:
                continue
            cat = self.db.query(ProductCategory).filter_by(code=code).first()
            if not cat:
                cat = ProductCategory(
                    code=code,
                    name=cat_data.get("name", code),
                    description=cat_data.get("description", "")
                )
                self.db.add(cat)
                self.db.flush()
            cat_map[code] = cat.id

        # 2. Ingest Customers
        cust_map: Dict[str, int] = {}
        # Preload existing customers
        existing_custs = self.db.query(Customer.customer_ref, Customer.id).all()
        for ref, cid in existing_custs:
            cust_map[ref] = cid

        for c_data in payload.get("customers", []):
            c_ref = str(c_data.get("customer_ref", "")).strip()
            if not c_ref:
                continue
            if c_ref not in cust_map:
                try:
                    s_date = datetime.strptime(str(c_data["signup_date"]).replace("T", " "), "%Y-%m-%d %H:%M:%S")
                except Exception:
                    s_date = datetime.utcnow()

                customer = Customer(
                    customer_ref=c_ref,
                    name=c_data.get("name", f"Account {c_ref}"),
                    email=c_data.get("email"),
                    segment=c_data.get("archetype", c_data.get("segment", "New")),
                    acquisition_channel=c_data.get("acquisition_channel", "Organic"),
                    region=c_data.get("region", "North America"),
                    signup_date=s_date,
                    is_active=c_data.get("is_active", True)
                )
                self.db.add(customer)
                self.db.flush()
                cust_map[c_ref] = customer.id

        # 3. Ingest Transactions with rigorous validation
        raw_txs = payload.get("transactions", [])
        batch.records_received = len(raw_txs)

        # Check existing transaction_refs to prevent duplicates
        seen_refs = set(
            r[0] for r in self.db.query(Transaction.transaction_ref).all()
        )
        batch_seen_refs = set()

        for idx, tx in enumerate(raw_txs):
            tx_ref = str(tx.get("transaction_ref", "")).strip()
            c_ref = str(tx.get("customer_ref", "")).strip()
            cat_code = str(tx.get("category_code", "")).strip()
            amount_val = tx.get("amount")
            ts_val = tx.get("timestamp")

            # Validation 1: Required reference
            if not tx_ref:
                rejections.append(IngestionRejection(
                    batch_id=batch.id,
                    row_index=idx,
                    raw_record=str(tx)[:400],
                    reason="Missing transaction_ref"
                ))
                continue

            # Validation 2: Duplicate check
            if tx_ref in seen_refs or tx_ref in batch_seen_refs:
                rejections.append(IngestionRejection(
                    batch_id=batch.id,
                    row_index=idx,
                    raw_record=str(tx)[:400],
                    reason=f"Duplicate transaction_ref: {tx_ref}"
                ))
                continue

            # Validation 3: Customer foreign key resolution
            if c_ref not in cust_map:
                rejections.append(IngestionRejection(
                    batch_id=batch.id,
                    row_index=idx,
                    raw_record=str(tx)[:400],
                    reason=f"Unresolved customer_ref: {c_ref}"
                ))
                continue

            # Validation 4: Timestamp format
            try:
                tx_time = datetime.strptime(str(ts_val).replace("T", " "), "%Y-%m-%d %H:%M:%S")
            except Exception:
                rejections.append(IngestionRejection(
                    batch_id=batch.id,
                    row_index=idx,
                    raw_record=str(tx)[:400],
                    reason=f"Invalid timestamp format: {ts_val}"
                ))
                continue

            # Validation 5: Amount validity (must be positive numeric)
            try:
                amount = float(amount_val)
                if amount <= 0:
                    raise ValueError("Amount must be greater than zero")
            except Exception as e:
                rejections.append(IngestionRejection(
                    batch_id=batch.id,
                    row_index=idx,
                    raw_record=str(tx)[:400],
                    reason=f"Invalid amount '{amount_val}': {str(e)}"
                ))
                continue

            # Validation 6: Category resolution
            cat_id = cat_map.get(cat_code)
            if not cat_id and cat_code:
                rejections.append(IngestionRejection(
                    batch_id=batch.id,
                    row_index=idx,
                    raw_record=str(tx)[:400],
                    reason=f"Unknown category_code: {cat_code}"
                ))
                continue

            batch_seen_refs.add(tx_ref)

            new_tx = Transaction(
                transaction_ref=tx_ref,
                customer_id=cust_map[c_ref],
                category_id=cat_id,
                timestamp=tx_time,
                amount=round(amount, 2),
                status=tx.get("status", "completed"),
                payment_method=tx.get("payment_method", "credit_card"),
                is_refund=bool(tx.get("is_refund", False))
            )
            self.db.add(new_tx)
            accepted_txs += 1

            if accepted_txs % 1000 == 0:
                self.db.flush()

        # 4. Ingest Activities
        for act in payload.get("activities", []):
            c_ref = str(act.get("customer_ref", "")).strip()
            if c_ref in cust_map:
                try:
                    act_time = datetime.strptime(str(act.get("timestamp")).replace("T", " "), "%Y-%m-%d %H:%M:%S")
                    activity = CustomerActivity(
                        customer_id=cust_map[c_ref],
                        activity_type=act.get("activity_type", "view_catalog"),
                        timestamp=act_time
                    )
                    self.db.add(activity)
                except Exception:
                    continue

        # 5. Save Rejections and Finalize Batch
        for rej in rejections:
            self.db.add(rej)

        batch.records_accepted = accepted_txs
        batch.records_rejected = len(rejections)
        batch.status = "completed" if len(rejections) == 0 else ("partial" if accepted_txs > 0 else "failed")
        batch.rejection_summary = {
            "total_rejected": len(rejections),
            "reasons": {
                r.reason: len([x for x in rejections if x.reason == r.reason])
                for r in rejections[:50]
            }
        }

        self.db.commit()

        return {
            "batch_ref": batch.batch_ref,
            "status": batch.status,
            "records_received": batch.records_received,
            "records_accepted": batch.records_accepted,
            "records_rejected": batch.records_rejected,
            "rejection_sample": [
                {"row": r.row_index, "reason": r.reason} for r in rejections[:10]
            ]
        }
