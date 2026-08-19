"""
Script de Teste Automático da API ReembolsaBR
Rodar com: python test_api_manual.py
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def print_step(title, data=None, status=None):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    if status:
        print(f"Status: {status}")
    if data:
        print(f"Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
    print('='*60)

def run_tests():
    session = requests.Session()
    
    # 1. Health Check
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print_step("1. Verificando Saúde da API", resp.json(), resp.status_code)
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        print("⚠️ Certifique-se de que o servidor está rodando: uvicorn main:app --reload")
        return

    # 2. Registro de Usuário
    user_data = {
        "email": f"teste_{int(time.time())}@empresa.com",
        "password": "senha123",
        "full_name": "Usuário Teste",
        "company_name": "Empresa Teste LTDA"
    }
    resp = session.post(f"{BASE_URL}/auth/register", json=user_data)
    print_step("2. Registrando Novo Usuário", resp.json() if resp.ok else resp.text, resp.status_code)
    
    if not resp.ok:
        # Tenta login se já existir
        print("⚠️ Usuário pode já existir, tentando login...")
        login_data = {"email": user_data["email"], "password": "senha123"}
        resp = session.post(f"{BASE_URL}/auth/login", data=login_data)
        print_step("Login Alternativo", resp.json() if resp.ok else resp.text, resp.status_code)

    # 3. Login (Obter Token)
    login_data = {"email": user_data["email"], "password": "senha123"}
    resp = session.post(f"{BASE_URL}/auth/login", data=login_data)
    if resp.ok:
        token = resp.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print_step("3. Login Realizado (Token Obtido)", {"token": f"{token[:20]}..."}, resp.status_code)
    else:
        print_step("3. Falha no Login", resp.text, resp.status_code)
        return

    # 4. Criar Política de Reembolso
    policy_data = {
        "name": "Política Padrão",
        "description": "Reembolso para despesas de viagem e alimentação",
        "max_amount": 5000.0,
        "require_receipt": True,
        "allowed_categories": ["transporte", "alimentacao", "hospedagem"]
    }
    resp = session.post(f"{BASE_URL}/policies/", json=policy_data)
    print_step("4. Criando Política de Reembolso", resp.json() if resp.ok else resp.text, resp.status_code)
    policy_id = resp.json().get("id") if resp.ok else None

    # 5. Criar Despesa
    expense_data = {
        "description": "Almoço com cliente",
        "amount": 150.50,
        "currency": "BRL",
        "category": "alimentacao",
        "date": "2024-05-20",
        "policy_id": policy_id
    }
    # Remove policy_id se for None para evitar erro
    if not policy_id:
        expense_data.pop("policy_id")
        
    resp = session.post(f"{BASE_URL}/expenses/", json=expense_data)
    print_step("5. Criando Despesa", resp.json() if resp.ok else resp.text, resp.status_code)
    expense_id = resp.json().get("id") if resp.ok else None

    # 6. Listar Despesas
    resp = session.get(f"{BASE_URL}/expenses/")
    print_step("6. Listando Minhas Despesas", resp.json() if resp.ok else resp.text, resp.status_code)

    # 7. Aprovar Despesa (Se houver ID)
    if expense_id:
        resp = session.post(f"{BASE_URL}/expenses/{expense_id}/approve")
        print_step("7. Aprovando Despesa", resp.json() if resp.ok else resp.text, resp.status_code)

    print("\n✅ Testes Concluídos!")

if __name__ == "__main__":
    run_tests()
