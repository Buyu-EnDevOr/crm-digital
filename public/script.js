// Função que vai lá no Python buscar o JSON e montar a tabela
async function carregarClientes() {
    try {
        const resposta = await fetch('http://127.0.0.1:8080/api/clientes');
        const clientes = await resposta.json();

        const tabela = document.getElementById('lista-corpo');
        tabela.innerHTML = ''; // Limpa o "Carregando..."

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

// Mandar o Python deletar o cliente no Firebase
async function deletarCliente(id) {
    if(confirm("Tem certeza que deseja excluir este cliente? Essa ação não pode ser desfeita.")) {
        try {
            const resposta = await fetch(`http://127.0.0.1:8080/api/clientes/${id}`, {
                method: 'DELETE' 
            });
            
            if(resposta.ok) {
                alert("Cliente excluído com sucesso!");
                carregarClientes(); 
            } else {
                alert("Erro ao excluir o cliente.");
            }
        } catch (erro) {
            console.error("Erro:", erro);
            alert("Erro de conexão com o servidor.");
        }
    }
}

// === FUNÇÕES DO FORMULÁRIO DE CADASTRO ===

function mostrarFormulario() {
    document.getElementById('form-cadastro').style.display = 'block';
}

function fecharFormulario() {
    document.getElementById('form-cadastro').style.display = 'none';
}

async function salvarCadastro() {
    // Puxa os valores dos inputs reais do HTML
    const nomeInput = document.getElementById('input-nome').value;
    const telefoneInput = document.getElementById('input-telefone').value;
    const poloInput = document.getElementById('select-polo').value;
    const statusInput = document.getElementById('select-status').value;

    if (!nomeInput) {
        alert("Por favor, preencha o nome do cliente.");
        return;
    }

    const dadosCliente = {
        nome: nomeInput,
        telefone: telefoneInput,
        polo: poloInput,
        status: statusInput
    };

    try {
        const resposta = await fetch('http://127.0.0.1:8080/api/clientes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify(dadosCliente)
        });

        if (resposta.ok) {
            alert("Cliente cadastrado com sucesso!");
            fecharFormulario(); // Esconde o painel
            carregarClientes(); // Atualiza a tabela na hora
            
            // Limpa os campos para o próximo
            document.getElementById('input-nome').value = '';
            document.getElementById('input-telefone').value = '';
            // Os selects voltam para o padrão naturalmente
        } else {
            alert("Erro ao cadastrar cliente.");
        }
    } catch (erro) {
        console.error("Erro ao cadastrar:", erro);
        alert("Erro de conexão com o servidor.");
    }
}

// Função simples para formatar os textos
function formatarTexto(texto) {
    if (!texto) return '-';
    return texto.replace('_', ' ').toUpperCase();
}

// Inicia a tabela
carregarClientes();