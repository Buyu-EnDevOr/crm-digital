// ==========================================
// 1. CONFIGURAÇÃO FIREBASE E IMPORTS
// ==========================================
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyA6fZuQf0-GshZ_wtxJW3CRFtlvFPxfaGg",
    authDomain: "crm-digital-6b415.firebaseapp.com",
    projectId: "crm-digital-6b415",
    storageBucket: "crm-digital-6b415.firebasestorage.app",
    messagingSenderId: "686804789801",
    appId: "1:686804789801:web:26ddd8979fc38ab4864a38"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Variáveis Globais de Estado
let ehAdmin = false;
let usuarioAtualUid = null; 
window.produtosCarregados = {};
let clienteEditandoId = null;

// Elementos da Interface (Globais)
const btnAdmin = document.getElementById('btn-admin');
const areaDeslogada = document.getElementById('area-deslogada');
const areaLogada = document.getElementById('area-logada');
const userEmailSpan = document.getElementById('user-email');
const userUidSpan = document.getElementById('user-uid');
const userFoto = document.getElementById('user-foto');
const btnLogout = document.getElementById('btn-logout');
const areaAdminProdutos = document.getElementById('area-admin-produtos');

// ==========================================
// 2. AUTENTICAÇÃO E ESTADO DO USUÁRIO
// ==========================================
onAuthStateChanged(auth, (user) => {
    if (user) {
        usuarioAtualUid = user.uid; 
        
        if(areaDeslogada) areaDeslogada.classList.add('oculto');
        if(areaLogada) areaLogada.classList.remove('oculto');
        if(userEmailSpan) userEmailSpan.innerText = user.email;

        if(userFoto) {
            userFoto.src = user.photoURL || "https://www.gravatar.com/avatar/?d=mp";
            userFoto.setAttribute('referrerpolicy', 'no-referrer');
            userFoto.style.display = 'block';
        }

        if(userUidSpan) {
            const idCurto = user.uid.substring(0, 8).toUpperCase();
            userUidSpan.innerText = "ID: #" + idCurto;
            userUidSpan.dataset.uid = user.uid;
        }

        // Sincroniza usuário com o Backend Python/Node
        fetch('/api/sync_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: user.uid,
                nome: user.displayName || 'Sem Nome',
                email: user.email,
                foto: user.photoURL || ''
            })
        }).catch(err => console.error(err));

        // Controle de Acesso Admin
        if (user.email === "pedroeliasm08@gmail.com") {
            ehAdmin = true;
            if(btnAdmin) btnAdmin.classList.remove('oculto');
            if(areaAdminProdutos) areaAdminProdutos.classList.remove('oculto');
        } else {
            ehAdmin = false;
            if(btnAdmin) btnAdmin.classList.add('oculto');
            if(areaAdminProdutos) areaAdminProdutos.classList.add('oculto');
        }
    } else {
        ehAdmin = false;
        usuarioAtualUid = null; 
        if(areaDeslogada) areaDeslogada.classList.remove('oculto');
        if(areaLogada) areaLogada.classList.add('oculto');
        if(btnAdmin) btnAdmin.classList.add('oculto');
        if(areaAdminProdutos) areaAdminProdutos.classList.add('oculto');
    }

    // Tenta carregar os produtos caso estejamos na tela de cardápio
    if(document.getElementById('container-categorias')) {
        window.carregarProdutos();
    }
});

if(btnLogout) {
    btnLogout.addEventListener('click', () => {
        import("https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js").then((module) => {
            module.signOut(auth).then(() => {
                window.location.href = "index.html";
            });
        });
    });
}

// ==========================================
// 3. INTERAÇÕES GERAIS DE UI (MENU E TEMAS)
// ==========================================
const btnToggle = document.getElementById('btn-toggle');
if (btnToggle) {
    btnToggle.addEventListener('click', () => {
        const menu = document.getElementById('menu-lateral');
        if(menu) menu.classList.toggle('oculta');
    });
}

const btnTema = document.getElementById('btn-tema');
if (btnTema) {
    btnTema.addEventListener('click', () => {
        document.body.classList.toggle('tema-escuro');
        if(document.body.classList.contains('tema-escuro')) {
            btnTema.innerHTML = '☀️ Claro';
        } else {
            btnTema.innerHTML = '🌙 Escuro';
        }
    });
}

