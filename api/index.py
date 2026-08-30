# 1. TODOS OS IMPORTS FICAM NO TOPO (adicionei o 'request' aqui)
from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

# 2. INICIALIZA O APLICATIVO E O BANCO DE DADOS
app = Flask(__name__)
CORS(app)

# Configuração de Segurança: Puxa a chave mestra
diretorio_api = os.path.dirname(os.path.abspath(__file__))
diretorio_raiz = os.path.dirname(diretorio_api)
caminho_chave = os.path.join(diretorio_raiz, 'chave-firebase.json')

cred = credentials.Certificate(caminho_chave)

# Evita inicializar o Firebase duas vezes
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()


# 3. AS ROTAS FICAM AQUI NO MEIO (depois do app e do db existirem)

@app.route('/api/status')
def status():
    return jsonify({"mensagem": "Servidor Python rodando perfeitamente!", "status": 200})

# Nova Rota (CREATE): Recebe os dados do formulário e salva no Firebase
@app.route('/api/clientes', methods=['POST'])
def criar_cliente():
    try:
        # Pega os dados que o JavaScript vai enviar
        novo_cliente = request.json 
        
        # Adiciona no Firebase na coleção 'leads'
        db.collection("leads").add(novo_cliente)
        
        return jsonify({"mensagem": "Cliente cadastrado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Rota (READ): O carteiro que entrega a lista de clientes para o HTML
@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    try:
        clientes_ref = db.collection("leads")
        clientes_banco = clientes_ref.stream()
        
        lista_clientes = []
        for cliente in clientes_banco:
            dados = cliente.to_dict()
            # Adicionamos o ID único do Firebase
            dados['id'] = cliente.id 
            lista_clientes.append(dados)
            
        return jsonify(lista_clientes)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Rota (DELETE): Deletar um cliente pelo ID
@app.route('/api/clientes/<id_cliente>', methods=['DELETE'])
def deletar_cliente(id_cliente):
    try:
        # Vai na pasta leads, procura o documento com esse ID e apaga
        db.collection("leads").document(id_cliente).delete()
        return jsonify({"mensagem": "Cliente deletado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# 4. INICIA O SERVIDOR (Sempre no final do arquivo)
if __name__ == '__main__':
    app.run(debug=True, port=8080)