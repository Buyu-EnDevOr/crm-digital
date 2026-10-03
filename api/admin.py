import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# 1. Apresentando a Chave Mestra para o Firebase
cred = credentials.Certificate("chave-firebase.json")
firebase_admin.initialize_app(cred)

# 2. Conectando ao Banco de Dados
db = firestore.client()

print("Conexão estabelecida! Buscando clientes e leads...\n")
print("-" * 50)

# 3. O Python vai na coleção 'leads' e puxa todos os documentos
clientes_ref = db.collection("leads")
clientes = clientes_ref.stream()

contador = 0

for cliente in clientes:
    contador += 1
    # Transformando os dados brutos num dicionário do Python
    dados = cliente.to_dict()
    
    nome = dados.get("nome", "Sem Nome")
    telefone = dados.get("telefone", "Sem Telefone")
    
    # NOVAS VARIÁVEIS DE ENDEREÇO (Substituindo o antigo 'polo')
    rua = dados.get("rua", "Não definida")
    bairro = dados.get("bairro", "Não definido")
    
    # STATUS NO FUNIL DE VENDAS
    status = dados.get("status", "indefinido").upper()
    
    print(f"Cliente {contador}: {nome}")
    print(f"WhatsApp: {telefone}")
    print(f"Endereço: {rua} - Bairro {bairro}")
    print(f"Status no Funil: [{status}]")
    print("-" * 50)

if contador == 0:
    print("Nenhum cliente cadastrado ainda. A base de dados está vazia.")