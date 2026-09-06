# CRM Digital & Vitrine Dinâmica 🚀

Um modelo de teste autoral (boilerplate/template) desenvolvido do zero (Full-Stack) para servir como base para futuros projetos web. Este repositório combina uma vitrine virtual focada em conversão para clientes com um robusto painel de gestão (CRM) nos bastidores para administração.

## 📌 Sobre o Projeto

Este projeto foi construído como um ambiente de estudo e validação tecnológica, provando a viabilidade de criar uma plataforma de vendas de serviços diretos (cortando taxas de marketplaces tradicionais) aliada a um sistema de gerenciamento interno. 

A arquitetura foi projetada para ser facilmente escalável e clonável. Caso queira iniciar um novo negócio, basta duplicar este projeto, trocar as chaves do Firebase e personalizar o visual.

## ⚙️ Funcionalidades

*   **Vitrine Dinâmica Editável:** O administrador pode alterar títulos, textos, links de imagens e contatos da página inicial diretamente pelo navegador, através de um modal "secreto" ativado por uma engrenagem oculta, sem precisar alterar código HTML.
*   **Gestão de Leads (CRUD):** Painel administrativo completo para adicionar, ler, atualizar e remover potenciais clientes (leads), categorizando-os por status de negociação e região.
*   **Segurança e Autenticação (Firebase):** Sistema de login rígido. Apenas a conta de e-mail designada como administradora tem acesso ao painel de controle e às ferramentas de edição da vitrine. Para usuários comuns, esses elementos são completamente removidos do código-fonte (DOM).
*   **Integração de Pagamento (Mercado Pago):** Rota de backend estruturada com a SDK do Mercado Pago (Checkout Pro) para gerar links dinâmicos de pagamento para os serviços oferecidos.
*   **Design UI/UX:** Layout inspirado em grandes marketplaces, utilizando efeitos *Glassmorphism* (cards translúcidos), fundo parallax, menus laterais retráteis (Sidebar Escura) e total responsividade.

## 🛠️ Tecnologias Utilizadas

**Front-end:**
*   HTML5, CSS3, JavaScript (Vanilla)
*   Integração direta via `fetch` API com o backend
*   Firebase Auth SDK (Autenticação client-side)

**Back-end:**
*   **Python 3**
*   **Flask** (Roteamento e construção da API)
*   **Firebase Admin SDK** (Conexão segura com o Firestore Database via variáveis de ambiente)
*   **Mercado Pago SDK** (Geração de links de pagamento)

**Infraestrutura & Hospedagem:**
*   **Vercel:** Hospedagem Serverless (`vercel.json` configurado para rodar o Python na nuvem).
*   **Google Firebase:** Banco de dados NoSQL (Firestore) e autenticação de usuários.
