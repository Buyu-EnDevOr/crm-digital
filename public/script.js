let clienteEditandoId = null;

async function carregarClientes() {
    try {
        // CORREÇÃO 1: Adicionado a barra inicial (/api/...)
        const resposta = await fetch('/api/clientes');
        const clientes = await resposta.json();

        const tabela = document.getElementById('lista-corpo');
        tabela.innerHTML = ''; 

        if (clientes.length === 0) {
            tabela.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhum cliente encontrado.</td></tr>';
            return;
        }

        clientes.forEach(cliente => {
            const linha = document.createElement('tr');
            linha.innerHTML = `
                <td><strong>${cliente.nome || 'Sem Nome'}</strong></td>
                <td>${cliente.telefone || '-'}</td>
                <td><span class="badge polo">${formatarTexto(cliente.polo)}</span></td>
                <td><span class="badge status ${cliente.status}">${formatarTexto(cliente.status)}</span></td>
                <td>
                    <button class="btn-editar" onclick="prepararEdicao('${cliente.id}', '${cliente.nome}', '${cliente.telefone}', '${cliente.polo}', '${cliente.status}')">Editar</button>
                    <button class="btn-excluir" onclick="deletarCliente('${cliente.id}')">Excluir</button>
                </td>
            `;
            tabela.appendChild(linha);
        });

    } catch (erro) {
        console.error("Erro:", erro);
        document.getElementById('lista-corpo').innerHTML = '<tr><td colspan="5" style="text-align: center; color: red;">Erro ao conectar com o Python. O servidor está ligado?</td></tr>';
    }
}

async function deletarCliente(id) {
    if(confirm("Tem certeza que deseja excluir este cliente?")) {
        try {
            // CORREÇÃO 2: Adicionado a barra inicial (/api/...)
            const resposta = await fetch(`/api/clientes/${id}`, { method: 'DELETE' });
            if(resposta.ok) {
                carregarClientes(); 
            } else {
                alert("Erro ao excluir.");
            }
        } catch (erro) {
            console.error("Erro:", erro);
        }
    }
}

function mostrarFormulario() {
    clienteEditandoId = null; 
    document.querySelector('#form-cadastro h2').innerText = "Cadastrar Novo Lead";
    
    document.getElementById('input-nome').value = '';
    document.getElementById('input-telefone').value = '';
    document.getElementById('select-polo').value = 'lagoa_dourada';
    document.getElementById('select-status').value = 'prospeccao';
    
    document.getElementById('form-cadastro').style.display = 'block';
}

function prepararEdicao(id, nome, telefone, polo, status) {
    clienteEditandoId = id; 
    document.querySelector('#form-cadastro h2').innerText = "Editar Lead";
    
    document.getElementById('input-nome').value = nome !== 'undefined' ? nome : '';
    document.getElementById('input-telefone').value = telefone !== 'undefined' ? telefone : '';
    document.getElementById('select-polo').value = polo;
    document.getElementById('select-status').value = status;
    
    document.getElementById('form-cadastro').style.display = 'block';
}

function fecharFormulario() {
    document.getElementById('form-cadastro').style.display = 'none';
    clienteEditandoId = null; 
}

async function salvarCadastro() {
    const nomeInput = document.getElementById('input-nome').value;
    const telefoneInput = document.getElementById('input-telefone').value;
    const poloInput = document.getElementById('select-polo').value;
    const statusInput = document.getElementById('select-status').value;

    if (!nomeInput) {
        alert("Por favor, preencha o nome.");
        return;
    }

    const dadosCliente = {
        nome: nomeInput,
        telefone: telefoneInput,
        polo: poloInput,
        status: statusInput
    };

    // CORREÇÃO 3: Trocado aspas simples (') por crase (`) e adicionado a barra inicial
    const url = clienteEditandoId ? `/api/clientes/${clienteEditandoId}` : '/api/clientes';
    const metodo = clienteEditandoId ? 'PUT' : 'POST';

    try {
        const resposta = await fetch(url, {
            method: metodo,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dadosCliente)
        });

        if (resposta.ok) {
            alert(clienteEditandoId ? "Atualizado com sucesso!" : "Cadastrado com sucesso!");
            fecharFormulario(); 
            carregarClientes(); 
        } else {
            alert("Erro ao salvar.");
        }
    } catch (erro) {
        console.error("Erro:", erro);
        alert("Erro de conexão.");
    }
}

function formatarTexto(texto) {
    if (!texto || texto === 'undefined') return '-';
    return texto.replace('_', ' ').toUpperCase();
}

carregarClientes();