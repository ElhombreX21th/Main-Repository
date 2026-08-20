from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def register_admin(
    client: TestClient, email: str = "ana@example.com", organization: str = "Acme Brasil"
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Ana Silva",
            "organization_name": organization,
            "email": email,
            "password": "Senha-forte-123",
            "country_code": "BR",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["first_name"] == "Ana"
    return {"Authorization": f"Bearer {body['access_token']}"}


def login(client: TestClient, email: str, password: str = "Senha-forte-123") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def test_expense_lifecycle_audit_and_tenant_isolation(client: TestClient):
    headers = register_admin(client)

    assert client.get("/api/v1/expenses").status_code == 401
    duplicate_org_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Ana Souza",
            "organization_name": " Acme Brasil ",
            "email": "ana2@example.com",
            "password": "Senha-forte-123",
            "country_code": "br",
        },
    )
    assert duplicate_org_response.status_code == 409
    assert duplicate_org_response.json()["detail"] == "Esta organização já está cadastrada."

    policy_response = client.post(
        "/api/v1/policies",
        headers=headers,
        json={
            "category": " lunch ",
            "country_code": "br",
            "currency": "brl",
            "max_amount": 100,
        },
    )
    assert policy_response.status_code == 201, policy_response.text
    policy = policy_response.json()
    assert policy["category"] == "lunch"
    assert policy["country_code"] == "BR"
    assert policy["currency"] == "BRL"

    duplicate_policy_response = client.post(
        "/api/v1/policies",
        headers=headers,
        json={
            "category": "lunch",
            "country_code": "BR",
            "currency": "BRL",
            "max_amount": 200,
        },
    )
    assert duplicate_policy_response.status_code == 409
    assert duplicate_policy_response.json()["detail"] == "Esta política já está cadastrada."

    users = [
        ("Pedro Funcionario", "pedro@example.com", "employee"),
        ("Carla Aprovadora", "carla@example.com", "approver"),
    ]
    for full_name, email, role in users:
        user_response = client.post(
            "/api/v1/auth/users",
            headers=headers,
            json={
                "full_name": full_name,
                "email": email,
                "password": "Senha-forte-123",
                "role": role,
            },
        )
        assert user_response.status_code == 201, user_response.text
        assert user_response.json()["role"] == role

    listed_users = client.get("/api/v1/auth/users", headers=headers)
    assert listed_users.status_code == 200, listed_users.text
    assert {user["email"] for user in listed_users.json()} == {
        "ana@example.com",
        "pedro@example.com",
        "carla@example.com",
    }

    employee_headers = login(client, "pedro@example.com")
    approver_headers = login(client, "carla@example.com")
    assert client.get("/api/v1/auth/users", headers=employee_headers).status_code == 403

    expense_payload = {
        "category": " lunch ",
        "amount": 120.5,
        "currency": "brl",
        "expense_date": "2026-08-20",
        "merchant_tax_id": "12.345.678/0001-90",
        "merchant_city": "Sao Paulo",
        "merchant_state": "sp",
        "invoice_key": "12345678901234567890123456789012345678901234",
        "country_code": "br",
        "description": "Almoco com cliente",
    }
    expense_response = client.post(
        "/api/v1/expenses", headers=employee_headers, json=expense_payload
    )
    assert expense_response.status_code == 201, expense_response.text
    expense = expense_response.json()
    assert expense["status"] == "draft"
    assert expense["category"] == "lunch"
    assert expense["currency"] == "BRL"
    assert expense["country_code"] == "BR"
    assert expense["merchant_state"] == "SP"
    assert expense["policy_violation"] == "Limite: BRL 100.00"

    duplicate_response = client.post(
        "/api/v1/expenses", headers=employee_headers, json=expense_payload
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Esta despesa já foi registrada."

    workflow_response = client.post(
        f"/api/v1/expenses/{expense['id']}/submit",
        headers=employee_headers,
    )
    assert workflow_response.status_code == 200, workflow_response.text
    assert workflow_response.json()["status"] == "submitted"

    forbidden_response = client.post(
        f"/api/v1/expenses/{expense['id']}/approve",
        headers=employee_headers,
    )
    assert forbidden_response.status_code == 403

    workflow_response = client.post(
        f"/api/v1/expenses/{expense['id']}/approve",
        headers=approver_headers,
    )
    assert workflow_response.status_code == 200, workflow_response.text
    assert workflow_response.json()["status"] == "approved"

    workflow_response = client.post(
        f"/api/v1/expenses/{expense['id']}/reimburse",
        headers=headers,
    )
    assert workflow_response.status_code == 200, workflow_response.text
    assert workflow_response.json()["status"] == "reimbursed"

    audit_response = client.get("/api/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200, audit_response.text
    audit_actions = {entry["action"] for entry in audit_response.json()}
    assert {"created", "submit", "approve", "reimburse"} <= audit_actions

    other_headers = register_admin(client, email="bia@example.com", organization="Beta Brasil")
    assert client.get("/api/v1/expenses", headers=other_headers).json() == []
    other_expense_response = client.post(
        "/api/v1/expenses", headers=other_headers, json=expense_payload
    )
    assert other_expense_response.status_code == 201, other_expense_response.text
