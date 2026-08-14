from sqlalchemy import inspect, select

from app.models.entities import Expense, Policy, User, UserRole


def expense_payload(**changes):
    payload = {
        "category": "meals",
        "amount": "89.90",
        "currency": "brl",
        "expense_date": "2026-08-14",
        "merchant_tax_id": "12.345.678/0001-90",
        "invoice_key": "1" * 44,
        "country_code": "br",
    }
    payload.update(changes)
    return payload


def test_admin_creates_employee_and_approver(client, auth_headers, db_session):
    for role in ("employee", "approver"):
        response = client.post(
            "/api/v1/users",
            headers=auth_headers,
            json={
                "email": f"{role}@example.com",
                "password": "senha-segura-123",
                "role": role,
            },
        )
        assert response.status_code == 201
        assert response.json()["role"] == role

    users = list(db_session.scalars(select(User).where(User.role != UserRole.admin)))
    assert {user.role for user in users} == {UserRole.employee, UserRole.approver}


def test_admin_cannot_create_another_admin(client, auth_headers):
    response = client.post(
        "/api/v1/users",
        headers=auth_headers,
        json={
            "email": "other-admin@example.com",
            "password": "senha-segura-123",
            "role": "admin",
        },
    )
    assert response.status_code == 422


def test_policy_and_expense_codes_are_uppercase(client, auth_headers, db_session):
    policy_response = client.post(
        "/api/v1/policies",
        headers=auth_headers,
        json={
            "category": "meals",
            "country_code": "br",
            "currency": "brl",
            "max_amount": "150.00",
        },
    )
    assert policy_response.status_code == 201
    expense_response = client.post("/api/v1/expenses", headers=auth_headers, json=expense_payload())
    assert expense_response.status_code == 201

    policy = db_session.scalar(select(Policy))
    expense = db_session.scalar(select(Expense))
    assert (policy.country_code, policy.currency) == ("BR", "BRL")
    assert (expense.country_code, expense.currency) == ("BR", "BRL")


def test_duplicate_invoice_key_returns_conflict(client, auth_headers):
    assert (
        client.post("/api/v1/expenses", headers=auth_headers, json=expense_payload()).status_code
        == 201
    )
    duplicate = expense_payload(
        merchant_tax_id="98.765.432/0001-10",
        expense_date="2026-08-15",
        amount="10.00",
    )
    assert client.post("/api/v1/expenses", headers=auth_headers, json=duplicate).status_code == 409


def test_duplicate_merchant_date_amount_returns_conflict(client, auth_headers):
    first = expense_payload(invoice_key="1" * 44)
    duplicate = expense_payload(invoice_key="2" * 44)
    assert client.post("/api/v1/expenses", headers=auth_headers, json=first).status_code == 201
    assert client.post("/api/v1/expenses", headers=auth_headers, json=duplicate).status_code == 409


def test_database_declares_both_duplicate_constraints(db_session):
    constraints = {
        item["name"] for item in inspect(db_session.bind).get_unique_constraints("expenses")
    }
    assert "uq_expense_invoice_key" in constraints
    assert "uq_expense_merchant_date_amount" in constraints
    assert db_session.scalar(select(Expense)) is None
