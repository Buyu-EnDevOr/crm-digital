from flask import Flask, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

app = Flask(__name__)
CORS(app)
# Configuração de Segurança: Puxa a chave mestra
# O Python vai procurar a chave na pasta correta, não importa de onde o servidor inicie
# Descobre a pasta atual (api/), volta uma pasta para trás (raiz) e pega a chave
diretorio_api = os.path.dirname(os.path.abspath(__file__))
diretorio_raiz = os.path.dirname(diretorio_api)
caminho_chave = os.path.join(diretorio_raiz, 'chave-firebase.json')

cred = credentials.Certificate(caminho_chave)

# Evita inicializar o Firebase duas vezes (erro comum em APIs)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route('/api/status')
def status():
    return jsonify({"mensagem": "Servidor Python rodando perfeitamente!", "status": 200})

# Nova Rota: O carteiro que entrega a lista de clientes para o HTML
@app.route('/api/clientes')
def listar_clientes():
    try:
        clientes_ref = db.collection("leads")
        clientes_banco = clientes_ref.stream()
        
        lista_clientes = []
        for cliente in clientes_banco:
            dados = cliente.to_dict()
            # Adicionamos o ID único do Firebase caso você queira um botão de "Deletar" depois
            dados['id'] = cliente.id 
            lista_clientes.append(dados)
            
        return jsonify(lista_clientes)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Nova Rota: Deletar um cliente pelo ID
@app.route('/api/clientes/<id_cliente>', methods=['DELETE'])
def deletar_cliente(id_cliente):
    try:
        # Vai na pasta leads, procura o documento com esse ID e apaga
        db.collection("leads").document(id_cliente).delete()
        return jsonify({"mensagem": "Cliente deletado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=8080)