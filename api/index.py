from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json # <-- NOVO: Precisamos disso para ler a chave da Vercel
import mercadopago
app = Flask(__name__)
CORS(app)

# Tenta pegar a chave do "cofre" da Vercel
firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')

if firebase_creds_json:
    # SE ESTIVER NA VERCEL: Usa a variável de ambiente
    cred_dict = json.loads(firebase_creds_json)
    
    # IMPORTANTE: Limpeza das quebras de linha que a Vercel costuma bagunçar
    if '\\n' in cred_dict.get('private_key', ''):
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
        
    cred = credentials.Certificate(cred_dict)
else:
    # SE ESTIVER NO SEU PC: Usa o arquivo físico .json
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

# UPDATE: Atualizar os dados de um cliente existente
@app.route('/api/clientes/<id_cliente>', methods=['PUT'])
def atualizar_cliente(id_cliente):
    try:
        dados_atualizados = request.json
        # O 'update' do Firebase altera apenas os campos enviados, sem apagar o resto
        db.collection("leads").document(id_cliente).update(dados_atualizados)
        return jsonify({"mensagem": "Cliente atualizado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
# ==========================================
# ROTAS DA VITRINE (CONFIGURAÇÕES DO SITE)
# ==========================================

@app.route('/api/config', methods=['GET'])
def obter_configuracoes():
    try:
        # Busca o documento 'vitrine' dentro da coleção 'settings'
        doc = db.collection("settings").document("vitrine").get()
        if doc.exists:
            return jsonify(doc.to_dict()), 200
        else:
            # Se for a primeira vez e o banco estiver vazio, envia um padrão visual
            padrao = {
                "titulo": "CRM-DIGITAL",
                "subtitulo": "modelo teste",
                "imagem_url": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
                "descricao": "Serviços digitais de escrita criativa e redação estratégica.\nTransformamos ideias em textos que convertem.",
                "contato": "(00) 00000-0000"
            }
            return jsonify(padrao), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/config', methods=['PUT'])
def atualizar_configuracoes():
    try:
        novos_dados = request.json
        # O merge=True garante que ele crie o documento caso não exista no Firebase
        db.collection("settings").document("vitrine").set(novos_dados, merge=True)
        return jsonify({"mensagem": "Vitrine atualizada com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    # ==========================================
# ROTA DE PAGAMENTO (MERCADO PAGO)
# ==========================================
@app.route('/api/pagamento', methods=['POST'])
def gerar_pagamento():
    try:
        # 1. Conectando com a sua conta do Mercado Pago
        # Você vai trocar isso pela sua chave Access Token de Teste
        sdk = mercadopago.SDK("SEU_ACCESS_TOKEN_DE_TESTE_AQUI")

        # 2. Criando o carrinho de compras (Preferência)
        preference_data = {
            "items": [
                {
                    "title": "Consultoria de Escrita Criativa",
                    "description": "Sessão de 1 hora de consultoria.",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": 10.00
                }
            ],
            # Para onde o cliente volta depois de pagar
            "back_urls": {
                "success": "http://127.0.0.1:5500/public/sucesso.html",
                "failure": "http://127.0.0.1:5500/public/erro.html",
                "pending": "http://127.0.0.1:5500/public/pendente.html"
            },
            "auto_return": "approved"
        }

        # 3. Enviando para o Mercado Pago e pegando o link gerado
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        # 4. Devolvendo o link de checkout (init_point) para o JavaScript
        return jsonify({"link_checkout": preference["init_point"]}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=8080)