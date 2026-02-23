#!/usr/bin/env python3
"""Seed database with sample data for testing the claims system."""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session, engine
from app.models import Member, Provider, Procedure, Diagnosis
from app.enums import MemberStatus


async def seed_data():
    """Seed the database with sample data."""
    async with async_session() as db:
        print("🌱 Seeding database with sample data...")

        # Create sample members
        members = [
            Member(
                id="M123",
                name="John Doe",
                email="john.doe@example.com",
                phone_number="+254700000001",
                status=MemberStatus.ACTIVE,
                benefit_limit=Decimal("100000.00"),
                used_benefit=Decimal("0.00"),
            ),
            Member(
                id="M124",
                name="Jane Smith",
                email="jane.smith@example.com",
                phone_number="+254700000002",
                status=MemberStatus.ACTIVE,
                benefit_limit=Decimal("50000.00"),
                used_benefit=Decimal("10000.00"),
            ),
            Member(
                id="M125",
                name="Bob Johnson",
                email="bob.johnson@example.com",
                phone_number="+254700000003",
                status=MemberStatus.INACTIVE,
                benefit_limit=Decimal("75000.00"),
                used_benefit=Decimal("0.00"),
            ),
        ]

        # Create sample providers
        providers = [
            Provider(
                id="H456",
                name="Nairobi General Hospital",
                address="123 Hospital Road, Nairobi",
                phone_number="+254200000001",
                email="info@nairobigeneral.co.ke",
                is_active=True,
            ),
            Provider(
                id="H457",
                name="Mombasa Medical Center",
                address="456 Coast Avenue, Mombasa",
                phone_number="+254200000002",
                email="info@mombasamedical.co.ke",
                is_active=True,
            ),
            Provider(
                id="H458",
                name="Kisumu Health Clinic",
                address="789 Lake Road, Kisumu",
                phone_number="+254200000003",
                email="info@kisumuhealth.co.ke",
                is_active=False,
            ),
        ]

        # Create sample diagnoses
        diagnoses = [
            Diagnosis(
                code="D001",
                name="Malaria",
                description="Parasitic infection transmitted by mosquitoes",
            ),
            Diagnosis(
                code="D002",
                name="Typhoid Fever",
                description="Bacterial infection caused by Salmonella typhi",
            ),
            Diagnosis(
                code="D003",
                name="Pneumonia",
                description="Lung infection causing inflammation",
            ),
            Diagnosis(
                code="D004",
                name="Diabetes Type 2",
                description="Chronic condition affecting blood sugar regulation",
            ),
        ]

        # Create sample procedures
        procedures = [
            Procedure(
                code="P001",
                name="General Consultation",
                description="Standard medical consultation and examination",
                average_cost=Decimal("5000.00"),
            ),
            Procedure(
                code="P002",
                name="Blood Test Panel",
                description="Comprehensive blood analysis",
                average_cost=Decimal("8000.00"),
            ),
            Procedure(
                code="P003",
                name="X-Ray Imaging",
                description="Radiographic imaging procedure",
                average_cost=Decimal("12000.00"),
            ),
            Procedure(
                code="P004",
                name="Minor Surgery",
                description="Outpatient surgical procedure",
                average_cost=Decimal("25000.00"),
            ),
            Procedure(
                code="P005",
                name="Hospital Admission (3 days)",
                description="Inpatient care for 3 days",
                average_cost=Decimal("45000.00"),
            ),
        ]

        # Add all data
        db.add_all(members)
        db.add_all(providers)
        db.add_all(diagnoses)
        db.add_all(procedures)

        await db.commit()

        print("✅ Database seeded successfully!")
        print(f"   - {len(members)} members")
        print(f"   - {len(providers)} providers")
        print(f"   - {len(diagnoses)} diagnoses")
        print(f"   - {len(procedures)} procedures")


async def main():
    """Main entry point."""
    try:
        await seed_data()
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
