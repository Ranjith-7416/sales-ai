from app.main import _normalize_lead_input_for_background
from app.schemas import LeadInputSchema


INQUIRIES = [
    "We need to process invoices and send extracted values to our ERP.",
    "Our support team needs a searchable knowledge workspace for internal policies.",
    "We are exploring automation and need help understanding what is possible.",
]


def test_arbitrary_customer_inquiries_are_preserved_independently():
    normalized = [
        _normalize_lead_input_for_background(
            LeadInputSchema(
                company_name=f"Customer {index}",
                contact_name=f"Contact {index}",
                email=f"contact{index}@example.test",
                inquiry_text=inquiry,
            )
        )
        for index, inquiry in enumerate(INQUIRIES, start=1)
    ]

    assert [item["inquiry_text"] for item in normalized] == INQUIRIES
    assert [item["company_name"] for item in normalized] == [
        "Customer 1",
        "Customer 2",
        "Customer 3",
    ]
    assert all(item["contact_name"] and item["email"] for item in normalized)
