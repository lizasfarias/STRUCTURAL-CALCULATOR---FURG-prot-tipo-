import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
import io

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
    n_points = 1000
    x = np.linspace(0, comprimento, n_points)
    
    V = np.zeros(n_points)
    M = np.zeros(n_points)
    
    if len(apoios) == 2:
        sum_momentos = 0
        sum_forcas_vert = 0
        
        for carga in cargas:
            if carga['tipo'] == 'pontual':
                sum_momentos += carga['intensidade'] * carga['posicao']
                sum_forcas_vert += carga['intensidade']
            elif carga['tipo'] == 'distribuida':
                if carga['int_inicial'] == carga['int_final']:
                    intensidade = carga['int_inicial']
                    comp_carga = carga['posic_final'] - carga['posic_inicial']
                    pos_centro = (carga['posic_inicial'] + carga['posic_final']) / 2
                    sum_momentos += intensidade * comp_carga * pos_centro
                    sum_forcas_vert += intensidade * comp_carga
        
        R2 = sum_momentos / comprimento
        R1 = sum_forcas_vert - R2
        
        reacoes = [R1, R2]
        
        for i, pos in enumerate(x):
            V[i] = R1
            
            for carga in cargas:
                if carga['tipo'] == 'pontual' and carga['posicao'] <= pos:
                    V[i] -= carga['intensidade']
                elif carga['tipo'] == 'distribuida':
                    if carga['posic_final'] <= pos:
                        if carga['int_inicial'] == carga['int_final']:
                            V[i] -= carga['int_inicial'] * (carga['posic_final'] - carga['posic_inicial'])
                    elif carga['posic_inicial'] <= pos:
                        if carga['int_inicial'] == carga['int_final']:
                            V[i] -= carga['int_inicial'] * (pos - carga['posic_inicial'])
            
            if i > 0:
                M[i] = M[i-1] + (V[i] + V[i-1]) / 2 * (x[i] - x[i-1])
    
    elif len(apoios) == 1:
        apoio_pos = apoios[0]
        R1 = 0
        M_apoio = 0
        
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
        
        for i, pos in enumerate(x):
            if pos >= apoio_pos:
                V[i] = R1
                M[i] = -M_apoio
                
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

