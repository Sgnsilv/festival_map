# 📍 Mapa dos Festivais Gastronômicos de Natal

Este projeto é um site interativo criado com **Streamlit** que exibe os restaurantes participantes dos festivais **Sweet Coffee Week 🍰** e **Sigablend 🍔**, ambos realizados na cidade de **Natal (RN)**.

---

## 🌐 **Descrição do Projeto**
O site mostra um mapa interativo com todos os restaurantes participantes, permitindo:
- Visualizar os locais exatos no mapa.
- Filtrar por tipo de refeição (café da manhã, almoço, jantar, resenha etc.).
- Identificar os festivais por ícones diferentes (🍰 para doces e 🍔 para hambúrgueres).
- Ver fotos e temas dos combos ao clicar nos marcadores.
- Escolher um ponto de referência (como “UFRN” ou “Praia de Ponta Negra”) para descobrir qual restaurante está mais próximo.

As cores dos marcadores indicam o quanto você quer visitar cada local:
- 🔴 Vermelho → Quero muito ir
- 🟡 Amarelo → Quero ir
- 🟢 Verde → Quero ir, mas nem tanto

---

## 📁 **Estrutura do Projeto**
```
📦 festival-map/
│
├── streamlit_festival_map.py   # Código principal do app Streamlit
├── dados_festival.csv          # Planilha com os dados dos restaurantes
├── requirements.txt            # Dependências necessárias
├── images/                     # Pasta com as fotos dos combos
│   ├── wow_cookies.jpg
│   ├── losmuerts.jpg
│   └── ...
└── README.md                   # Este arquivo
```



## 🚀 **Como Executar Localmente**

### 1️⃣ Instalar dependências:
```bash
pip install -r requirements.txt
```

### 2️⃣ Rodar o app:
```bash
streamlit run streamlit_festival_map.py
```

O app abrirá automaticamente no navegador.

---

Confira o site em:
```
https://seuusuario-festival-map.streamlit.app
```

---

## 📅 **Informações do Evento**
Os festivais ocorrerão entre **6 e 16 de novembro** em Natal/RN.

### 🍰 Sweet Coffee Week  
[https://www.instagram.com/sweetcoffeeweek](https://www.instagram.com/sweetcoffeeweek)

### 🍔 Sigablend Festival  
[https://www.instagram.com/sigablend](https://www.instagram.com/sigablend)

