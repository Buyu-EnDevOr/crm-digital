from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json # <-- Necessário para ler a chave da Vercel
import stripe

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

# ==========================================
# ROTA DE AUTOMAÇÃO CRM (FASE 1)
# ==========================================
@app.route('/api/sync_user', methods=['POST'])
def sincronizar_usuario():
    try:
        dados = request.json
        uid = dados.get('uid')
        
        if not uid:
            return jsonify({"erro": "UID não fornecido"}), 400
            
        # 1. Procura o cliente no banco de dados usando o UID único do Google
        cliente_ref = db.collection("leads").document(uid)
        doc = cliente_ref.get()
        
        if not doc.exists:
            # 2. Se NÃO EXISTE: Cria a ficha base do cliente automaticamente!
            novo_cliente = {
                "nome": dados.get('nome', 'Sem Nome'),
                "email": dados.get('email', ''),
                "foto_url": dados.get('foto', ''),
                "telefone": "-", # Será preenchido na Fase 2
                "polo": "-",     # Será preenchido na Fase 2
                "status": "prospeccao", # Status inicial automático do Funil
                "historico_compras": [], # Gaveta vazia pronta para a Fase 4
                "ultimo_acesso": firestore.SERVER_TIMESTAMP
            }
            cliente_ref.set(novo_cliente)
            return jsonify({"mensagem": "Novo lead cadastrado automaticamente no funil!", "novo": True}), 201
        else:
            # 3. Se JÁ EXISTE: Apenas atualiza a data de acesso e a foto (caso ele tenha trocado no Google)
            cliente_ref.update({
                "foto_url": dados.get('foto', ''),
                "ultimo_acesso": firestore.SERVER_TIMESTAMP
            })
            return jsonify({"mensagem": "Login registrado com sucesso.", "novo": False}), 200
            
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ==========================================
# CRUD MANUAL DE CLIENTES (PAINEL ADMIN)
# ==========================================

# CREATE: Recebe os dados do formulário e salva (Cadastro manual)
@app.route('/api/clientes', methods=['POST'])
def criar_cliente():
    try:
        novo_cliente = request.json 
        db.collection("leads").add(novo_cliente)
        return jsonify({"mensagem": "Cliente cadastrado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# READ: Entrega a lista de clientes para a tabela do HTML
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
# ROTA DE PAGAMENTO (STRIPE)
# ==========================================
@app.route('/api/pagamento', methods=['POST'])
def gerar_pagamento():
    try:
        # 1. Busca a chave escondida nas Variáveis de Ambiente
        stripe.api_key = os.environ.get("STRIPE_KEY")

        # 2. Criando a sessão de checkout
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': 'Consultoria Criativa',
                        'description': 'Reunião de 1 hora para estruturação de ideias e roteiros.',
                    },
                    'unit_amount': 1000, 
                },
                'quantity': 1,
            }],
            mode='payment',
            # LINKS ATUALIZADOS PARA A SUA VERCEL AQUI 👇
            success_url='https://crm-digital-lac.vercel.app/sucesso.html', 
            cancel_url='https://crm-digital-lac.vercel.app/servicos.html',
        )

        # 3. Devolvendo o link de checkout gerado para o JavaScript
        return jsonify({"link_checkout": session.url}), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)