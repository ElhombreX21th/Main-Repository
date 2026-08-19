#!/usr/bin/env python3
"""
Script de teste automático da API ReembolsaBR
Testa todo o fluxo: Register -> Login -> Policy -> Expense -> Approve
"""

import requests
import time
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print('='*60)

def test_health():
    """Testa se a API está no ar"""
    print_section("1. Verificando Saúde da API")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API está ONLINE e saudável!")
            print(f"   Resposta: {response.json()}")
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar à API em http://localhost:8000")
        print("   Verifique se o servidor está rodando: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_register():
    """Cria um usuário de teste"""
    print_section("2. Criando Usuário de Teste")
    
    # Gera dados únicos para evitar conflitos
    timestamp = int(time.time())
    user_data = {
        "email": f"teste{timestamp}@reembolsabr.com",
        "password": "Senha12345!",  # Mínimo 10 caracteres
        "organization_name": "Empresa Teste Ltda"  # Campo exigido pela API
        # full_name e country_code são opcionais
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ Usuário criado com sucesso!")
            print(f"   Email: {user_data['email']}")
            return user_data['email'], user_data['password']
        elif response.status_code == 400:
            print(f"⚠️  Usuário já existe ou erro: {response.json()}")
            # Tenta fazer login mesmo assim
            return user_data['email'], user_data['password']
        else:
            print(f"❌ Erro ao criar usuário: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None, None

def test_login(email, password):
    """Faz login e retorna o token"""
    print_section("3. Realizando Login")
    
    login_data = {
        "username": email,  # OAuth2 usa 'username' para email
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/token", data=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print("✅ Login realizado com sucesso!")
                print(f"   Token: {token[:50]}...")
                return token
            else:
                print(f"❌ Token não encontrado na resposta: {data}")
                return None
        else:
            print(f"❌ Erro no login: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_create_policy(token):
    """Cria uma política de reembolso"""
    print_section("4. Criando Política de Reembolso")
    
    policy_data = {
        "name": "Política de Viagens 2025",
        "description": "Reembolso para despesas de viagens corporativas",
        "max_amount": 5000.00,
        "currency": "BRL",
        "allowed_categories": ["transporte", "alimentacao", "hospedagem"],
        "requires_receipt": True,
        "approval_required": True
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/policies/",
            json=policy_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ Política criada com sucesso!")
            print(f"   ID: {data.get('id')}")
            print(f"   Nome: {data.get('name')}")
            print(f"   Valor Máximo: R$ {data.get('max_amount')}")
            return data.get('id')
        else:
            print(f"❌ Erro ao criar política: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_create_expense(token, policy_id):
    """Cria uma despesa"""
    print_section("5. Criando Despesa de Teste")
    
    expense_data = {
        "description": "Almoço com cliente potencial",
        "amount": 150.75,
        "currency": "BRL",
        "category": "alimentacao",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "policy_id": policy_id,
        "notes": "Reunião importante no centro de SP"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/expenses/",
            json=expense_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ Despesa criada com sucesso!")
            print(f"   ID: {data.get('id')}")
            print(f"   Descrição: {data.get('description')}")
            print(f"   Valor: R$ {data.get('amount')}")
            print(f"   Status: {data.get('status')}")
            return data.get('id')
        else:
            print(f"❌ Erro ao criar despesa: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_list_expenses(token):
    """Lista todas as despesas"""
    print_section("6. Listando Despesas")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/expenses/",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            expenses = data.get('items', []) if isinstance(data, dict) else data
            print(f"✅ Encontradas {len(expenses)} despesa(s)!")
            for exp in expenses:
                print(f"   - {exp.get('description')}: R$ {exp.get('amount')} ({exp.get('status')})")
            return expenses
        else:
            print(f"❌ Erro ao listar: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def test_approve_expense(token, expense_id):
    """Aprova uma despesa"""
    print_section("7. Aprovando Despesa")
    
    if not expense_id:
        print("⚠️  Nenhum ID de despesa para aprovar")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/expenses/{expense_id}/approve",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ Despesa APROVADA com sucesso!")
            print(f"   ID: {data.get('id')}")
            print(f"   Status atual: {data.get('status')}")
            print(f"   Aprovado por: {data.get('approved_by', 'N/A')}")
            return True
        else:
            print(f"❌ Erro ao aprovar: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🧪 TESTE AUTOMÁTICO DA API REEMBOLSABR")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Início: {datetime.now().strftime('%H:%M:%S')}")
    
    # 1. Health Check
    if not test_health():
        print("\n❌ TESTE ABORTADO: API não está disponível")
        return
    
    # 2. Register
    email, password = test_register()
    if not email:
        print("\n⚠️  Continuando sem usuário novo...")
        return
    
    # 3. Login
    token = test_login(email, password)
    if not token:
        print("\n❌ TESTE ABORTADO: Não foi possível fazer login")
        return
    
    # 4. Create Policy
    policy_id = test_create_policy(token)
    if not policy_id:
        print("\n⚠️  Continuando sem política...")
    
    # 5. Create Expense
    expense_id = test_create_expense(token, policy_id)
    
    # 6. List Expenses
    test_list_expenses(token)
    
    # 7. Approve Expense
    if expense_id:
        test_approve_expense(token, expense_id)
    
    print("\n" + "="*60)
    print("✅ TESTE CONCLUÍDO!")
    print(f"Fim: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
