let clienteEditandoId = null;

// ==========================================
// 1. CARREGAR E LISTAR CLIENTES
// ==========================================
async function carregarClientes() {
    try {
        const resposta = await fetch('/api/clientes');
        const clientes = await resposta.json();

        const tabela = document.getElementById('lista-corpo');
        tabela.innerHTML = ''; 

        if (clientes.length === 0) {
            tabela.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhum lead encontrado.</td></tr>';
            return;
        }

        clientes.forEach(cliente => {
            const linha = document.createElement('tr');
            
            // Tratamento para evitar que apareça 'undefined' na tela
            const nomeStr = (cliente.nome && cliente.nome !== 'undefined') ? cliente.nome : 'Sem Nome';
            const telStr = (cliente.telefone && cliente.telefone !== 'undefined') ? cliente.telefone : '-';
            const poloStr = cliente.polo || 'indefinido';
            const statusStr = cliente.status || 'indefinido';
            
            // Tratamento contra aspas simples em nomes para não quebrar o botão HTML
            const nomeSafe = nomeStr.replace(/'/g, "\\'"); 
            
            linha.innerHTML = `
                <td><strong>${nomeStr}</strong></td>
                <td>${telStr}</td>
                <td><span class="badge polo">${formatarTexto(poloStr)}</span></td>
                <td><span class="badge status ${statusStr}">${formatarTexto(statusStr)}</span></td>
                <td>
                    <button class="btn-editar" onclick="prepararEdicao('${cliente.id}', '${nomeSafe}', '${telStr}', '${poloStr}', '${statusStr}')">Editar</button>
                    <button class="btn-excluir" onclick="deletarCliente('${cliente.id}')">Excluir</button>
                </td>
            `;
            tabela.appendChild(linha);
        });

    } catch (erro) {
        console.error("Erro ao carregar clientes:", erro);
        document.getElementById('lista-corpo').innerHTML = '<tr><td colspan="5" style="text-align: center; color: #ef4444;">Erro ao carregar os dados. Verifique a conexão.</td></tr>';
    }
}

// ==========================================
// 2. DELETAR CLIENTE
// ==========================================
async function deletarCliente(id) {
    if(confirm("Tem certeza que deseja excluir este Lead permanentemente?")) {
        try {
            const resposta = await fetch(`/api/clientes/${id}`, { method: 'DELETE' });
            if(resposta.ok) {
                carregarClientes(); 
            } else {
                alert("Erro ao tentar excluir o cliente.");
            }
        } catch (erro) {
            console.error("Erro na exclusão:", erro);
            alert("Erro de conexão ao excluir.");
        }
    }
}

// ==========================================
// 3. CONTROLE DO FORMULÁRIO (ABRIR / FECHAR / PREPARAR)
// ==========================================
function mostrarFormulario() {
    clienteEditandoId = null; 
    document.querySelector('#form-cadastro h2').innerText = "Cadastrar Novo Lead";
    
    document.getElementById('input-nome').value = '';
    document.getElementById('input-telefone').value = '';
    document.getElementById('select-polo').value = 'lagoa_dourada'; // Valor padrão
    document.getElementById('select-status').value = 'prospeccao'; // Valor padrão
    
    document.getElementById('form-cadastro').style.display = 'block';
}

function prepararEdicao(id, nome, telefone, polo, status) {
    clienteEditandoId = id; 
    document.querySelector('#form-cadastro h2').innerText = "Editar Lead";
    
    document.getElementById('input-nome').value = nome !== '-' ? nome : '';
    document.getElementById('input-telefone').value = telefone !== '-' ? telefone : '';
    
    // Verifica se os selects existem antes de aplicar, evitando erros
    const poloSelect = document.getElementById('select-polo');
    if (poloSelect) poloSelect.value = polo;
    
    const statusSelect = document.getElementById('select-status');
    if (statusSelect) statusSelect.value = status;
    
    document.getElementById('form-cadastro').style.display = 'block';
}

function fecharFormulario() {
    document.getElementById('form-cadastro').style.display = 'none';
    clienteEditandoId = null; 
}

// ==========================================
// 4. SALVAR / ATUALIZAR CLIENTE
// ==========================================
async function salvarCadastro() {
    const nomeInput = document.getElementById('input-nome').value.trim();
    const telefoneInput = document.getElementById('input-telefone').value.trim();
    const poloInput = document.getElementById('select-polo').value;
    const statusInput = document.getElementById('select-status').value;

    if (!nomeInput) {
        alert("Por favor, preencha o nome do Lead.");
        return;
    }

    const dadosCliente = {
        nome: nomeInput,
        telefone: telefoneInput,
        polo: poloInput,
        status: statusInput
    };

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
            fecharFormulario(); 
            carregarClientes(); 
        } else {
            alert("Erro no servidor ao tentar salvar.");
        }
    } catch (erro) {
        console.error("Erro ao salvar:", erro);
        alert("Erro de conexão. Verifique se o servidor está respondendo.");
    }
}

// ==========================================
// 5. FUNÇÕES AUXILIARES
// ==========================================
function formatarTexto(texto) {
    if (!texto || texto === 'undefined') return '-';
    // Substitui underline por espaço e coloca em Maiúsculo
    return texto.replace(/_/g, ' ').toUpperCase();
}

// ==========================================
// INICIALIZAÇÃO
// ==========================================
// Inicia o carregamento da tabela assim que a página abre
carregarClientes();