import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
import io

# Inicialização do session_state
if "nos" not in st.session_state:
    st.session_state["nos"] = []
if "num_nos" not in st.session_state:
    st.session_state["num_nos"] = 2
if "barras" not in st.session_state:
    st.session_state["barras"] = []
if "num_barras" not in st.session_state:
    st.session_state["num_barras"] = 1
if "trelica_ativa" not in st.session_state:
    st.session_state["trelica_ativa"] = False
if "confirmar_nos" not in st.session_state:
    st.session_state["confirmar_nos"] = False
if "confirmar_barras" not in st.session_state:
    st.session_state["confirmar_barras"] = False
if "forcas_externas" not in st.session_state:
    st.session_state["forcas_externas"] = []
if "forcas_finalizadas" not in st.session_state:
    st.session_state["forcas_finalizadas"] = False
if "unidade" not in st.session_state:
    st.session_state["unidade"] = "kN"
if "apoios" not in st.session_state:
    st.session_state["apoios"] = []
if "num_apoios" not in st.session_state:
    st.session_state["num_apoios"] = 2
if "confirmar_apoios" not in st.session_state:
    st.session_state["confirmar_apoios"] = False
if "viga_ativa" not in st.session_state:
    st.session_state["viga_ativa"] = False
if "comp_viga" not in st.session_state:
    st.session_state["comp_viga"] = 5.0
if "apoios_viga" not in st.session_state:
    st.session_state["apoios_viga"] = []
if "cargas_viga" not in st.session_state:
    st.session_state["cargas_viga"] = []
if "viga_resolvida" not in st.session_state:
    st.session_state["viga_resolvida"] = False

def atualizar_nos():
    st.session_state["nos"] = [(0.0, 0.0) for _ in range(st.session_state["num_nos"])]

def atualizar_barras():
    st.session_state["barras"] = [(1, 2) for _ in range(st.session_state["num_barras"])]

def atualizar_apoios():
    st.session_state["apoios"] = [
        {"no": i + 1, "tipo": "Apoio de primeiro gênero (fixo em X)", "restricao_x": False, "restricao_y": False}
        for i in range(st.session_state["num_apoios"])]

def resolver_viga(comprimento, apoios, cargas):
    """
    Resolve uma viga isostática e retorna reações, esforço cortante e momento fletor
    """
    # Número de pontos para discretização
    n_points = 1000
    x = np.linspace(0, comprimento, n_points)
    
    # Inicializar arrays
    V = np.zeros(n_points)  # Esforço cortante
    M = np.zeros(n_points)  # Momento fletor
    
    # Calcular reações de apoio
    # Para viga com 2 apoios
    if len(apoios) == 2:
        # Somatório de momentos em relação ao primeiro apoio
        sum_momentos = 0
        sum_forcas_vert = 0
        
        for carga in cargas:
            if carga['tipo'] == 'pontual':
                sum_momentos += carga['intensidade'] * carga['posicao']
                sum_forcas_vert += carga['intensidade']
            elif carga['tipo'] == 'distribuida':
                # Para carga distribuída uniforme
                if carga['int_inicial'] == carga['int_final']:
                    intensidade = carga['int_inicial']
                    comp_carga = carga['posic_final'] - carga['posic_inicial']
                    pos_centro = (carga['posic_inicial'] + carga['posic_final']) / 2
                    sum_momentos += intensidade * comp_carga * pos_centro
                    sum_forcas_vert += intensidade * comp_carga
        
        # Reação no segundo apoio
        R2 = sum_momentos / comprimento
        # Reação no primeiro apoio
        R1 = sum_forcas_vert - R2
        
        reacoes = [R1, R2]
        
        # Calcular esforço cortante e momento fletor
        for i, pos in enumerate(x):
            # Esforço cortante
            V[i] = R1
            
            # Subtrair forças à esquerda da posição atual
            for carga in cargas:
                if carga['tipo'] == 'pontual' and carga['posicao'] <= pos:
                    V[i] -= carga['intensidade']
                elif carga['tipo'] == 'distribuida':
                    if carga['posic_final'] <= pos:
                        # Carga totalmente à esquerda
                        if carga['int_inicial'] == carga['int_final']:
                            V[i] -= carga['int_inicial'] * (carga['posic_final'] - carga['posic_inicial'])
                    elif carga['posic_inicial'] <= pos:
                        # Carga parcialmente à esquerda
                        if carga['int_inicial'] == carga['int_final']:
                            V[i] -= carga['int_inicial'] * (pos - carga['posic_inicial'])
            
            # Momento fletor (integral do cortante)
            if i > 0:
                M[i] = M[i-1] + (V[i] + V[i-1]) / 2 * (x[i] - x[i-1])
    
    # Para viga em balanço (1 apoio)
    elif len(apoios) == 1:
        apoio_pos = apoios[0]
        R1 = 0
        M_apoio = 0
        
        # Calcular reação e momento no apoio
        for carga in cargas:
            if carga['tipo'] == 'pontual':
                distancia = carga['posicao'] - apoio_pos
                R1 += carga['intensidade']
                M_apoio += carga['intensidade'] * distancia
            elif carga['tipo'] == 'distribuida':
                if carga['int_inicial'] == carga['int_final']:
                    intensidade = carga['int_inicial']
                    comp_carga = carga['posic_final'] - carga['posic_inicial']
                    pos_centro = (carga['posic_inicial'] + carga['posic_final']) / 2
                    distancia = pos_centro - apoio_pos
                    R1 += intensidade * comp_carga
                    M_apoio += intensidade * comp_carga * distancia
        
        reacoes = [R1]
        
        # Calcular esforço cortante e momento fletor
        for i, pos in enumerate(x):
            if pos >= apoio_pos:
                V[i] = R1
                M[i] = -M_apoio
                
                # Subtrair forças entre apoio e posição atual
                for carga in cargas:
                    if carga['tipo'] == 'pontual' and apoio_pos <= carga['posicao'] <= pos:
                        V[i] -= carga['intensidade']
                        M[i] += carga['intensidade'] * (carga['posicao'] - pos)
                    elif carga['tipo'] == 'distribuida':
                        if apoio_pos <= carga['posic_inicial'] <= pos:
                            comp_efetivo = min(carga['posic_final'], pos) - carga['posic_inicial']
                            if carga['int_inicial'] == carga['int_final']:
                                V[i] -= carga['int_inicial'] * comp_efetivo
                                M[i] += carga['int_inicial'] * comp_efetivo * (carga['posic_inicial'] + comp_efetivo/2 - pos)
    
    return reacoes, V, M, x

