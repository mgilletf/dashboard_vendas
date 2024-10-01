import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f"{prefixo} {valor:.2f} {unidade}"
        valor /= 1000
    return f"{prefixo} {valor:.2f} milhões"

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {
    'regiao': regiao.lower(),
    'ano': ano
}
response = requests.get(url, params = query_string)
dados = pd.DataFrame.from_dict(response.json())

dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

##Tabelas
###Tabelas de receitas
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on= 'Local da compra', right_index= True).sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq= 'M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()
receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

###Tabelas de quantidade de vendas
qtd_estados = dados.groupby('Local da compra')[['Produto']].count()
qtd_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(qtd_estados, left_on= 'Local da compra', right_index= True).sort_values('Produto', ascending=False)

qtd_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq= 'M'))['Produto'].count().reset_index()
qtd_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
qtd_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()
qtd_categorias = dados.groupby('Categoria do Produto')[['Produto']].count().sort_values('Produto', ascending=False)

estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].agg(['sum', 'count']))
categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].agg(['sum', 'count']))

###Tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

##Gráficos
###Gráficos receita
fig_mapa_receita = px.scatter_geo(
    receita_estados,
    lat= 'lat',
    lon = 'lon',
    scope= 'south america',
    size= 'Preço',
    template= 'seaborn',
    hover_name= 'Local da compra',
    hover_data= {'lat': False, 'lon': False},
    title= 'Receita por estado'
)

fig_receita_mensal = px.line(
    receita_mensal,
    x = 'Mês',
    y = 'Preço',
    markers= True,
    range_y= (0, receita_mensal.max()),
    color= 'Ano',
    line_dash= 'Ano',
    title= 'Receita Mensal'
)
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(
    receita_estados.head(),
    x='Local da compra',
    y='Preço',
    text_auto=True,
    title='Top estados (receita)'
)

#fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(
    receita_categorias,
    text_auto=True,
    title='Receita por categoria'
)

fig_receita_categorias.update_layout(yaxis_title = 'Receita')

###Gráficos Quantidade de Vendas
fig_mapa_qtd = px.scatter_geo(
    qtd_estados,
    lat= 'lat',
    lon = 'lon',
    scope= 'south america',
    size= 'Produto',
    template= 'seaborn',
    hover_name= 'Local da compra',
    hover_data= {'lat': False, 'lon': False},
    title= 'Quantidade de vendas por estado'
)

fig_qtd_mensal = px.line(
    qtd_mensal,
    x = 'Mês',
    y = 'Produto',
    markers= True,
    range_y= (0, qtd_mensal.max()),
    color= 'Ano',
    line_dash= 'Ano',
    title= 'Quantidade Mensal'
)

#Visualização no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados['Preço'].shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categorias, use_container_width = True)

with aba2:
    qtd_estados = st.number_input('Quantidade de Estados', 2, 10, 5)
    qtd_categorias = 8
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_qtd, use_container_width = True)
        fig_qtd_estados = px.bar(
            estados[['count']].sort_values('count', ascending=False).head(qtd_estados),
            x='count',
            y=estados[['count']].sort_values('count', ascending=False).head(qtd_estados).index,
            text_auto=True,
            title=f'Top {qtd_estados} estados (quantidade de vendas)'
        )
        fig_qtd_estados.update_layout(yaxis_title = 'Quantidade de Vendas')
        st.plotly_chart(fig_qtd_estados)
    
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados['Preço'].shape[0]))
        st.plotly_chart(fig_qtd_mensal, use_container_width = True)
        fig_qtd_categorias = px.bar(
            categorias[['count']].sort_values('count', ascending=False).head(qtd_categorias),
            x='count',
            y=categorias[['count']].sort_values('count', ascending=False).head(qtd_categorias).index,
            text_auto=True,
            title=f'Top {qtd_categorias} categorias (quantidade de vendas)'
        )
        fig_qtd_categorias.update_layout(yaxis_title = 'Quantidade de Vendas por Categoria')        
        st.plotly_chart(fig_qtd_categorias)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de Vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(
            vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
            x='sum',
            y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
            text_auto=True,            
            title=f'Top {qtd_vendedores} vendedores (receita)'
        )
        fig_receita_vendedores.update_layout(yaxis_title = 'Vendedores')
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados['Preço'].shape[0]))
        fig_vendas_vendedores = px.bar(
            vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
            x='count',
            y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)'
        )
        fig_vendas_vendedores.update_layout(yaxis_title = 'Vendedores')
        st.plotly_chart(fig_vendas_vendedores)

#Removido na aula 2.8
#st.dataframe(dados)

