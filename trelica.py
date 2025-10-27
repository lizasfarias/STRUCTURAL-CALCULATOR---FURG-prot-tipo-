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


def atualizar_nos():
    st.session_state["nos"] = [(0.0, 0.0) for _ in range(st.session_state["num_nos"])]


def atualizar_barras():
    st.session_state["barras"] = [(1, 2) for _ in range(st.session_state["num_barras"])]


def atualizar_apoios():
    st.session_state["apoios"] = [
        {"no": i + 1, "tipo": "Apoio de primeiro gênero (fixo em X)", "restricao_x": False, "restricao_y": False}
        for i in range(st.session_state["num_apoios"])]


st.markdown("<h1 style='text-align: center; color: #C0C0C0;'>STRUCTURAL CALCULATOR - FURG</h1>",
            unsafe_allow_html=True)
st.image("https://www.furg.br/arquivos/logo-furg.png", width=100)
st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTmz3bTUgaU5raqIVmyc_30uahw7JlLHNYgSQ&s", width=100)
st.subheader("Qual tipo de estrutura você quer calcular?")
st.image(
    image='https://static.vecteezy.com/system/resources/thumbnails/059/935/806/small/structural-truss-design-a-detailed-3d-model-of-a-metal-framework-for-engineering-and-architect-png.png',
    width=150
)
st.write("Devs: Lizandro Almeida de Oliveira Farias - FURG")
st.write("Orientador: Carlos Hernandorena Viegas")

if st.button("Treliça 2D"):
    st.session_state["trelica_ativa"] = True

