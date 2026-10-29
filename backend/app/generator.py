import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


CATEGORIES = [
    {"code": "CAT_SAAS", "name": "Software Subscriptions", "description": "Cloud and SaaS tools"},
    {"code": "CAT_HW", "name": "Hardware & Devices", "description": "Laptops, monitors and accessories"},
    {"code": "CAT_SERV", "name": "Professional Services", "description": "Consulting and implementation"},
    {"code": "CAT_OFFICE", "name": "Office Equipment", "description": "Ergonomic furniture and supplies"},
    {"code": "CAT_MAINT", "name": "Maintenance & Support", "description": "SLA and technical support"},
]

CHANNELS = ["Organic", "Direct Sales", "Partner Referral", "Paid Search", "Events"]
REGIONS = ["North America", "Europe", "Asia-Pacific", "Latin America"]
SEGMENT_ARCHETYPES = ["Frequent", "Declining", "VIP", "Irregular", "New", "Inactive"]


class SyntheticDataGenerator:
    """Generates realistic, reproducible SME business transaction data."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        random.seed(seed)

    def generate(
        self,
        n_customers: int = 400,
        start_date: datetime = datetime(2025, 1, 1),
        end_date: datetime = datetime(2026, 4, 1),
        corrupt: bool = False,
        corruption_rate: float = 0.05
    ) -> Dict[str, Any]:
        """Generate synthetic customers, categories, transactions, and activities."""
        categories = CATEGORIES

        # 1. Generate Customers
        customers = []
        total_days = (end_date - start_date).days

        for i in range(1, n_customers + 1):
            cust_ref = f"CUST-{i:05d}"
            # Signup distributed across the time horizon, front-loaded for realistic tenure
            signup_day_offset = int(self.rng.beta(2, 3) * (total_days - 60))
            signup_dt = start_date + timedelta(days=signup_day_offset)

            # Assign behavior archetype
            archetype = self.rng.choice(
                SEGMENT_ARCHETYPES,
                p=[0.25, 0.20, 0.10, 0.20, 0.15, 0.10]
            )
            channel = self.rng.choice(CHANNELS, p=[0.30, 0.25, 0.15, 0.20, 0.10])
            region = self.rng.choice(REGIONS, p=[0.45, 0.30, 0.15, 0.10])

            customers.append({
                "customer_ref": cust_ref,
                "name": f"Enterprise Account {i}",
                "email": f"billing{i}@enterprise{i}.com",
                "archetype": archetype,
                "acquisition_channel": channel,
                "region": region,
                "signup_date": signup_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "is_active": True
            })

        # 2. Generate Transactions based on archetypes
        transactions = []
        activities = []
        tx_counter = 1
        act_counter = 1

        for cust in customers:
            c_ref = cust["customer_ref"]
            archetype = cust["archetype"]
            c_signup = datetime.strptime(cust["signup_date"], "%Y-%m-%d %H:%M:%S")

            # Behavior parameters
            if archetype == "VIP":
                freq_lambda = 8  # transactions per month
                base_amount_mean, base_amount_sd = 1200.0, 350.0
                active_until = end_date
            elif archetype == "Frequent":
                freq_lambda = 6
                base_amount_mean, base_amount_sd = 450.0, 100.0
                active_until = end_date
            elif archetype == "Declining":
                freq_lambda = 4
                base_amount_mean, base_amount_sd = 300.0, 80.0
                # Becomes inactive 60-90 days before end_date
                drop_offset = int(self.rng.integers(60, 120))
                active_until = max(c_signup + timedelta(days=30), end_date - timedelta(days=drop_offset))
            elif archetype == "Irregular":
                freq_lambda = 2
                base_amount_mean, base_amount_sd = 600.0, 250.0
                active_until = end_date
            elif archetype == "New":
                freq_lambda = 3
                base_amount_mean, base_amount_sd = 250.0, 50.0
                # Recent signups
                active_until = end_date
            else:  # Inactive
                freq_lambda = 1
                base_amount_mean, base_amount_sd = 180.0, 40.0
                active_until = min(end_date, c_signup + timedelta(days=int(self.rng.integers(20, 60))))

            cur_time = c_signup + timedelta(days=int(self.rng.integers(1, 10)))

            while cur_time < active_until and cur_time < end_date:
                # Seasonal adjustment (higher sales at quarter ends)
                quarter_boost = 1.25 if cur_time.month in [3, 6, 9, 12] and cur_time.day > 20 else 1.0
                amount = float(max(25.0, self.rng.normal(base_amount_mean, base_amount_sd) * quarter_boost))

                # Category choice
                cat = self.rng.choice(categories)

                # Payment method & status (small realistic refund rate ~2%)
                is_refund = bool(self.rng.random() < 0.02)
                status = "refunded" if is_refund else "completed"

                tx_ref = f"TX-{tx_counter:07d}"
                transactions.append({
                    "transaction_ref": tx_ref,
                    "customer_ref": c_ref,
                    "category_code": cat["code"],
                    "timestamp": cur_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": round(amount, 2),
                    "status": status,
                    "payment_method": self.rng.choice(["credit_card", "ach", "wire_transfer"], p=[0.6, 0.3, 0.1]),
                    "is_refund": is_refund
                })
                tx_counter += 1

                # Generate companion activity log
                activities.append({
                    "customer_ref": c_ref,
                    "activity_type": "view_catalog",
                    "timestamp": (cur_time - timedelta(minutes=int(self.rng.integers(5, 60)))).strftime("%Y-%m-%d %H:%M:%S")
                })
                activities.append({
                    "customer_ref": c_ref,
                    "activity_type": "cart_update",
                    "timestamp": cur_time.strftime("%Y-%m-%d %H:%M:%S")
                })

                # Interval to next transaction: Poisson process via Exponential distribution
                days_to_next = float(self.rng.exponential(scale=30.0 / freq_lambda))
                cur_time += timedelta(days=max(1.0, days_to_next), hours=int(self.rng.integers(0, 23)))

        # 3. Optional Corruption for Data Ingestion & Quality Testing
        if corrupt:
            transactions = self._apply_corruption(transactions, customers, corruption_rate)

        return {
            "categories": categories,
            "customers": customers,
            "transactions": transactions,
            "activities": activities,
            "metadata": {
                "seed": self.seed,
                "n_customers": len(customers),
                "n_transactions": len(transactions),
                "n_activities": len(activities),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "is_corrupted": corrupt
            }
        }

    def _apply_corruption(
        self,
        transactions: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        rate: float
    ) -> List[Dict[str, Any]]:
        corrupted = [dict(tx) for tx in transactions]
        n_corrupt = int(len(corrupted) * rate)
        indices = self.rng.choice(len(corrupted), size=n_corrupt, replace=False)

        for idx in indices:
            corrupt_type = self.rng.choice([
                "duplicate_ref", "negative_amount", "invalid_timestamp",
                "missing_customer", "invalid_category", "null_amount"
            ])
            if corrupt_type == "duplicate_ref":
                corrupted[idx]["transaction_ref"] = corrupted[max(0, idx - 1)]["transaction_ref"]
            elif corrupt_type == "negative_amount":
                corrupted[idx]["amount"] = -round(abs(corrupted[idx]["amount"]), 2)
            elif corrupt_type == "invalid_timestamp":
                corrupted[idx]["timestamp"] = "INVALID_TIMESTAMP_STRING"
            elif corrupt_type == "missing_customer":
                corrupted[idx]["customer_ref"] = "NON_EXISTENT_CUST_99999"
            elif corrupt_type == "invalid_category":
                corrupted[idx]["category_code"] = "UNKNOWN_CAT_XYZ"
            elif corrupt_type == "null_amount":
                corrupted[idx]["amount"] = None

        return corrupted
