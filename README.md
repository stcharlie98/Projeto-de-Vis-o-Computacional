# Projeto da disciplina 218153 – Sistemas de Visão Computacional (PUC-Campinas): Análise de Movimentos dos Pés com Visão Computacional

Este repositório reúne o código, dados, vídeo e figuras utilizados no trabalho “Análise de movimentos dos pés com visão computacional para aplicações em mobilidade funcional”.
O objetivo principal é analisar a dinâmica da marcha estacionária a partir de dados 3D estimados por um sistema de pose estimation, extraindo métricas como amplitude, cadência, simetria e periodicidade.

O repositório serve tanto como material complementar ao relatório quanto como base reprodutível para experimentos futuros.

## Estrutura do Repositório

<img width="479" height="452" alt="image" src="https://github.com/user-attachments/assets/573b6900-25cc-4ac2-b997-8a731afba44e" />

## Objetivo do Projeto

O projeto investiga a possibilidade de analisar padrões de mobilidade utilizando somente coordenadas 3D estimadas por um sistema de visão computacional monocular.
As métricas avaliadas incluem:

Amplitude vertical dos tornozelos

Cadência estimada por janela deslizante

Índice de simetria entre passos esquerdo e direito

Autocorrelação do movimento vertical

Esses indicadores são relevantes em aplicações de monitoramento funcional, fisioterapia preventiva e análise de marcha em ambientes com recursos limitados, como lares de idosos.

## Metodologia Resumida

O pipeline adotado no script segue as etapas:

Carregamento e inspeção do CSV
Verificação de colunas, detecção automática dos nomes dos tornozelos e do eixo temporal.

Pré-processamento e filtragem

interpolação de valores ausentes

filtro de mediana

filtro Butterworth (4ª ordem, fase zero) quando disponível

Detecção de picos (passos)
Identificação dos máximos locais correspondentes aos instantes de elevação do pé.

Cálculo de métricas

cadência por janela móvel

emparelhamento E–D para cálculo de simetria

autocorrelação do sinal filtrado

Geração das figuras e exportação da tabela final

## Como Executar o Script

Instale as dependências necessárias:

pip install numpy pandas matplotlib scipy


Ajuste os caminhos no início do arquivo VisaoComp.py:

csv_path = r"C:\SEU_CAMINHO\20251029-220949_Walk.csv"
out_dir  = r"C:\SEU_CAMINHO\resultados"


Rode o script:

python VisaoComp.py


Os gráficos e o arquivo picos_resumo.csv serão salvos automaticamente na pasta definida em out_dir.

## Figuras Geradas

O script produz quatro figuras principais:

Trajetória vertical dos tornozelos com picos detectados

Cadência estimada por janela móvel (10 s)

Índice de simetria entre passos

Autocorrelação do movimento vertical do tornozelo esquerdo

Essas figuras aparecem no relatório como Figura 1 a Figura 4, respectivamente.

## Limitações Conhecidas

A taxa de amostragem do CSV não é explicitamente definida, sendo inferida pelo script.

O sistema de pose estimation utilizado ainda está em testes, portanto pode apresentar ruído elevado, especialmente em articulações distais.

Os valores de amplitude não representam altura absoluta, mas sim variação relativa no eixo Y.

O script não realiza calibração geométrica ou reconstrução métrica.

## Créditos

Projeto desenvolvido pelos alunos:
Charles de Souza, Emerson Mafalda Oliveira, Gustavo Henrique da Silva, Patrick Geraldi do Amaral
Curso: Engenharia de Controle e Automação – PUC-Campinas
Disciplina: 218153 – Sistemas de Visão Computacional
Docente: Prof. Everton Dias

## Licença

Uso exclusivamente acadêmico e educacional.
O conteúdo pode ser reutilizado para estudos, desde que citada a fonte.