// ==========================================
// 4. LÓGICA DO CARDÁPIO DIGITAL (PRODUTOS)
// ==========================================
window.carregarProdutos = async function() {
    const container = document.getElementById('container-categorias');
    if (!container) return; // Trava de segurança para não dar erro em outras páginas

    try {
        const resposta = await fetch('/api/produtos');
        const produtosDoBanco = await resposta.json();
        
        container.innerHTML = '';
        window.produtosCarregados = {};

        if (!produtosDoBanco || produtosDoBanco.length === 0) {
            container.innerHTML = '<p style="text-align: center; width: 100%; color: var(--cor-texto-mutado); font-weight: 500;">O cardápio está sendo preparado. Volte em breve!</p>';
            return;
        }

        const categorias = {};
        produtosDoBanco.forEach(prod => {
            window.produtosCarregados[prod.id] = prod;
            const cat = prod.categoria || 'Destaques'; 
            if (!categorias[cat]) categorias[cat] = [];
            categorias[cat].push(prod);
        });

        for (const [nomeCategoria, produtos] of Object.entries(categorias)) {
            let htmlPrateleira = `
                <div class="secao-categoria">
                    <div class="cabecalho-categoria">
                        <h2 class="titulo-categoria">${nomeCategoria}</h2>
                        <button class="btn-ver-mais" onclick="window.verMais('${nomeCategoria}')">Ver mais ></button>
                    </div>
                    <div class="prateleira">
            `;

            produtos.forEach(prod => {
                const valorFormatado = parseFloat(prod.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
                const urlImagem = prod.imagem_url ? prod.imagem_url : "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg";
                
                const botaoExcluir = ehAdmin 
                    ? `<button onclick="window.deletarProduto('${prod.id}')" style="background: transparent; color: #ef4444; border: 1px solid #ef4444; border-radius: 6px; padding: 4px 8px; margin-top: 10px; cursor: pointer; font-weight: bold; font-size: 0.75rem; width: 100%; transition: 0.3s;">🗑️ Excluir</button>`
                    : '';

                htmlPrateleira += `
                    <div class="card-produto">
                        <img src="${urlImagem}" alt="${prod.nome}" class="img-produto" onerror="this.src='https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg'">
                        
                        <div class="area-info-produto">
                            <div class="tag-nome-produto" title="${prod.nome}">${prod.nome}</div>
                            <p class="produto-descricao" title="${prod.descricao}">${prod.descricao}</p>
                            <span class="link-ler-mais" onclick="window.abrirModalLeitura('${prod.id}')" style="color: var(--cor-primaria, #D4AF37); cursor: pointer; font-size: 0.9rem; font-weight: bold; margin-bottom: 10px; display: inline-block;">Ler detalhes</span>
                            
                            <button class="btn-comprar-preco" onclick="window.iniciarCheckoutStripe('${prod.id}', this)">
                                ${valorFormatado}
                            </button>
                            ${botaoExcluir}
                        </div>
                    </div>
                `;
            });

            htmlPrateleira += `</div></div>`;
            container.innerHTML += htmlPrateleira;
        }
    } catch (erro) {
        console.error("Erro ao carregar cardápio:", erro);
        container.innerHTML = '<p style="text-align: center; color: red;">Erro ao conectar com o banco de dados.</p>';
    }
};

window.verMais = function(categoria) {
    alert(`Em breve: Tela completa com ordenação avançada para a categoria ${categoria}!`);
};

window.iniciarCheckoutStripe = async function(idProduto, botao) {
    const produto = window.produtosCarregados[idProduto];
    if (!produto) return;
    if (!usuarioAtualUid) {
        alert("Por favor, faça login para fazer um pedido!");
        window.location.href = "login.html";
        return;
    }
    const textoOriginal = botao.innerText;
    botao.innerText = "Processando...";
    botao.disabled = true;

    try {
        const resposta = await fetch('/api/pagamento', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nome: produto.nome,
                descricao: produto.descricao,
                valor: produto.valor,
                email: document.getElementById('user-email').innerText, 
                uid_cliente: usuarioAtualUid
            })
        });
        const dados = await resposta.json();
        if (resposta.ok && dados.link_checkout) {
            window.location.href = dados.link_checkout;
        } else {
            alert(dados.erro || "Erro no pagamento.");
            botao.innerText = textoOriginal;
            botao.disabled = false;
        }
    } catch (erro) {
        alert("Erro ao conectar com o servidor.");
        botao.innerText = textoOriginal;
        botao.disabled = false;
    }
};

