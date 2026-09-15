# Quiz de Engenharia de Software

Aplicação gráfica de quiz para **Engenharia de Software**, desenvolvida em Python com **Tkinter**.

As perguntas são carregadas de um arquivo `perguntas.json`, permitindo responder diferentes tipos de questões e consultar o gabarito e as explicações posteriormente.

## Funcionalidades

* Interface gráfica com Tkinter.
* Carregamento de perguntas através de arquivo JSON.
* Navegação entre perguntas.
* Organização das perguntas por seções.
* Três tipos de questões:

  * **Múltipla escolha**
  * **Verdadeiro ou Falso**
  * **Discursiva**
* Exibição do gabarito após responder.
* Exibição de explicações para questões objetivas.
* Comparação da resposta do usuário com o gabarito.
* Contagem de acertos e perguntas conferidas.
* Possibilidade de abrir outro arquivo JSON pela própria interface.
* Respostas permanecem armazenadas durante a execução do programa.

## Requisitos

* Python 3
* Tkinter

No Ubuntu/WSL, caso o Tkinter não esteja instalado:

```bash
sudo apt install python3-tk
```

## Estrutura do projeto

```text
quiz-app/
├── quiz_app.py
├── perguntas.json
└── README.md
```

O arquivo `perguntas.json` contém as perguntas utilizadas pelo programa.

## Executando

Se `perguntas.json` estiver na mesma pasta do programa:

```bash
python3 quiz_app.py
```

Também é possível especificar outro arquivo JSON:

```bash
python3 quiz_app.py caminho/para/perguntas.json
```

## Executando no WSL com WSLg

No WSL, configure o display antes de executar o programa:

```bash
export DISPLAY=:0
```

Depois execute:

```bash
python3 quiz_app.py
```

### Exemplo

```bash
export DISPLAY=:0
python3 quiz_app.py
```

O `DISPLAY=:0` é necessário neste ambiente para que a interface gráfica do Tkinter seja exibida corretamente através do WSLg.

## Formato do JSON

O programa espera um arquivo JSON organizado em **seções**, contendo uma lista de perguntas.

Estrutura básica:

```json
{
  "sections": [
    {
      "title": "Nome da seção",
      "questions": [
        {
          "id": "q1",
          "type": "multiple_choice",
          "prompt": "Pergunta aqui?",
          "options": [
            {
              "key": "A",
              "text": "Alternativa A"
            },
            {
              "key": "B",
              "text": "Alternativa B"
            }
          ],
          "correct": "A",
          "explanation": "Explicação da resposta."
        }
      ]
    }
  ]
}
```

### Múltipla escolha

Utiliza:

```json
{
  "id": "q1",
  "type": "multiple_choice",
  "prompt": "Pergunta?",
  "options": [
    {
      "key": "A",
      "text": "Alternativa A"
    },
    {
      "key": "B",
      "text": "Alternativa B"
    }
  ],
  "correct": "A",
  "explanation": "Explicação."
}
```

### Verdadeiro ou Falso

Utiliza uma lista de afirmações:

```json
{
  "id": "q2",
  "type": "true_false_list",
  "prompt": "Classifique as afirmações:",
  "items": [
    "Primeira afirmação.",
    "Segunda afirmação.",
    "Terceira afirmação."
  ],
  "correct": [
    "V",
    "F",
    "V"
  ],
  "explanation": "Explicação das respostas."
}
```

### Discursiva

Utiliza uma resposta de referência:

```json
{
  "id": "q3",
  "type": "discursive",
  "prompt": "Explique o conceito.",
  "model_answer": "Resposta modelo ou referência."
}
```

## Interface

A interface possui:

* **Lista lateral:** mostra as seções e suas respectivas perguntas.
* **Área principal:** exibe a pergunta selecionada.
* **Ver Resposta:** revela o gabarito e a explicação.
* **Anterior / Próxima:** permite navegar entre as perguntas.
* **Placar:** mostra o número de perguntas objetivas conferidas e os acertos.
* **Abrir arquivo JSON:** permite carregar outro conjunto de perguntas.

## Observações

O programa não altera o arquivo `perguntas.json`. As respostas e o progresso ficam armazenados apenas durante a execução da aplicação.

Para utilizar outro conjunto de perguntas, basta fornecer outro arquivo JSON seguindo a estrutura esperada.
