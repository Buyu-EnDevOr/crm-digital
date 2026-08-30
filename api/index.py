from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

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

@app.route('/api/status')
def status():
    return jsonify({"mensagem": "Servidor Python rodando perfeitamente!", "status": 200})

# CREATE: Recebe os dados do formulário e salva
@app.route('/api/clientes', methods=['POST'])
def criar_cliente():
    try:
        novo_cliente = request.json 
        db.collection("leads").add(novo_cliente)
        return jsonify({"mensagem": "Cliente cadastrado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# READ: Entrega a lista de clientes para o HTML
@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    try:
        clientes_ref = db.collection("leads")
        clientes_banco = clientes_ref.stream()
        
        lista_clientes = []
        for cliente in clientes_banco:
            dados = cliente.to_dict()
            dados['id'] = cliente.id 
            lista_clientes.append(dados)
            
        return jsonify(lista_clientes)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# DELETE: Deletar um cliente pelo ID
@app.route('/api/clientes/<id_cliente>', methods=['DELETE'])
def deletar_cliente(id_cliente):
    try:
        db.collection("leads").document(id_cliente).delete()
        return jsonify({"mensagem": "Cliente deletado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# UPDATE: Atualizar os dados de um cliente existente (O PASSO 1 ENTROU AQUI)
@app.route('/api/clientes/<id_cliente>', methods=['PUT'])
def atualizar_cliente(id_cliente):
    try:
        dados_atualizados = request.json
        # O 'update' do Firebase altera apenas os campos enviados, sem apagar o resto
        db.collection("leads").document(id_cliente).update(dados_atualizados)
        return jsonify({"mensagem": "Cliente atualizado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080)