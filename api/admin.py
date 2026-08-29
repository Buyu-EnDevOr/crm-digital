import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# 1. Apresentando a Chave Mestra para o Firebase
cred = credentials.Certificate("chave-firebase.json")
firebase_admin.initialize_app(cred)

# 2. Conectando ao Banco de Dados
db = firestore.client()

print("Conexão estabelecida! Buscando clientes...\n")
print("-" * 40)

# 3. O Python vai na pasta 'leads' e puxa todo mundo
clientes_ref = db.collection("leads")
clientes = clientes_ref.stream()

contador = 0
for cliente in clientes:
    contador += 1
    # Transformando os dados brutos em um dicionário do Python
    dados = cliente.to_dict()
    
    nome = dados.get("nome", "Sem Nome")
    telefone = dados.get("telefone", "Sem Telefone")
    polo = dados.get("polo", "Não definido")
    status = dados.get("status", "Não definido")
    
    print(f"Cliente {contador}: {nome}")
    print(f"WhatsApp: {telefone}")
    print(f"Polo: {polo} | Status: {status}")
    print("-" * 40)

if contador == 0:
    print("Nenhum cliente cadastrado ainda.")