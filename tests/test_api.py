from sqlalchemy import inspect, select

from app.models.entities import Approval, ApprovalDecision, Expense, Policy, User, UserRole


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
    response = client.get("/api/v1/users", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_web_interface_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "ReembolsaBR" in response.text
    assert client.get("/assets/styles.css").status_code == 200
    assert client.get("/demo").status_code == 200


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


def test_refresh_token_is_rotated(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Refresh Corp",
            "email": "refresh@example.com",
            "password": "senha-segura-123",
        },
    ).json()
    refreshed = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": registration["refresh_token"]}
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != registration["refresh_token"]
    replay = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": registration["refresh_token"]}
    )
    assert replay.status_code == 401


def test_high_value_expense_requires_two_approval_levels(client, auth_headers, db_session):
    created = client.post(
        "/api/v1/expenses",
        headers=auth_headers,
        json=expense_payload(amount="6000.00"),
    ).json()
    expense_id = created["id"]
    assert (
        client.post(f"/api/v1/expenses/{expense_id}/submit", headers=auth_headers).status_code
        == 200
    )

    first = client.post(
        f"/api/v1/expenses/{expense_id}/approve",
        headers=auth_headers,
        json={"comment": "Gestor aprovou"},
    )
    assert first.json()["status"] == "submitted"
    second = client.post(
        f"/api/v1/expenses/{expense_id}/approve",
        headers=auth_headers,
        json={"comment": "Financeiro aprovou"},
    )
    assert second.json()["status"] == "approved"
    decisions = list(db_session.scalars(select(Approval).order_by(Approval.level)))
    assert [item.decision for item in decisions] == [
        ApprovalDecision.approved,
        ApprovalDecision.approved,
    ]


def test_reports_erp_export_and_privacy_export(client, auth_headers):
    created = client.post(
        "/api/v1/expenses", headers=auth_headers, json=expense_payload(cost_center="SP-01")
    ).json()
    client.post(f"/api/v1/expenses/{created['id']}/submit", headers=auth_headers)
    client.post(f"/api/v1/expenses/{created['id']}/approve", headers=auth_headers)

    report = client.get("/api/v1/reports/expenses", headers=auth_headers)
    assert report.status_code == 200
    assert report.json()[0]["total"] == "89.90"
    erp = client.get("/api/v1/integrations/erp/approved-expenses", headers=auth_headers)
    assert erp.status_code == 200
    assert erp.json()["entries"][0]["cost_center"] == "SP-01"
    privacy = client.get("/api/v1/privacy/me/export", headers=auth_headers)
    assert privacy.status_code == 200
    assert privacy.json()["expenses"][0]["id"] == created["id"]


def test_receipt_upload(client, auth_headers, monkeypatch, tmp_path):
    from app.api.routes import expenses as expense_routes

    monkeypatch.setattr(expense_routes.settings, "receipt_storage_path", str(tmp_path))
    created = client.post("/api/v1/expenses", headers=auth_headers, json=expense_payload()).json()
    response = client.post(
        f"/api/v1/expenses/{created['id']}/receipt",
        headers=auth_headers,
        files={"receipt": ("nota.txt", b"TOTAL R$ 89,90", "text/plain")},
    )
    assert response.status_code == 200
    assert len(list(tmp_path.rglob("*.txt"))) == 1


def test_account_anonymization_revokes_access(client, auth_headers, db_session):
    response = client.delete("/api/v1/privacy/me", headers=auth_headers)
    assert response.status_code == 204
    user = db_session.scalar(select(User))
    assert not user.is_active
    assert user.email.endswith("@invalid.local")
    assert client.get("/api/v1/privacy/me/export", headers=auth_headers).status_code == 401
