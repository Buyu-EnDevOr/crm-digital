from flask import Flask, jsonify

app = Flask(__name__)

# Uma rota de teste para ver se o backend está vivo
@app.route('/api/status')
def status():
    return jsonify({"mensagem": "Servidor Python rodando perfeitamente!", "status": 200})

# No futuro, criaremos rotas como /api/produtos ou /api/login aqui

# Essa linha é obrigatória para a Vercel exportar o app
# Vercel serverless function entrypoint