def desenhar_viga(comprimento, apoios, cargas, unidade):
    fig, ax = plt.subplots(figsize=(12, 5))
    
    ax.plot([0, comprimento], [0, 0], 'k-', linewidth=4, label='Viga')
    
    ax.set_xlim(-0.2, comprimento + 0.2)
    ax.set_ylim(-1, 1)
    ax.set_aspect('auto')
    ax.grid(True, alpha=0.3)
    ax.set_title('REPRESENTAÇÃO DA VIGA', fontsize=14, fontweight='bold')
    ax.set_xlabel('Comprimento (m)', fontweight='bold')
    ax.set_ylabel('', fontweight='bold')
    ax.tick_params(axis='y', which='both', left=False, labelleft=False)
    
    escala_cargas = 0.5
    
    for i, apoio_pos in enumerate(apoios):
        if len(apoios) == 1:
            triangle = plt.Polygon([[apoio_pos-0.3, -0.5], 
                                   [apoio_pos+0.3, -0.5], 
                                   [apoio_pos, 0]], 
                                   color='darkgreen', alpha=0.8)
            ax.add_patch(triangle)
            rect = plt.Rectangle((apoio_pos-0.35, -0.5), 0.7, 0.1, 
                                color='gray', alpha=0.6)
            ax.add_patch(rect)
            ax.text(apoio_pos, -0.7, f'ENGASTE', 
                   ha='center', va='top', fontweight='bold', 
                   fontsize=10, bbox=dict(boxstyle="round,pad=0.3", 
                                         facecolor="lightgreen", 
                                         alpha=0.8))
        else:
            triangle = plt.Polygon([[apoio_pos-0.2, -0.4], 
                                   [apoio_pos+0.2, -0.4], 
                                   [apoio_pos, 0]], 
                                   color='darkred', alpha=0.8)
            ax.add_patch(triangle)
            
            for j in range(3):
                circle = plt.Circle((apoio_pos - 0.1 + j*0.1, -0.45), 
                                   0.03, color='black', alpha=0.5)
                ax.add_patch(circle)
            
            ax.text(apoio_pos, -0.6, f'Apoio {i+1}', 
                   ha='center', va='top', fontweight='bold', 
                   fontsize=10, bbox=dict(boxstyle="round,pad=0.3", 
                                         facecolor="lightcoral", 
                                         alpha=0.8))
    
    for i, carga in enumerate(cargas):
        if carga['tipo'] == 'pontual':
            pos = carga['posicao']
            intensidade = carga['intensidade']
            
            cor_carga = 'blue' if intensidade > 0 else 'darkblue'
            
            altura_seta = 0.8 * escala_cargas * min(1, abs(intensidade)/50)
            
            if intensidade > 0:
                ax.arrow(pos, 0, 0, altura_seta, 
                        head_width=0.15, head_length=0.15, 
                        fc=cor_carga, ec=cor_carga, 
                        linewidth=3, alpha=0.8)
                ax.text(pos, altura_seta + 0.05, 
                       f'{abs(intensidade):.1f} {unidade}', 
                       ha='center', va='bottom', fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", 
                                facecolor="lightblue", 
                                alpha=0.8))
            else:
                ax.arrow(pos, 0, 0, -altura_seta, 
                        head_width=0.15, head_length=0.15, 
                        fc=cor_carga, ec=cor_carga, 
                        linewidth=3, alpha=0.8)
                ax.text(pos, -altura_seta - 0.05, 
                       f'{abs(intensidade):.1f} {unidade}', 
                       ha='center', va='top', fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", 
                                facecolor="lightblue", 
                                alpha=0.8))
            
            ax.axvline(x=pos, color='gray', linestyle=':', 
                      alpha=0.5, linewidth=1)
            
            ax.plot(pos, 0, 'ro', markersize=8, alpha=0.7)
    
    for i, carga in enumerate(cargas):
        if carga['tipo'] == 'distribuida':
            x_inicio = carga['posic_inicial']
            x_fim = carga['posic_final']
            int_inicio = carga['int_inicial']
            int_fim = carga['int_final']
            
            if int_inicio == int_fim:
                altura = 0.6 * escala_cargas * min(1, abs(int_inicio)/20)
                
                ax.hlines(y=altura, xmin=x_inicio, xmax=x_fim, 
                         color='purple', linewidth=3, alpha=0.8)
                
                num_setas = min(8, int((x_fim - x_inicio) / 0.5))
                if num_setas > 0:
                    for j in range(num_setas):
                        x_pos = x_inicio + (x_fim - x_inicio) * (j + 0.5) / num_setas
                        ax.arrow(x_pos, altura, 0, -altura, 
                                head_width=0.08, head_length=0.08,
                                fc='purple', ec='purple', 
                                linewidth=2, alpha=0.7)
                
                ax.text((x_inicio + x_fim)/2, altura + 0.05, 
                       f'{abs(int_inicio):.1f} {unidade}/m', 
                       ha='center', va='bottom', fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", 
                                facecolor="lavender", 
                                alpha=0.8))
                
                ax.fill_between([x_inicio, x_fim], 0, altura, 
                               alpha=0.1, color='purple')
            
            else:
                x = np.linspace(x_inicio, x_fim, 50)
                y_max = max(abs(int_inicio), abs(int_fim))
                y_norm = np.linspace(int_inicio, int_fim, 50) / y_max * 0.6 * escala_cargas
                
                ax.fill_between(x, 0, y_norm, alpha=0.2, color='orange')
                
                for pos, intens in [(x_inicio, int_inicio), 
                                   ((x_inicio + x_fim)/2, (int_inicio + int_fim)/2), 
                                   (x_fim, int_fim)]:
                    altura = abs(intens) / y_max * 0.6 * escala_cargas
                    if intens > 0:
                        ax.arrow(pos, altura, 0, -altura, 
                                head_width=0.08, head_length=0.08,
                                fc='orange', ec='orange')
                    else:
                        ax.arrow(pos, 0, 0, altura, 
                                head_width=0.08, head_length=0.08,
                                fc='orange', ec='orange')
                
                ax.text((x_inicio + x_fim)/2, 0.4 * escala_cargas, 
                       f'Carga variável\n{int_inicio:.1f} → {int_fim:.1f} {unidade}/m', 
                       ha='center', va='center', fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", 
                                facecolor="wheat", 
                                alpha=0.8))
    
    return fig