window.abrirModalLeitura = function(idProduto) {
    const produto = window.produtosCarregados[idProduto];
    if(!produto) return;
    document.getElementById('titulo-leitura').innerText = produto.nome;
    document.getElementById('texto-leitura').innerText = produto.descricao;
    document.getElementById('overlay-produto').style.display = 'block';
    document.getElementById('modal-leitura').style.display = 'block';
};

window.fecharModalLeitura = function() {
    document.getElementById('overlay-produto').style.display = 'none';
    document.getElementById('modal-leitura').style.display = 'none';
};

window.abrirModalProduto = function() {
    document.getElementById('overlay-produto').style.display = 'block';
    document.getElementById('modal-produto').style.display = 'block';
};

window.fecharModalProduto = function() {
    document.getElementById('overlay-produto').style.display = 'none';
    document.getElementById('modal-produto').style.display = 'none';
};

window.salvarProduto = async function() {
    const nome = document.getElementById('prod-nome').value.trim();
    const categoria = document.getElementById('prod-categoria').value; 
    const descricao = document.getElementById('prod-descricao').value.trim();
    const valor = document.getElementById('prod-valor').value;
    const imagem = document.getElementById('prod-imagem').value.trim();

    if (!nome || !valor) {
        alert("O Nome e o Valor são obrigatórios!");
        return;
    }

    const novoProduto = {
        nome: nome,
        categoria: categoria,
        descricao: descricao,
        valor: parseFloat(valor),
        imagem_url: imagem
    };

    const botaoSalvar = document.querySelector('#modal-produto .btn-modal-salvar');
    botaoSalvar.innerText = "Salvando...";
    botaoSalvar.disabled = true;

    try {
        const resposta = await fetch('/api/produtos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(novoProduto)
        });
        if (resposta.ok) {
            window.fecharModalProduto();
            document.getElementById('prod-nome').value = '';
            document.getElementById('prod-descricao').value = '';
            document.getElementById('prod-valor').value = '';
            document.getElementById('prod-imagem').value = '';
            window.carregarProdutos();
        } else {
            alert("Erro ao criar o produto.");
        }
    } catch (erro) {
        alert("Erro de conexão.");
    } finally {
        botaoSalvar.innerText = "Salvar Item";
        botaoSalvar.disabled = false;
    }
};

window.deletarProduto = async function(idProduto) {
    if (!confirm("Tem certeza que deseja excluir este item do cardápio?")) return;
    try {
        const res = await fetch(`/api/produtos/${idProduto}`, { method: 'DELETE' });
        if (res.ok) window.carregarProdutos(); 
        else alert("Erro ao tentar remover o item.");
    } catch (e) {
        alert("Erro de conexão com o banco de dados.");
    }
};

// ==========================================
// 5. LÓGICA DE LEADS (PAINEL ADMIN)
// ==========================================
function formatarTexto(texto) {
    if (!texto || texto === 'undefined') return '-';
    return texto.replace(/_/g, ' ').toUpperCase();
}