if st.session_state["trelica_ativa"]:
    st.subheader("CÁLCULO DE TRELIÇAS 2D: DETERMINAÇÃO DE REAÇÕES DE APOIO E FORÇAS INTERNAS")
    st.write(
        "Treliças são estruturas constituídas por barras ligadas entre si por nós articulados. "
        "Cada uma das barras de uma treliça é responsável pela estabilidade da estrutura, "
        "de forma que cada uma delas exerce esforços axiales."
    )

    st.subheader("DETERMINE AS UNIDADES DE MEDIDA! ")
    if st.button("kilonewton(kN)"):
        st.session_state["unidade"] = "kN"
        st.success("unidade kN escolhida com sucesso! ")
    if st.button("newton(N)"):
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
        novo_num_barras = st.slider(
            "Número de Barras",
            min_value=1,
            max_value=100,
            value=st.session_state["num_barras"],
            key="slider_num_barras"
        )
        if novo_num_barras != st.session_state["num_barras"]:
            st.session_state["num_barras"] = novo_num_barras
            atualizar_barras()
            st.session_state["confirmar_barras"] = False

        barras_temp = []
        for i in range(st.session_state["num_barras"]):
            col1, col2 = st.columns(2)
            with col1:
                no_in = st.number_input(
                    f"Nó inicial da barra {i + 1}",
                    min_value=1,
                    max_value=st.session_state["num_nos"],
                    value=int(st.session_state["barras"][i][0]) if i < len(st.session_state["barras"]) else 1,
                    key=f"no_in_{i}"
                )
            with col2:
                no_fin = st.number_input(
                    f"Nó final da barra {i + 1}",
                    min_value=1,
                    max_value=st.session_state["num_nos"],
                    value=int(st.session_state["barras"][i][1]) if i < len(st.session_state["barras"]) else 2,
                    key=f"no_fin_{i}"
                )
            barras_temp.append((no_in, no_fin))

        if st.button("Confirmar Barras", key="confirmar_barras_btn"):
            st.session_state["barras"] = barras_temp
            st.session_state["confirmar_barras"] = True
            st.success("Barras confirmadas com sucesso!")
            st.rerun()

        if st.session_state["confirmar_barras"]:
            df_barras = pd.DataFrame(st.session_state["barras"], columns=["Nó Inicial", "Nó Final"])
            df_barras.index = [f"Barra {i + 1}" for i in range(len(df_barras))]
            st.write("Disposição das Barras:")
            st.table(df_barras)

            st.subheader("3) DETERMINAÇÃO DAS FORÇAS EXTERNAS")
            st.write("EM QUAL NÓ VOCÊ QUER ADICIONAR A FORÇA EXTERNA? ")

            no_selec = st.selectbox(
                "Selecione o nó para aplicar a força: ",
                options=[f"Nó {i + 1}" for i in range(st.session_state["num_nos"])],
                key="no_forc"
            )

            numero_no = int(no_selec.split()[1])
            forx, fory = st.columns(2)
            with forx:
                fx = st.number_input(
                    f"Força Horizontal no {no_selec}",
                    value=0.0,
                    key=f'fx_{numero_no}'
                )
            with fory:
                fy = st.number_input(
                    f"Força Vertical no {no_selec}",
                    value=0.0,
                    key=f'fy_{numero_no}'
                )
            if st.button("Adicionar Força", key="adicionar_forca_btn"):
                st.session_state["forcas_externas"].append({
                    "no": numero_no,
                    "fx": fx,
                    "fy": fy
                })
                st.success(f"Força adicionada ao {no_selec}")
                st.rerun()

            if st.session_state["forcas_externas"]:
                st.write("**Forças Externas Adicionadas:**")
                dados_forcas = []
                for forca in st.session_state["forcas_externas"]:
                    dados_forcas.append({
                        "Nó": forca["no"],
                        f"FX ({st.session_state['unidade']})": forca["fx"],
                        f"FY ({st.session_state['unidade']})": forca["fy"]
                    })

                df_forcas = pd.DataFrame(dados_forcas)
                st.table(df_forcas)

            if st.button("Finalizar adição de forças", key="finalizar_forcas_btn"):
                st.session_state["forcas_finalizadas"] = True
                st.success("Forças externas definidas")
                st.rerun()

            if st.session_state["forcas_finalizadas"]:
                st.subheader("4) DETERMINAÇÃO DAS REAÇÕES DE APOIO")
                novo_num_apoios = st.slider(
                    "Número de Apoios",
                    min_value=1,
                    max_value=3,
                    value=st.session_state["num_apoios"],
                    key="slider_num_apoios"
                )

                if novo_num_apoios != st.session_state["num_apoios"]:
                    st.session_state["num_apoios"] = novo_num_apoios
                    atualizar_apoios()
                    st.session_state["confirmar_apoios"] = False

                apoios_temp = []
                for i in range(st.session_state["num_apoios"]):
                    st.markdown(f"Apoio {i + 1}")

                    no_apoio = st.selectbox(
                        f"Selecione o nó para o apoio {i + 1}",
                        options=[f"Nó {j + 1}" for j in range(st.session_state["num_nos"])],
                        key=f"no_apoio_{i}"
                    )

                    numero_no_apoio = int(no_apoio.split()[1])

                    tipo_apoio = st.selectbox(
                        f"Selecione o tipo de apoio para o {no_apoio}",
                        options=[
                            "Apoio de primeiro gênero (fixo em X)",
                            "Apoio de primeiro gênero (fixo em Y)",
                            "Apoio de segundo gênero (fixo em X e Y)",
                        ],
                        key=f"tipo_apoio_{i}"
                    )

                    if tipo_apoio == "Apoio de primeiro gênero (fixo em X)":
                        restricao_x = True
                        restricao_y = False
                    elif tipo_apoio == "Apoio de primeiro gênero (fixo em Y)":
                        restricao_x = False
                        restricao_y = True
                    elif tipo_apoio == "Apoio de segundo gênero (fixo em X e Y)":
                        restricao_x = True
                        restricao_y = True

                    apoios_temp.append({
                        "no": numero_no_apoio,
                        "tipo": tipo_apoio,
                        "restricao_x": restricao_x,
                        "restricao_y": restricao_y
                    })

                if st.button("Confirmar Apoios", key="confirmar_apoios_btn"):
                    st.session_state["apoios"] = apoios_temp
                    st.session_state["confirmar_apoios"] = True
                    st.success("Apoios definidos!")
                    st.rerun()

                if st.session_state["confirmar_apoios"]:
                    st.write("**Apoios Definidos:**")
                    dados_apoios = []
                    for apoio in st.session_state["apoios"]:
                        dados_apoios.append({
                            "Nó": apoio["no"],
                            "Tipo de Apoio": apoio["tipo"],
                            "Restrição X": "Sim" if apoio["restricao_x"] else "Não",
                            "Restrição Y": "Sim" if apoio["restricao_y"] else "Não"
                        })
                    df_apoios = pd.DataFrame(dados_apoios)
                    st.table(df_apoios)

                    if st.button("RESOLVER TRELIÇA"):
                        quant_nos = len(st.session_state["nos"])
                        quant_barras = len(st.session_state["barras"])
                        quant_restricoes = sum(1 for apoio in st.session_state["apoios"]
                                               for restricao in [apoio["restricao_x"], apoio["restricao_y"]]
                                               if restricao)

                        total_variaveis = quant_barras + quant_restricoes

                        if 2 * quant_nos != total_variaveis:
                            st.error(
                                f"Treliça não é isostática! Equações: {2 * quant_nos}, Incógnitas: {total_variaveis}")
                            st.stop()

                        COEF = np.zeros((2 * quant_nos, total_variaveis))
                        FEXT = np.zeros(2 * quant_nos)

                        for i, (no_in, no_fin) in enumerate(st.session_state["barras"]):
                            xi, yi = st.session_state["nos"][no_in - 1]
                            xf, yf = st.session_state["nos"][no_fin - 1]

                            dx = xf - xi
                            dy = yf - yi
                            L = np.sqrt(dx ** 2 + dy ** 2)

                            if L == 0:
                                st.error(f"Barra {i + 1} tem comprimento zero!")
                                st.stop()
                            cos = dx / L
                            sen = dy / L

                            COEF[2 * (no_in - 1), i] = cos
                            COEF[2 * (no_in - 1) + 1, i] = sen
                            COEF[2 * (no_fin - 1), i] = -cos
                            COEF[2 * (no_fin - 1) + 1, i] = -sen

                        forcas_dict = {}
                        for forca in st.session_state["forcas_externas"]:
                            no = forca["no"]
                            forcas_dict[no] = (forca["fx"], forca["fy"])

                        for i in range(1, quant_nos + 1):
                            fx, fy = forcas_dict.get(i, (0.0, 0.0))
                            FEXT[2 * (i - 1)] = -fx
                            FEXT[2 * (i - 1) + 1] = -fy

                        coluna_atual = quant_barras

                        apoio_lista = []
                        for apoio in st.session_state["apoios"]:
                            no = apoio["no"]
                            if apoio["restricao_x"]:
                                COEF[2 * (no - 1), coluna_atual] = 1
                                apoio_lista.append((no, 'X'))
                                coluna_atual += 1
                            if apoio["restricao_y"]:
                                COEF[2 * (no - 1) + 1, coluna_atual] = 1
                                apoio_lista.append((no, 'Y'))
                                coluna_atual += 1

                        try:
                            solucao = np.linalg.solve(COEF, FEXT)

                            forcas_nas_barras = solucao[:quant_barras]
                            reacoes_apoio = solucao[quant_barras:quant_barras + quant_restricoes]

                            st.success("Treliça resolvida com sucesso!")

                            st.subheader("FORÇAS NAS BARRAS")
                            dados_barras = []
                            for i, forca in enumerate(forcas_nas_barras):
                                dados_barras.append({
                                    "Barra": i + 1,
                                    f"Força ({st.session_state['unidade']})": round(forca, 4),
                                    "Tipo": "TRAÇÃO" if forca > 0 else "COMPRESSÃO"
                                })
                            df_barras = pd.DataFrame(dados_barras)
                            st.dataframe(df_barras)

                            st.subheader("REAÇÕES DE APOIO")
                            dados_reacoes = []
                            coluna = 0
                            for i, (no, direcao) in enumerate(apoio_lista):
                                dados_reacoes.append({
                                    "Nó": no,
                                    "Direção": direcao,
                                    f"Reação ({st.session_state['unidade']})": round(reacoes_apoio[i], 4)
                                })
                            df_reacoes = pd.DataFrame(dados_reacoes)
                            st.dataframe(df_reacoes)

                            st.subheader("VISUALIZAÇÃO GRÁFICA DA TRELIÇA")

                            numero_de_nos = {i + 1: coord for i, coord in enumerate(st.session_state["nos"])}
                            barra = st.session_state["barras"]
                            forca = {f["no"]: (f["fx"], f["fy"]) for f in st.session_state["forcas_externas"]}
                            apoio = apoio_lista
                            resultado = np.concatenate([forcas_nas_barras, reacoes_apoio])
                            unit = 2 if st.session_state["unidade"] == "kN" else 1

                            fig, ax = plt.subplots(figsize=(14, 10))
                            plt.rcParams['font.family'] = 'DejaVu Sans'
                            plt.rcParams['font.size'] = 10

                            todos_x = [coord[0] for coord in numero_de_nos.values()]
                            todos_y = [coord[1] for coord in numero_de_nos.values()]
                            margem_x = (max(todos_x) - min(todos_x)) * 0.3
                            margem_y = (max(todos_y) - min(todos_y)) * 0.3

                            plt.xlim(min(todos_x) - margem_x, max(todos_x) + margem_x)
                            plt.ylim(min(todos_y) - margem_y, max(todos_y) + margem_y)

                            if resultado is not None:
                                forces_barras = resultado[:len(barra)]
                                if len(forces_barras) > 0:
                                    max_force = np.max(np.abs(forces_barras))
                                    norm = Normalize(vmin=-max_force, vmax=max_force)
                                else:
                                    norm = Normalize(vmin=-1, vmax=1)
                                cmap = cm.coolwarm

                            for i, (ni, nf) in enumerate(barra):
                                x0, y0 = numero_de_nos[ni]
                                x1, y1 = numero_de_nos[nf]

                                if resultado is not None and i < len(resultado):
                                    f = resultado[i]
                                    cor = cmap(norm(f)) if f != 0 else 'gray'
                                    espessura = 2 + 3 * abs(norm(f))
                                else:
                                    cor = 'black'
                                    espessura = 2

                                plt.plot([x0, x1], [y0, y1], color=cor, linewidth=espessura, zorder=1)

                                if resultado is not None and i < len(resultado):
                                    xm = (x0 + x1) / 2
                                    ym = (y0 + y1) / 2
                                    offset_x = (y1 - y0) * 0.08
                                    offset_y = (x1 - x0) * -0.08

                                    label = f'{abs(resultado[i]):.1f} {"KN" if unit == 2 else "N"}'
                                    plt.text(xm + offset_x, ym + offset_y, label,
                                             color=cor, fontsize=10, ha='center', va='center', fontweight='bold',
                                             bbox=dict(boxstyle="round,pad=0.3", facecolor='white',
                                                       alpha=0.9, edgecolor=cor, linewidth=1))

                            for n, (x, y) in numero_de_nos.items():
                                plt.plot(x, y, 'o', color='black', markersize=10, zorder=3, markeredgewidth=2)
                                plt.text(x + 0.15, y + 0.15, f'Nó {n}', fontsize=11, fontweight='bold',
                                         bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.8))

                            tamanho_medio = (margem_x + margem_y) / 2
                            escala_forca = tamanho_medio * 0.15

                            for n, (fx, fy) in forca.items():
                                if fx != 0 or fy != 0:
                                    x, y = numero_de_nos[n]
                                    magnitude = np.sqrt(fx ** 2 + fy ** 2)

                                    if magnitude > 0:
                                        fator_escala = escala_forca * (1 + magnitude / 10)
                                        fx_norm = fx / magnitude * fator_escala
                                        fy_norm = fy / magnitude * fator_escala

                                        arrow = plt.arrow(x, y, fx_norm, fy_norm,
                                                          head_width=fator_escala * 0.4,
                                                          head_length=fator_escala * 0.6,
                                                          fc='#2E8B57', ec='#2E8B57',
                                                          linewidth=3, zorder=4, alpha=0.9)

                                        angulo = np.degrees(np.arctan2(fy, fx))
                                        offset_label = fator_escala * 1.8

                                        plt.text(x + fx_norm * 1.5, y + fy_norm * 1.5,
                                                 f'F={magnitude:.1f} {"KN" if unit == 2 else "N"}',
                                                 fontsize=11, color='#2E8B57', ha='center', va='center',
                                                 fontweight='bold', rotation=angulo,
                                                 bbox=dict(boxstyle="round,pad=0.4", facecolor='white',
                                                           alpha=0.95, edgecolor='#2E8B57', linewidth=2))

                            if resultado is not None:
                                reacoes_por_no = {}
                                for j, (nodo, direcao) in enumerate(apoio):
                                    if j < len(resultado) - len(barra):
                                        valor = resultado[len(barra) + j]
                                        if nodo not in reacoes_por_no:
                                            reacoes_por_no[nodo] = {'X': 0, 'Y': 0}
                                        reacoes_por_no[nodo][direcao] += valor

                                for nodo, reacoes in reacoes_por_no.items():
                                    x, y = numero_de_nos[nodo]

                                    if reacoes['X'] != 0:
                                        direcao = 1 if reacoes['X'] > 0 else -1
                                        arrow_x = plt.arrow(x, y, reacoes['X'] / abs(reacoes['X']) * escala_forca * 0.8,
                                                            0,
                                                            head_width=escala_forca * 0.35,
                                                            head_length=escala_forca * 0.5,
                                                            fc='#FF6B6B', ec='#FF6B6B',
                                                            linewidth=3, zorder=4, alpha=0.9)

                                        plt.text(x + direcao * escala_forca * 1.2, y + escala_forca * 0.3,
                                                 f'Rx={abs(reacoes["X"]):.1f} {"KN" if unit == 2 else "N"}',
                                                 fontsize=11, color='#FF6B6B', ha='center', va='center',
                                                 fontweight='bold',
                                                 bbox=dict(boxstyle="round,pad=0.3", facecolor='white',
                                                           alpha=0.95, edgecolor='#FF6B6B', linewidth=2))

                                    if reacoes['Y'] != 0:
                                        direcao = 1 if reacoes['Y'] > 0 else -1
                                        arrow_y = plt.arrow(x, y, 0,
                                                            reacoes['Y'] / abs(reacoes['Y']) * escala_forca * 0.8,
                                                            head_width=escala_forca * 0.35,
                                                            head_length=escala_forca * 0.5,
                                                            fc='#4ECDC4', ec='#4ECDC4',
                                                            linewidth=3, zorder=4, alpha=0.9)

                                        plt.text(x + escala_forca * 0.3, y + direcao * escala_forca * 1.2,
                                                 f'Ry={abs(reacoes["Y"]):.1f} {"KN" if unit == 2 else "N"}',
                                                 fontsize=11, color='#4ECDC4', ha='center', va='center',
                                                 fontweight='bold',
                                                 bbox=dict(boxstyle="round,pad=0.3", facecolor='white',
                                                           alpha=0.95, edgecolor='#4ECDC4', linewidth=2))

                            simbolos = {'X': '>', 'Y': '^'}
                            cores_apoio = {'X': '#FF6B6B', 'Y': '#4ECDC4'}

                            for n, direcao in apoio:
                                x, y = numero_de_nos[n]
                                plt.plot(x, y, simbolos[direcao], color=cores_apoio[direcao],
                                         markersize=12, markeredgewidth=2, zorder=3, alpha=0.8)

                            legenda_elements = [
                                plt.Line2D([0], [0], color='red', lw=3, label='Tração'),
                                plt.Line2D([0], [0], color='blue', lw=3, label='Compressão'),
                                plt.Line2D([0], [0], color='#2E8B57', lw=3, marker='>', markersize=10,
                                           label='Força Externa'),
                                plt.Line2D([0], [0], color='#FF6B6B', lw=3, marker='>', markersize=10,
                                           label='Reação em X'),
                                plt.Line2D([0], [0], color='#4ECDC4', lw=3, marker='^', markersize=10,
                                           label='Reação em Y'),
                                plt.Line2D([0], [0], marker='o', color='black', markersize=8, label='Nó',
                                           linestyle='None')
                            ]

                            ax.legend(handles=legenda_elements, loc='upper right',
                                      bbox_to_anchor=(1.18, 1), fontsize=10, framealpha=0.9)

                            plt.xlabel('Coordenada X', fontsize=12, fontweight='bold')
                            plt.ylabel('Coordenada Y', fontsize=12, fontweight='bold')
                            plt.title('ANÁLISE DE TRELIÇA', fontsize=16, fontweight='bold', pad=20)
                            plt.grid(True, alpha=0.2, linestyle='--')
                            plt.axis('equal')

                            ax.set_facecolor('#f0f8ff')
                            ax.grid(True, color='white', linestyle='-', linewidth=1, alpha=0.7)

                            plt.tight_layout()

                            st.pyplot(fig)
                            plt.close(fig)

                        except np.linalg.LinAlgError:
                            st.error("Sistema singular! Verifique se a treliça é estável e isostática.")
                        except Exception as e:

                            st.error(f"Erro no cálculo: {str(e)}")