def plotar_diagramas_viga(comprimento, apoios, cargas, reacoes, V, M, x, unidade):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    ax1.plot(x, V, 'b-', linewidth=3, label='Esforço Cortante')
    ax1.fill_between(x, V, alpha=0.3, color='blue')
    ax1.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax1.set_ylabel(f'Cortante ({unidade})', fontsize=12, fontweight='bold')
    ax1.set_title('DIAGRAMA DE ESFORÇO CORTANTE', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')
    
    for apoio in apoios:
        ax1.axvline(x=apoio, color='green', linestyle='--', 
                   alpha=0.7, linewidth=2)
        ax1.text(apoio, ax1.get_ylim()[1]*0.9, f'Apoio', 
                ha='center', va='top', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.2", 
                         facecolor="lightgreen", 
                         alpha=0.8))
    
    for carga in cargas:
        if carga['tipo'] == 'pontual':
            ax1.axvline(x=carga['posicao'], color='orange', 
                       linestyle=':', alpha=0.7, linewidth=2)
            ax1.text(carga['posicao'], ax1.get_ylim()[0]*0.9, 
                    f'Carga: {carga["intensidade"]:.1f} {unidade}', 
                    ha='center', va='bottom', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", 
                             facecolor="lightyellow", 
                             alpha=0.8))
    
    ax2.plot(x, M, 'r-', linewidth=3, label='Momento Fletor')
    ax2.fill_between(x, M, alpha=0.3, color='red')
    ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax2.set_ylabel(f'Momento ({unidade}·m)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Posição ao longo da viga (m)', fontsize=12, fontweight='bold')
    ax2.set_title('DIAGRAMA DE MOMENTO FLETOR', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')
    
    for apoio in apoios:
        ax2.axvline(x=apoio, color='green', linestyle='--', 
                   alpha=0.7, linewidth=2)
    
    for carga in cargas:
        if carga['tipo'] == 'pontual':
            ax2.axvline(x=carga['posicao'], color='orange', 
                       linestyle=':', alpha=0.7, linewidth=2)
        elif carga['tipo'] == 'distribuida':
            ax2.axvspan(carga['posic_inicial'], carga['posic_final'], 
                       alpha=0.1, color='orange')
    
    V_max = np.max(np.abs(V))
    M_max = np.max(np.abs(M))
    
    ax1.text(0.02, 0.98, f'Cortante máximo: {V_max:.2f} {unidade}', 
            transform=ax1.transAxes, fontsize=10, 
            verticalalignment='top',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5))
    
    ax2.text(0.02, 0.98, f'Momento máximo: {M_max:.2f} {unidade}·m', 
            transform=ax2.transAxes, fontsize=10, 
            verticalalignment='top',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5))
    
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

