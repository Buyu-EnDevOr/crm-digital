from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json
import stripe
import datetime

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
# ROTA DE AUTOMAÇÃO CRM (ATUALIZADA)
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
                "rua": "-",              # NOVO: Substitui o 'polo'
                "bairro": "Indefinido",  # NOVO: Substitui o 'polo'
                "status": "prospeccao",
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
# NOVAS ROTAS DO FUNIL DE VENDAS
# ==========================================
@app.route('/api/clientes/status', methods=['PUT'])
def atualizar_status_funil():
    try:
        dados = request.json
        uid = dados.get('uid')
        status = dados.get('status')
        
        if not uid or not status:
            return jsonify({"erro": "UID ou status ausente"}), 400
            
        db.collection("leads").document(uid).update({"status": status})
        return jsonify({"mensagem": f"Status atualizado para {status}"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/clientes/sync-endereco', methods=['PUT'])
def sincronizar_endereco_crm():
    try:
        dados = request.json
        uid = dados.get('uid')
        if not uid:
            return jsonify({"erro": "UID ausente"}), 400
            
        atualizacao = {}
        if 'rua' in dados: atualizacao['rua'] = dados['rua']
        if 'bairro' in dados: atualizacao['bairro'] = dados['bairro']
        
        db.collection("leads").document(uid).update(atualizacao)
        return jsonify({"mensagem": "Endereço sincronizado no CRM"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ==========================================
# HISTÓRICO DE COMPRAS
# ==========================================
@app.route('/api/historico/compras', methods=['POST'])
def salvar_historico_compra():
    try:
        dados = request.json
        uid = dados.get('uid')
        if not uid:
            return jsonify({"erro": "UID ausente"}), 400
            
        nova_compra = {
            "uid": uid,
            "produtos": dados.get('produtos', []),
            "total": float(dados.get('total', 0)),
            "data": dados.get('data', datetime.datetime.now(datetime.timezone.utc).isoformat())
        }
        db.collection("historico_compras").add(nova_compra)
        return jsonify({"mensagem": "Histórico gravado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/historico/<uid_cliente>', methods=['GET'])
def listar_historico_cliente(uid_cliente):
    try:
        # Busca todas as compras referentes a este UID
        compras_ref = db.collection("historico_compras").where("uid", "==", uid_cliente).stream()
        lista_compras = []
        for c in compras_ref:
            dados = c.to_dict()
            dados['id'] = c.id
            lista_compras.append(dados)
            
        # Ordena da mais recente para a mais antiga
        lista_compras.sort(key=lambda x: x.get('data', ''), reverse=True)
        return jsonify(lista_compras), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ==========================================
# LOGS E CARRINHO ABANDONADO
# ==========================================
@app.route('/api/log/carrinho-abandonado', methods=['POST'])
def registar_carrinho_abandonado():
    try:
        # O navigator.sendBeacon do Front-end às vezes envia os dados como texto simples
        if not request.json:
            dados = json.loads(request.data)
        else:
            dados = request.json
            
        uid = dados.get('uid')
        if not uid:
            return jsonify({"erro": "UID ausente"}), 400
            
        log = {
            "uid": uid,
            "produtos": dados.get('produtos', []),
            "data": dados.get('data', datetime.datetime.now(datetime.timezone.utc).isoformat())
        }
        db.collection("carrinho_abandonado").add(log)
        return jsonify({"mensagem": "Abandono de carrinho registado"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/cron/limpar-logs', methods=['GET'])
def limpar_logs_antigos():
    try:
        # Calcula exatamente a data de 7 dias atrás
        sete_dias_atras = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        data_limite_iso = sete_dias_atras.isoformat()
        
        # Procura registos de abandono de carrinho mais antigos que 7 dias
        logs_antigos = db.collection("carrinho_abandonado").where("data", "<", data_limite_iso).stream()
        
        contador = 0
        for log in logs_antigos:
            db.collection("carrinho_abandonado").document(log.id).delete()
            contador += 1
            
        return jsonify({"mensagem": f"Limpeza concluída. {contador} logs antigos foram excluídos."}), 200
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
# ROTAS DA VITRINE (HOME) E PRODUTOS ... 
# (Mantidas exatamente iguais para não quebrar nada)
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
                "descricao": "Serviços digitais...",
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
        return jsonify({"mensagem": "Vitrine atualizada!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/produtos', methods=['POST'])
def criar_produto():
    try:
        db.collection("produtos").add(request.json)
        return jsonify({"mensagem": "Produto criado!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/produtos', methods=['GET'])
def listar_produtos():
    try:
        lista_produtos = [{"id": p.id, **p.to_dict()} for p in db.collection("produtos").stream()]
        return jsonify(lista_produtos), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/produtos/<id_produto>', methods=['DELETE'])
def deletar_produto(id_produto):
    try:
        db.collection("produtos").document(id_produto).delete()
        return jsonify({"mensagem": "Produto deletado!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)