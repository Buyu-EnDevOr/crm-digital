// Função que vai lá no Python buscar o JSON e montar a tabela
async function carregarClientes() {
    try {
        // Batendo na porta do seu servidor Python
        const resposta = await fetch('http://127.0.0.1:8080/api/clientes');
        const clientes = await resposta.json();

        const tabela = document.getElementById('lista-corpo');
        tabela.innerHTML = ''; // Limpa o "Carregando..."

        if (clientes.length === 0) {
            tabela.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhum cliente encontrado.</td></tr>';
            return;
        }

        // Para cada cliente no JSON, cria uma linha na tabela com o botão de excluir
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

// Nova Função: Mandar o Python deletar o cliente no Firebase
async function deletarCliente(id) {
    // Confirmação de segurança
    if(confirm("Tem certeza que deseja excluir este cliente? Essa ação não pode ser desfeita.")) {
        try {
            const resposta = await fetch(`http://127.0.0.1:8080/api/clientes/${id}`, {
                method: 'DELETE' // Avisa o Python que a intenção é apagar
            });
            
            if(resposta.ok) {
                alert("Cliente excluído com sucesso!");
                carregarClientes(); // Recarrega a tabela na mesma hora para o nome sumir
            } else {
                alert("Erro ao excluir o cliente.");
            }
        } catch (erro) {
            console.error("Erro:", erro);
            alert("Erro de conexão com o servidor.");
        }
    }
}

// === NOVA FUNÇÃO (CREATE) ADICIONADA AQUI ===
// Função para enviar um novo cliente para o Python
async function novoCadastro() {
    // Usando prompt para testar rápido. Depois podemos trocar por um modal/formulário!
    const nomeInput = prompt("Digite o nome do novo cliente:");
    if (!nomeInput) return; // Se o usuário cancelar, a função para aqui

    const telefoneInput = prompt("Digite o WhatsApp do cliente:");

    const dadosCliente = {
        nome: nomeInput,
        telefone: telefoneInput,
        polo: "ONLINE",          // Colocando um padrão temporário
        status: "PROSPECCAO"     // Colocando um padrão temporário
    };

    try {
        const resposta = await fetch('http://127.0.0.1:8080/api/clientes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json' // Avisa o Python que estamos mandando um JSON
            },
            body: JSON.stringify(dadosCliente)
        });

        if (resposta.ok) {
            alert("Cliente cadastrado com sucesso!");
            carregarClientes(); // Atualiza a tabela na hora para o novo cliente aparecer
        } else {
            alert("Erro ao cadastrar cliente.");
        }
    } catch (erro) {
        console.error("Erro ao cadastrar:", erro);
        alert("Erro de conexão com o servidor.");
    }
}

// Função simples para formatar os textos (ex: "lagoa_dourada" vira "LAGOA DOURADA")
function formatarTexto(texto) {
    if (!texto) return '-';
    return texto.replace('_', ' ').toUpperCase();
}

// Chama a função assim que o site abrir
carregarClientes();