if st.session_state["viga_ativa"]:
    st.subheader("CÁLCULO DE ESFORÇOS EM UMA VIGA ISOSTÁTICA: DETERMINAÇÃO DE REAÇÕES DE APOIO E DIAGRAMAS DE ESFORÇO CORTANTE E MOMENTO FLETOR")
    st.write("Uma viga é um elemento estrutural cujo sua principal função é resistir a cargas transversais, sendo fundamental para a estabilidade da estrutura de uma edificação.")

    st.subheader("DETERMINE AS UNIDADES DE MEDIDA DE FORÇA!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("kilonewton(kN)", key="btn_kN_viga"):
            st.session_state["unidade"] = "kN"
            st.success("Unidade kN escolhida com sucesso! ")
    with col2:
        if st.button("newton(N)", key="btn_N_viga"):
            st.session_state["unidade"] = "N"
            st.success("Unidade N escolhida com sucesso!")
        
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
        st.write("VIGA EM BALANÇO (ENGASTE ÚNICO)")
        apoio_pos = st.slider("Posição do engaste (m)", 0.0, float(comp_viga), 0.0, key="apoio_unico")
        apoios_viga_temp.append(apoio_pos)
    else:
        st.write("VIGA BIAPOIADA")
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
    
    if st.session_state["cargas_viga"]:
        st.write("**CARGAS ADICIONADAS:**")
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
    
    st.write("**ADICIONAR NOVA CARGA:**")
    tipo_carga = st.radio("Tipo de carga:", ["Pontual", "Distribuída"], key="tipo_carga")
    
    if tipo_carga == "Pontual":
        col1, col2, col3 = st.columns(3)
        with col1:
            intensidade = st.number_input(f"Intensidade ({st.session_state['unidade']})", 
                                        value=10.0, key="int_pontual")
        with col2:
            direcao = st.selectbox("Direção", ["Para baixo (+)","Para cima (-)"], key="dir_pontual")
        with col3:
            posicao = st.slider("Posição (m)", 0.0, float(comp_viga), 
                               float(comp_viga)/2, key="pos_pontual")
        
        if st.button("Adicionar Carga Pontual", key="add_carga_pontual"):
            intensidade_final = intensidade if direcao == "Para baixo (+)" else -intensidade
            st.session_state["cargas_viga"].append({
                'tipo': 'pontual',
                'intensidade': intensidade_final,
                'posicao': posicao
            })
            st.success("Carga pontual adicionada!")
            st.rerun()
            
    else:
        col1, col2 = st.columns(2)
        with col1:
            int_inicial = st.number_input(f"Intensidade inicial ({st.session_state['unidade']}/m)", 
                                        value=5.0, key="int_inicial")
            direcao_inicial = st.selectbox("Direção inicial", ["Para baixo (+)","Para cima (-)"], key="dir_inicial")
            posic_inicial = st.slider("Posição inicial (m)", 0.0, float(comp_viga), 
                                    0.0, key="pos_inicial")
        with col2:
            int_final = st.number_input(f"Intensidade final ({st.session_state['unidade']}/m)", 
                                      value=5.0, key="int_final")
            direcao_final = st.selectbox("Direção final", ["Para baixo (+)","Para cima (-)"], key="dir_final")
            posic_final = st.slider("Posição final (m)", 0.0, float(comp_viga), 
                                   float(comp_viga), key="pos_final")
        
        int_inicial_final = int_inicial if direcao_inicial == "Para baixo (+)" else -int_inicial
        int_final_final = int_final if direcao_final == "Para baixo (+)" else -int_final
        
        if posic_inicial >= posic_final:
            st.error("Posição inicial deve ser menor que posição final!")
        else:
            if st.button("Adicionar Carga Distribuída", key="add_carga_distribuida"):
                st.session_state["cargas_viga"].append({
                    'tipo': 'distribuida',
                    'int_inicial': int_inicial_final,
                    'int_final': int_final_final,
                    'posic_inicial': posic_inicial,
                    'posic_final': posic_final
                })
                st.success("Carga distribuída adicionada!")
                st.rerun()
    
    if (st.session_state["apoios_viga"] and st.session_state["cargas_viga"] and 
        st.session_state["comp_viga"] > 0):
        
        st.subheader("4) VISUALIZAÇÃO E CÁLCULO")
        
        st.write("**VISUALIZAÇÃO DA VIGA:**")
        if st.session_state["apoios_viga"] and st.session_state["cargas_viga"]:
            fig_viga = desenhar_viga(
                st.session_state["comp_viga"],
                st.session_state["apoios_viga"],
                st.session_state["cargas_viga"],
                st.session_state["unidade"]
            )
            st.pyplot(fig_viga)
        
        if st.button("RESOLVER VIGA E GERAR DIAGRAMAS", key="resolver_viga_btn"):
            try:
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
    
    if st.session_state["viga_resolvida"]:
        st.subheader("RESULTADOS DA ANÁLISE")
        
        st.write("**REAÇÕES DE APOIO:**")
        dados_reacoes = []
        for i, reacao in enumerate(st.session_state["reacoes_viga"]):
            dados_reacoes.append({
                "Apoio": i + 1,
                f"Reação Vertical ({st.session_state['unidade']})": round(reacao, 3)
            })
        df_reacoes = pd.DataFrame(dados_reacoes)
        st.table(df_reacoes)
        
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
        
        st.write("**OBSERVAÇÕES:**")
        if len(st.session_state["apoios_viga"]) == 1:
            st.info("Viga em balanço: O momento no engaste é máximo e negativo (tração nas fibras superiores).")
        else:
            st.info("Viga biapoiada: Os momentos nos apoios são nulos e o momento máximo ocorre no vão.")
        
        if st.button("NOVA ANÁLISE", key="nova_analise_btn"):
            st.session_state["viga_resolvida"] = False
            st.session_state["cargas_viga"] = []
            st.session_state["apoios_viga"] = []
            st.rerun()
