from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json
import stripe

app = Flask(__name__)
CORS(app)

# Tenta pegar a chave do "cofre" da Vercel
firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')

if firebase_creds_json:
    cred_dict = json.loads(firebase_creds_json)
    if '\\n' in cred_dict.get('private_key', ''):
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
    cred = credentials.Certificate(cred_dict)
else:
    diretorio_api = os.path.dirname(os.path.abspath(__file__))
    diretorio_raiz = os.path.dirname(diretorio_api)
    caminho_chave = os.path.join(diretorio_raiz, 'chave-firebase.json')
    cred = credentials.Certificate(caminho_chave)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route('/api/status')
def status():
    return jsonify({"mensagem": "Servidor Python rodando perfeitamente!", "status": 200})

# ==========================================
# ROTA DE AUTOMAÇÃO CRM
# ==========================================
@app.route('/api/sync_user', methods=['POST'])
def sincronizar_usuario():
    try:
        dados = request.json
        uid = dados.get('uid')
        
        if not uid:
            return jsonify({"erro": "UID não fornecido"}), 400
            
        cliente_ref = db.collection("leads").document(uid)
        doc = cliente_ref.get()
        
        if not doc.exists:
            novo_cliente = {
                "nome": dados.get('nome', 'Sem Nome'),
                "email": dados.get('email', ''),
                "foto_url": dados.get('foto', ''),
                "telefone": "-", 
                "polo": "-",     
                "status": "prospeccao", 
                "historico_compras": [], 
                "ultimo_acesso": firestore.SERVER_TIMESTAMP
            }
            cliente_ref.set(novo_cliente)
            return jsonify({"mensagem": "Novo lead cadastrado no funil!", "novo": True}), 201
        else:
            cliente_ref.update({
                "foto_url": dados.get('foto', ''),
                "ultimo_acesso": firestore.SERVER_TIMESTAMP
            })
            return jsonify({"mensagem": "Login registrado com sucesso.", "novo": False}), 200
            
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ==========================================
# CRUD DE CLIENTES (ADMIN)
# ==========================================
@app.route('/api/clientes', methods=['POST'])
def criar_cliente():
    try:
        novo_cliente = request.json 
        db.collection("leads").add(novo_cliente)
        return jsonify({"mensagem": "Cliente cadastrado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    try:
        clientes_ref = db.collection("leads").stream()
        lista_clientes = []
        for cliente in clientes_ref:
            dados = cliente.to_dict()
            dados['id'] = cliente.id 
            lista_clientes.append(dados)
        return jsonify(lista_clientes)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/clientes/<id_cliente>', methods=['DELETE'])
def deletar_cliente(id_cliente):
    try:
        db.collection("leads").document(id_cliente).delete()
        return jsonify({"mensagem": "Cliente deletado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/clientes/<id_cliente>', methods=['PUT'])
def atualizar_cliente(id_cliente):
    try:
        dados_atualizados = request.json
        db.collection("leads").document(id_cliente).update(dados_atualizados)
        return jsonify({"mensagem": "Cliente atualizado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ==========================================
# ROTAS DA VITRINE (HOME)
# ==========================================
@app.route('/api/config', methods=['GET'])
def obter_configuracoes():
    try:
        doc = db.collection("settings").document("vitrine").get()
        if doc.exists:
            return jsonify(doc.to_dict()), 200
        else:
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
        db.collection("settings").document("vitrine").set(novos_dados, merge=True)
        return jsonify({"mensagem": "Vitrine atualizada com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ==========================================
# ROTAS DE PRODUTOS (CATÁLOGO)
# ==========================================
@app.route('/api/produtos', methods=['POST'])
def criar_produto():
    try:
        novo_produto = request.json
        db.collection("produtos").add(novo_produto)
        return jsonify({"mensagem": "Produto criado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/produtos', methods=['GET'])
def listar_produtos():
    try:
        produtos_ref = db.collection("produtos").stream()
        lista_produtos = []
        for p in produtos_ref:
            dados = p.to_dict()
            dados['id'] = p.id
            lista_produtos.append(dados)
        return jsonify(lista_produtos), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/produtos/<id_produto>', methods=['DELETE'])
def deletar_produto(id_produto):
    try:
        db.collection("produtos").document(id_produto).delete()
        return jsonify({"mensagem": "Produto deletado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ==========================================
# CHECKOUT STRIPE 100% DINÂMICO
# ==========================================
@app.route('/api/pagamento', methods=['POST'])
def gerar_pagamento():
    try:
        chave_stripe = os.environ.get("STRIPE_KEY")
        if not chave_stripe:
            return jsonify({"erro": "Chave do Stripe não encontrada nas configurações da Vercel."}), 500
            
        stripe.api_key = chave_stripe
        dados = request.json or {}

        nome = dados.get('nome', 'Serviço Digital')
        descricao = dados.get('descricao', 'Contratação de serviço via CRM Digital')
        valor = float(dados.get('valor', 10.0))
        uid_cliente = dados.get('uid_cliente') # <--- NOVO: Recebe o ID do cliente logado

        # Stripe calcula em centavos
        valor_centavos = int(round(valor * 100))
        if valor_centavos < 50:
            valor_centavos = 50 

        # <--- NOVO: Atualiza o status do cliente no Firebase para "Em Negociação"
        if uid_cliente:
            try:
                db.collection("leads").document(uid_cliente).update({
                    "status": "negociacao"
                })
            except Exception as update_err:
                print(f"Aviso: Não foi possível atualizar status do lead {uid_cliente}: {update_err}")

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': nome,
                        'description': descricao or 'Serviço contratado',
                    },
                    'unit_amount': valor_centavos,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://crm-digital-lac.vercel.app/sucesso.html',
            cancel_url='https://crm-digital-lac.vercel.app/servicos.html',
        )

        return jsonify({"link_checkout": session.url}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)