def plotar_diagramas_viga(comprimento, apoios, cargas, reacoes, V, M, x, unidade):
    """Plota os diagramas de esforço cortante e momento fletor"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Diagrama de Esforço Cortante
    ax1.plot(x, V, 'b-', linewidth=2, label='Esforço Cortante')
    ax1.fill_between(x, V, alpha=0.3, color='blue')
    ax1.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax1.set_ylabel(f'Cortante ({unidade})', fontsize=12, fontweight='bold')
    ax1.set_title('DIAGRAMA DE ESFORÇO CORTANTE', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Diagrama de Momento Fletor
    ax2.plot(x, M, 'r-', linewidth=2, label='Momento Fletor')
    ax2.fill_between(x, M, alpha=0.3, color='red')
    ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax2.set_ylabel(f'Momento ({unidade}·m)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Posição ao longo da viga (m)', fontsize=12, fontweight='bold')
    ax2.set_title('DIAGRAMA DE MOMENTO FLETOR', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Adicionar apoios
    for apoio in apoios:
        ax1.axvline(x=apoio, color='g', linestyle='--', alpha=0.7, label='Apoio')
        ax2.axvline(x=apoio, color='g', linestyle='--', alpha=0.7, label='Apoio')
    
    # Adicionar cargas
    for carga in cargas:
        if carga['tipo'] == 'pontual':
            ax1.axvline(x=carga['posicao'], color='orange', linestyle=':', alpha=0.7)
            ax2.axvline(x=carga['posicao'], color='orange', linestyle=':', alpha=0.7)
        elif carga['tipo'] == 'distribuida':
            ax1.axvspan(carga['posic_inicial'], carga['posic_final'], alpha=0.2, color='orange')
            ax2.axvspan(carga['posic_inicial'], carga['posic_final'], alpha=0.2, color='orange')
    
    plt.tight_layout()
    return fig

st.markdown("<h1 style='text-align: center; color: #C0C0C0;'>STRUCTURAL CALCULATOR - FURG</h1>",
            unsafe_allow_html=True)
st.image("https://www.furg.br/arquivos/logo-furg.png", width=100)
st.write("Devs: Lizandro Almeida de Oliveira Farias")
st.write("Orientador: Carlos Hernandorena Viegas")
st.subheader("Qual tipo de estrutura você quer calcular?")
st.image(
    image='https://static.vecteezy.com/system/resources/thumbnails/059/935/806/small/structural-truss-design-a-detailed-3d-model-of-a-metal-framework-for-engineering-and-architect-png.png',
    width=150
)
if st.button("Treliça 2D"):
    st.session_state["trelica_ativa"] = True
    st.session_state["viga_ativa"] = False

st.image("https://media.istockphoto.com/id/1484499140/pt/vetorial/steel-beam-icon-steel-industry.jpg?s=612x612&w=0&k=20&c=9GMY85onlQykOeHQuCpXAMk2GTT58D4mirTJ5N08q2I=", width=150)
if st.button("Cálculo de Vigas: Diagramas"):
    st.session_state["viga_ativa"] = True
    st.session_state["trelica_ativa"] = False

# SEÇÃO TRELIÇA (mantida igual)
if st.session_state["trelica_ativa"]:
    st.subheader("CÁLCULO DE TRELIÇAS 2D: DETERMINAÇÃO DE REAÇÕES DE APOIO E FORÇAS INTERNAS")
    st.write(
        "Treliças são estruturas constituídas por barras ligadas entre si por nós articulados. "
        "Cada uma das barras de uma treliça é responsável pela estabilidade da estrutura, "
        "de forma que cada uma delas exerce esforços axiales."
    )

    st.subheader("DETERMINE AS UNIDADES DE MEDIDA! ")
    if st.button("kilonewton(kN)", key="btn_kN"):
        st.session_state["unidade"] = "kN"
        st.success("unidade kN escolhida com sucesso! ")
    if st.button("newton(N)", key="btn_N"):
        st.session_state["unidade"] = "N"
        st.success("unidade N escolhida com sucesso! ")

    st.subheader("1) DETERMINAÇÃO DOS NÓS")
    novo_num_nos = st.slider(
        "Número de Nós",
        min_value=2,
        max_value=100,
        value=st.session_state["num_nos"],
        key="slider_num_nos"
    )
    if novo_num_nos != st.session_state["num_nos"]:
        st.session_state["num_nos"] = novo_num_nos
        atualizar_nos()
        st.session_state["confirmar_nos"] = False

    coordenadas_temp = []
    for i in range(st.session_state["num_nos"]):
        st.markdown(f"Nó {i + 1}")
        col_1, col_2 = st.columns(2)
        with col_1:
            x = st.number_input(
                f"Coordenada X do Nó {i + 1}",
                value=float(st.session_state["nos"][i][0]) if i < len(st.session_state["nos"]) else 0.0,
                key=f"x_input_{i}"
            )
        with col_2:
            y = st.number_input(
                f"Coordenada Y do Nó {i + 1}",
                value=float(st.session_state["nos"][i][1]) if i < len(st.session_state["nos"]) else 0.0,
                key=f"y_input_{i}"
            )
        coordenadas_temp.append((x, y))

    if st.button("Confirmar coordenadas dos nós", key="confirmar_nos_btn"):
        st.session_state["nos"] = coordenadas_temp
        st.session_state["confirmar_nos"] = True
        st.success("Todos os nós foram confirmados!")
        st.rerun()
        
    if st.session_state["confirmar_nos"]:
        df_nos = pd.DataFrame(st.session_state["nos"], columns=["X", "Y"])
        df_nos.index = [f"Nó {i + 1}" for i in range(len(df_nos))]
        st.write("Coordenadas dos Nós")
        st.table(df_nos)

        st.subheader("2) DETERMINAÇÃO DA DISPOSIÇÃO DAS BARRAS")
        # ... (código da treliça mantido igual) ...

# SEÇÃO VIGA
if st.session_state["viga_ativa"]:
    st.subheader("CÁLCULO DE ESFORÇOS EM UMA VIGA ISOSTÁTICA: DETERMINAÇÃO DE REAÇÕES DE APOIO E DIAGRAMAS DE ESFORÇO CORTANTE E MOMENTO FLETOR")
    st.write("Uma viga é um elemento estrutural cujo sua principal função é resistir a cargas transversais, sendo fundamental para a estabilidade da estrutura de uma edificação.")

    st.subheader("DETERMINE AS UNIDADES DE MEDIDA DE FORÇA!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("kilonewton(kN)", key="btn_kN_viga"):
            st.session_state["unidade"] = "kN"
            st.success("unidade kN escolhida com sucesso! ")
    with col2:
        if st.button("newton(N)", key="btn_N_viga"):
            st.session_state["unidade"] = "N"
            st.success("unidade N escolhida com sucesso!")
        
    st.subheader("1) COMPRIMENTO DA VIGA")
    comp_viga = st.number_input("Qual o comprimento da viga? (metros)", 
                               value=st.session_state["comp_viga"], 
                               min_value=1.0, 
                               max_value=100.0,
                               key="comp_viga_input")
    
    if st.button("Confirmar comprimento da viga", key="confirmar_comp_viga"):
        st.session_state["comp_viga"] = comp_viga
        st.success(f"Comprimento da viga definido como {comp_viga} metros!")
        
    st.subheader("2) DETERMINAÇÃO DOS APOIOS")
    num_apoios_viga = st.selectbox("Número de Apoios", [1, 2], key="num_apoios_viga")
    
    apoios_viga_temp = []
    if num_apoios_viga == 1:
        st.write("Posição do apoio único:")
        apoio_pos = st.slider("Posição do apoio (m)", 0.0, float(comp_viga), 0.0, key="apoio_unico")
        apoios_viga_temp.append(apoio_pos)
    else:
        st.write("Posições dos apoios:")
        col1, col2 = st.columns(2)
        with col1:
            apoio1 = st.slider("Posição Apoio 1 (m)", 0.0, float(comp_viga), 0.0, key="apoio1")
        with col2:
            apoio2 = st.slider("Posição Apoio 2 (m)", 0.0, float(comp_viga), float(comp_viga), key="apoio2")
        if apoio1 < apoio2:
            apoios_viga_temp.extend([apoio1, apoio2])
        else:
            st.error("O apoio 1 deve estar antes do apoio 2!")
    
    if st.button("Confirmar apoios", key="confirmar_apoios_viga"):
        st.session_state["apoios_viga"] = apoios_viga_temp
        st.success("Apoios confirmados!")
            
    st.subheader("3) DETERMINAÇÃO DAS CARGAS")
    
    # Listar cargas existentes
    if st.session_state["cargas_viga"]:
        st.write("**Cargas Adicionadas:**")
        dados_cargas = []
        for idx, carga in enumerate(st.session_state["cargas_viga"]):
            if carga['tipo'] == 'pontual':
                dados_cargas.append({
                    "ID": idx + 1,
                    "Tipo": "Pontual",
                    f"Intensidade ({st.session_state['unidade']})": carga['intensidade'],
                    "Posição (m)": carga['posicao']
                })
            else:
                dados_cargas.append({
                    "ID": idx + 1,
                    "Tipo": "Distribuída",
                    f"Int. Inicial ({st.session_state['unidade']}/m)": carga['int_inicial'],
                    f"Int. Final ({st.session_state['unidade']}/m)": carga['int_final'],
                    "Pos. Inicial (m)": carga['posic_inicial'],
                    "Pos. Final (m)": carga['posic_final']
                })
        df_cargas = pd.DataFrame(dados_cargas)
        st.table(df_cargas)
        
        if st.button("Remover Todas as Cargas", key="remover_cargas_btn"):
            st.session_state["cargas_viga"] = []
            st.success("Todas as cargas foram removidas!")
            st.rerun()
    
    st.write("Adicionar nova carga:")
    tipo_carga = st.radio("Tipo de carga:", ["Pontual", "Distribuída"], key="tipo_carga")
    
    if tipo_carga == "Pontual":
        col1, col2 = st.columns(2)
        with col1:
            intensidade = st.number_input(f"Intensidade da carga ({st.session_state['unidade']})", 
                                        value=10.0, key="int_pontual")
        with col2:
            posicao = st.slider("Posição da carga (m)", 0.0, float(comp_viga), 
                               float(comp_viga)/2, key="pos_pontual")
        
        if st.button("Adicionar Carga Pontual", key="add_carga_pontual"):
            st.session_state["cargas_viga"].append({
                'tipo': 'pontual',
                'intensidade': intensidade,
                'posicao': posicao
            })
            st.success("Carga pontual adicionada!")
            st.rerun()
            
    else:  # Carga distribuída
        col1, col2 = st.columns(2)
        with col1:
            int_inicial = st.number_input(f"Intensidade inicial ({st.session_state['unidade']}/m)", 
                                        value=5.0, key="int_inicial")
            posic_inicial = st.slider("Posição inicial (m)", 0.0, float(comp_viga), 
                                    0.0, key="pos_inicial")
        with col2:
            int_final = st.number_input(f"Intensidade final ({st.session_state['unidade']}/m)", 
                                      value=5.0, key="int_final")
            posic_final = st.slider("Posição final (m)", 0.0, float(comp_viga), 
                                   float(comp_viga), key="pos_final")
        
        if posic_inicial >= posic_final:
            st.error("Posição inicial deve ser menor que posição final!")
        else:
            if st.button("Adicionar Carga Distribuída", key="add_carga_distribuida"):
                st.session_state["cargas_viga"].append({
                    'tipo': 'distribuida',
                    'int_inicial': int_inicial,
                    'int_final': int_final,
                    'posic_inicial': posic_inicial,
                    'posic_final': posic_final
                })
                st.success("Carga distribuída adicionada!")
                st.rerun()
    
    # BOTÃO PARA RESOLVER VIGA
    if (st.session_state["apoios_viga"] and st.session_state["cargas_viga"] and 
        st.session_state["comp_viga"] > 0):
        
        if st.button("RESOLVER VIGA E GERAR DIAGRAMAS", key="resolver_viga_btn"):
            try:
                # Resolver a viga
                reacoes, V, M, x = resolver_viga(
                    st.session_state["comp_viga"],
                    st.session_state["apoios_viga"],
                    st.session_state["cargas_viga"]
                )
                
                st.session_state["viga_resolvida"] = True
                st.session_state["reacoes_viga"] = reacoes
                st.session_state["cortante_viga"] = V
                st.session_state["momento_viga"] = M
                st.session_state["posicoes_viga"] = x
                
                st.success("Viga resolvida com sucesso!")
                
            except Exception as e:
                st.error(f"Erro ao resolver a viga: {str(e)}")
    
    # MOSTRAR RESULTADOS
    if st.session_state["viga_resolvida"]:
        st.subheader("RESULTADOS DA ANÁLISE")
        
        # Reações de apoio
        st.write("**REAÇÕES DE APOIO:**")
        dados_reacoes = []
        for i, reacao in enumerate(st.session_state["reacoes_viga"]):
            dados_reacoes.append({
                "Apoio": i + 1,
                f"Reação Vertical ({st.session_state['unidade']})": round(reacao, 3)
            })
        df_reacoes = pd.DataFrame(dados_reacoes)
        st.table(df_reacoes)
        
        # Valores máximos
        V_max = np.max(np.abs(st.session_state["cortante_viga"]))
        M_max = np.max(np.abs(st.session_state["momento_viga"]))
        
        st.write("**VALORES MÁXIMOS:**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"Esforço Cortante Máximo ({st.session_state['unidade']})", 
                     f"{V_max:.3f}")
        with col2:
            st.metric(f"Momento Fletor Máximo ({st.session_state['unidade']}·m)", 
                     f"{M_max:.3f}")
        
        # Diagramas
        st.subheader("DIAGRAMAS DE ESFORÇOS")
        
        fig = plotar_diagramas_viga(
            st.session_state["comp_viga"],
            st.session_state["apoios_viga"],
            st.session_state["cargas_viga"],
            st.session_state["reacoes_viga"],
            st.session_state["cortante_viga"],
            st.session_state["momento_viga"],
            st.session_state["posicoes_viga"],
            st.session_state["unidade"]
        )
        
        st.pyplot(fig)
        
        # Tabela de valores em pontos específicos
        st.subheader("VALORES EM PONTOS ESPECÍFICOS")
        pontos_especificos = [0, st.session_state["comp_viga"]/4, st.session_state["comp_viga"]/2, 
                             3*st.session_state["comp_viga"]/4, st.session_state["comp_viga"]]
        
        dados_pontos = []
        for pos in pontos_especificos:
            idx = np.argmin(np.abs(st.session_state["posicoes_viga"] - pos))
            dados_pontos.append({
                "Posição (m)": round(pos, 2),
                f"Cortante ({st.session_state['unidade']})": round(st.session_state["cortante_viga"][idx], 3),
                f"Momento ({st.session_state['unidade']}·m)": round(st.session_state["momento_viga"][idx], 3)
            })
        
        df_pontos = pd.DataFrame(dados_pontos)
        st.table(df_pontos)