window.carregarClientes = async function() {
    const tabela = document.getElementById('lista-corpo');
    if (!tabela) return; 

    try {
        const resposta = await fetch('/api/clientes');
        const clientes = await resposta.json();
        tabela.innerHTML = ''; 

        if (clientes.length === 0) {
            tabela.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhum lead encontrado.</td></tr>';
            return;
        }

        clientes.forEach(cliente => {
            const linha = document.createElement('tr');
            const nomeStr = (cliente.nome && cliente.nome !== 'undefined') ? cliente.nome : 'Sem Nome';
            const telStr = (cliente.telefone && cliente.telefone !== 'undefined') ? cliente.telefone : '-';
            const poloStr = cliente.polo || 'indefinido';
            const statusStr = cliente.status || 'indefinido';
            const nomeSafe = nomeStr.replace(/'/g, "\\'"); 
            
            linha.innerHTML = `
                <td><strong>${nomeStr}</strong></td>
                <td>${telStr}</td>
                <td><span class="badge polo">${formatarTexto(poloStr)}</span></td>
                <td><span class="badge status ${statusStr}">${formatarTexto(statusStr)}</span></td>
                <td>
                    <button class="btn-editar" onclick="window.prepararEdicao('${cliente.id}', '${nomeSafe}', '${telStr}', '${poloStr}', '${statusStr}')">Editar</button>
                    <button class="btn-excluir" onclick="window.deletarCliente('${cliente.id}')">Excluir</button>
                </td>
            `;
            tabela.appendChild(linha);
        });
    } catch (erro) {
        console.error("Erro ao carregar clientes:", erro);
        tabela.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #ef4444;">Erro ao carregar os dados.</td></tr>';
    }
};

window.deletarCliente = async function(id) {
    if(confirm("Tem certeza que deseja excluir este Lead permanentemente?")) {
        try {
            const resposta = await fetch(`/api/clientes/${id}`, { method: 'DELETE' });
            if(resposta.ok) window.carregarClientes(); 
            else alert("Erro ao tentar excluir o cliente.");
        } catch (erro) {
            alert("Erro de conexão ao excluir.");
        }
    }
};

window.mostrarFormulario = function() {
    clienteEditandoId = null; 
    document.querySelector('#form-cadastro h2').innerText = "Cadastrar Novo Lead";
    document.getElementById('input-nome').value = '';
    document.getElementById('input-telefone').value = '';
    
    const selectPolo = document.getElementById('select-polo');
    if(selectPolo) selectPolo.value = 'lagoa_dourada';
    const selectStatus = document.getElementById('select-status');
    if(selectStatus) selectStatus.value = 'prospeccao';
    
    document.getElementById('form-cadastro').style.display = 'block';
};

window.prepararEdicao = function(id, nome, telefone, polo, status) {
    clienteEditandoId = id; 
    document.querySelector('#form-cadastro h2').innerText = "Editar Lead";
    document.getElementById('input-nome').value = nome !== '-' ? nome : '';
    document.getElementById('input-telefone').value = telefone !== '-' ? telefone : '';
    
    const poloSelect = document.getElementById('select-polo');
    if (poloSelect) poloSelect.value = polo;
    const statusSelect = document.getElementById('select-status');
    if (statusSelect) statusSelect.value = status;
    
    document.getElementById('form-cadastro').style.display = 'block';
};

window.fecharFormulario = function() {
    document.getElementById('form-cadastro').style.display = 'none';
    clienteEditandoId = null; 
};

window.salvarCadastro = async function() {
    const nomeInput = document.getElementById('input-nome').value.trim();
    const telefoneInput = document.getElementById('input-telefone').value.trim();
    const poloInput = document.getElementById('select-polo').value;
    const statusInput = document.getElementById('select-status').value;

    if (!nomeInput) return alert("Por favor, preencha o nome do Lead.");

    const dadosCliente = { nome: nomeInput, telefone: telefoneInput, polo: poloInput, status: statusInput };
    const url = clienteEditandoId ? `/api/clientes/${clienteEditandoId}` : '/api/clientes';
    const metodo = clienteEditandoId ? 'PUT' : 'POST';

    try {
        const resposta = await fetch(url, {
            method: metodo,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dadosCliente)
        });

        if (resposta.ok) {
            alert(clienteEditandoId ? "Lead atualizado com sucesso!" : "Lead cadastrado com sucesso!");
            window.fecharFormulario(); 
            window.carregarClientes(); 
        } else {
            alert("Erro no servidor ao tentar salvar.");
        }
    } catch (erro) {
        alert("Erro de conexão.");
    }
};

// ==========================================
// 6. INICIALIZAÇÃO
// ==========================================
// Tenta carregar a tabela de clientes assim que a página abre (se estiver no Painel Admin)
if(document.getElementById('lista-corpo')) {
    window.carregarClientes();
}