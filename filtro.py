# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/filtro.py
# VERSÃO FINAL - Todos os bugs de modal corrigidos
import streamlit as st
import pandas as pd
from database import get_connection
from sqlalchemy import text
from config import (
    SECRETARIAS,
    TECNICOS,
    STATUS_OPTIONS,
    EQUIPAMENTOS,
    CATEGORIAS,
)
from import_export import exportar_filtrados_para_excel
import base64
import math
import pytz
from datetime import datetime


# ============================================================================
# FUNÇÕES AUXILIARES DE BANCO DE DADOS
# ============================================================================

def f_deletar_os(conn, os_id, os_type):
    """Deleta uma OS específica do banco de dados."""
    table_name = "os_interna" if os_type == "Interna" else "os_externa"
    try:
        with conn.connect() as con:
            with con.begin():
                query = text(f"DELETE FROM {table_name} WHERE id = :id")
                con.execute(query, {"id": os_id})
        st.success(f"OS (ID: {os_id}) deletada com sucesso.")
        return True
    except Exception as e:
        st.error(f"Erro ao deletar OS: {e}")
        return False


def f_atualizar_os(conn, table_name, os_id, dados):
    """Atualiza uma OS específica no banco de dados."""
    try:
        with conn.connect() as con:
            with con.begin():
                set_clause = []
                params = {"id": os_id}
                for key, value in dados.items():
                    if key != "id":
                        set_clause.append(f"{key} = :{key}")
                        params[key] = value

                if not set_clause:
                    st.error("Nenhum dado para atualizar.")
                    return False

                query = text(
                    f"UPDATE {table_name} SET {', '.join(set_clause)} WHERE id = :id"
                )
                con.execute(query, params)
        st.success(f"Ordem de Serviço (ID: {os_id}) atualizada com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar OS: {e}")
        return False


# ============================================================================
# FUNÇÃO DE LIMPEZA DE ESTADOS DOS MODAIS
# ============================================================================

def limpar_estados_modais():
    """Limpa todos os estados relacionados aos modais para evitar conflitos."""
    if "view_os_id" in st.session_state:
        del st.session_state.view_os_id
    if "edit_os_data" in st.session_state:
        del st.session_state.edit_os_data
    if "delete_os_data" in st.session_state:
        del st.session_state.delete_os_data


# ============================================================================
# FUNÇÕES DE EXIBIÇÃO
# ============================================================================

def display_os_details(os_data):
    """Exibe os detalhes de uma OS."""
    st.markdown(f"#### Detalhes Completos da OS: {os_data.get('numero', 'N/A')}")

    col_map = {
        "numero": "Número",
        "tipo": "Tipo",
        "status": "Status",
        "secretaria": "Secretaria",
        "setor": "Setor",
        "solicitante": "Solicitante",
        "telefone": "Telefone",
        "data": "Data de Entrada",
        "hora": "Hora de Entrada",
        "tecnico": "Técnico",
        "equipamento": "Equipamento",
        "patrimonio": "Patrimônio",
        "categoria": "Categoria",
        "data_finalizada": "Data de Finalização",
        "data_retirada": "Data de Retirada",
        "registrado_por": "Registrado Por",
    }

    display_data = []
    for col, label in col_map.items():
        if col in os_data and pd.notna(os_data[col]):
            value = os_data[col]
            if col == "data" and value:
                try:
                    value = pd.to_datetime(value).strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
            if col == "hora" and value:
                try:
                    value = pd.to_datetime(str(value)).strftime("%H:%M:%S")
                except (ValueError, TypeError):
                    pass
            if col in ["data_finalizada", "data_retirada"] and value:
                try:
                    value = (
                        pd.to_datetime(value, utc=True)
                        .tz_convert("America/Sao_Paulo")
                        .strftime("%d/%m/%Y %H:%M:%S")
                    )
                except (ValueError, TypeError):
                    pass
            display_data.append([f"**{label}**", value])

    st.table(pd.DataFrame(display_data, columns=["Campo", "Valor"]))

    st.markdown("**Solicitação do Cliente:**")
    st.text_area(
        "solicitacao_exp",
        value=os_data.get("solicitacao_cliente", "") or "",
        disabled=True,
        label_visibility="collapsed",
        height=100,
    )

    st.markdown("**Serviço Executado / Descrição:**")
    texto_completo = f"{os_data.get('servico_executado', '') or ''}\n{os_data.get('descricao', '') or ''}".strip()
    st.text_area(
        "servico_exp",
        value=texto_completo,
        disabled=True,
        label_visibility="collapsed",
        height=100,
    )

    if os_data.get("status") == "ENTREGUE AO CLIENTE":
        st.markdown("---")
        st.markdown("#### Informações da Entrega")
        retirada_por = os_data.get("retirada_por")
        if pd.notna(retirada_por):
            st.write(f"**Nome do recebedor:** {retirada_por}")

    if os_data.get("laudo_pdf") is not None and len(os_data.get("laudo_pdf")) > 0:
        st.markdown("---")
        st.markdown("#### Laudo Técnico (Anexo PDF Antigo)")
        pdf_data = (
            bytes(os_data["laudo_pdf"])
            if isinstance(os_data["laudo_pdf"], memoryview)
            else os_data["laudo_pdf"]
        )
        st.download_button(
            label=f"Baixar Laudo PDF ({os_data.get('laudo_filename')})",
            data=pdf_data,
            file_name=os_data.get('laudo_filename'),
            mime="application/pdf",
        )


# ============================================================================
# MODAIS - DEFINIDOS COMO @st.dialog
# ============================================================================

@st.dialog("Detalhes Completos da Ordem de Serviço", width="large")
def modal_detalhes(os_data, conn):
    """Modal para exibir detalhes completos da OS."""
    display_os_details(os_data)
    st.markdown("---")
    st.markdown("#### Laudos de Avaliação Associados")

    tipo_os_laudo = os_data.get('tipo')
    numero_os = os_data.get('numero')
    laudos_registrados = []

    try:
        query_laudos = text(
            "SELECT * FROM laudos "
            "WHERE numero_os = :num AND tipo_os = :tipo "
            "ORDER BY id DESC"
        )
        with conn.connect() as con:
            results = con.execute(
                query_laudos,
                {"num": numero_os, "tipo": tipo_os_laudo},
            ).fetchall()
            laudos_registrados = [r._mapping for r in results]
    except Exception as e:
        st.error(f"Erro ao buscar laudos: {e}")

    if not laudos_registrados:
        st.info("Nenhum laudo de avaliação registrado para esta OS.")
    else:
        fuso_sp = pytz.timezone("America/Sao_Paulo")
        for laudo in laudos_registrados:
            data_reg = laudo["data_registro"].astimezone(fuso_sp).strftime("%d/%m/%Y %H:%M")
            exp_title = (
                f"Laudo ID {laudo['id']} - "
                f"{laudo.get('estado_conservacao')} "
                f"({laudo['status']}) - Reg. {data_reg}"
            )
            with st.expander(exp_title):
                st.markdown(f"**Técnico:** {laudo['tecnico']}")
                st.markdown(f"**Estado de Conservação:** {laudo.get('estado_conservacao')}")
                st.markdown(f"**Equipamento Completo:** {laudo.get('equipamento_completo')}")
                st.markdown("**Diagnóstico:**")
                st.text_area(
                    f"diag_{laudo['id']}",
                    laudo.get("diagnostico", ""),
                    height=100,
                    disabled=True,
                    label_visibility="collapsed",
                )
                if laudo.get("observacoes"):
                    st.markdown("**Observações:**")
                    st.text_area(
                        f"obs_{laudo['id']}",
                        laudo["observacoes"],
                        height=80,
                        disabled=True,
                        label_visibility="collapsed",
                    )
                st.markdown("---")

    if st.button("Fechar Detalhes", use_container_width=True, key="close_modal_detalhes"):
        limpar_estados_modais()
        st.rerun()


@st.dialog("Editar Ordem de Serviço", width="large")
def modal_editar(os_data, conn):
    """Modal para editar uma OS."""
    os_tipo = os_data.get("tipo")
    table_name = "os_interna" if os_tipo == "Interna" else "os_externa"

    st.markdown(f"### Editando OS #{os_data.get('numero', 'N/A')}")
    st.markdown(f"**Tipo:** {os_tipo} | **Status Atual:** {os_data.get('status', 'N/A')}")
    st.markdown("---")

    with st.form("form_editar_os"):
        col1, col2, col3 = st.columns(3)

        with col1:
            status = st.selectbox(
                "Status *",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(os_data.get("status", "EM ABERTO"))
                if os_data.get("status") in STATUS_OPTIONS
                else 0,
            )

        with col2:
            secretaria = st.selectbox(
                "Secretaria *",
                sorted(SECRETARIAS),
                index=sorted(SECRETARIAS).index(os_data.get("secretaria"))
                if os_data.get("secretaria") in sorted(SECRETARIAS)
                else 0,
            )

        with col3:
            setor = st.text_input(
                "Setor",
                value=os_data.get("setor", ""),
                placeholder="Ex: TI, Administrativo",
            )

        col1, col2, col3 = st.columns(3)

        with col1:
            tecnico = st.selectbox(
                "Técnico *",
                sorted(TECNICOS),
                index=sorted(TECNICOS).index(os_data.get("tecnico"))
                if os_data.get("tecnico") in sorted(TECNICOS)
                else 0,
            )

        with col2:
            equipamento = st.text_input(
                "Equipamento",
                value=os_data.get("equipamento", ""),
                placeholder="Ex: Desktop, Impressora",
            )

        with col3:
            patrimonio = st.text_input(
                "Patrimônio",
                value=os_data.get("patrimonio", ""),
                placeholder="Ex: PA-2024-001",
            )

        col1, col2 = st.columns(2)

        with col1:
            categoria = st.selectbox(
                "Categoria",
                [""] + sorted(CATEGORIAS),
                index=([""] + sorted(CATEGORIAS)).index(os_data.get("categoria", ""))
                if os_data.get("categoria")
                else 0,
            )

        with col2:
            data_finalizada = st.date_input(
                "Data de Finalização",
                value=pd.to_datetime(os_data.get("data_finalizada")).date()
                if pd.notna(os_data.get("data_finalizada"))
                else None,
            )

        st.markdown("#### Descrição do Serviço")
        servico_executado = st.text_area(
            "Serviço Executado",
            value=os_data.get("servico_executado", ""),
            height=150,
            placeholder="Descreva o serviço realizado...",
        )

        submitted = st.form_submit_button(
            "Salvar Alterações",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            if not secretaria or not tecnico or not status:
                st.error("Preencha todos os campos obrigatórios (marcados com *).")
            else:
                dados_atualizacao = {
                    "status": status,
                    "secretaria": secretaria,
                    "setor": setor if setor else None,
                    "tecnico": tecnico,
                    "equipamento": equipamento if equipamento else None,
                    "patrimonio": patrimonio if patrimonio else None,
                    "categoria": categoria if categoria else None,
                    "servico_executado": servico_executado if servico_executado else None,
                    "data_finalizada": data_finalizada if data_finalizada else None,
                }

                if f_atualizar_os(conn, table_name, os_data.get("id"), dados_atualizacao):
                    limpar_estados_modais()
                    st.session_state.df_filtrado = pd.DataFrame()
                    st.rerun()

    st.markdown("---")
    if st.button("Cancelar", use_container_width=True, key="cancel_edit"):
        limpar_estados_modais()
        st.rerun()


@st.dialog("Confirmar Exclusão", width="large")
def modal_excluir(os_data, conn):
    """Modal para confirmar exclusão de OS."""
    st.warning(f"**Você tem certeza que deseja deletar a OS {os_data.get('numero')}?**")
    st.markdown("Esta ação não pode ser desfeita.")
    st.markdown(f"**Tipo:** {os_data.get('tipo')}")
    st.markdown(f"**Secretaria:** {os_data.get('secretaria')}")
    st.markdown(f"**Solicitante:** {os_data.get('solicitante')}")
    st.markdown("---")

    col1, col2 = st.columns(2)

    if col1.button("Confirmar Exclusão", type="primary", use_container_width=True):
        if f_deletar_os(conn, os_data.get("id"), os_data.get("tipo")):
            limpar_estados_modais()
            st.session_state.df_filtrado = pd.DataFrame()
            st.rerun()

    if col2.button("Cancelar", use_container_width=True, key="cancel_delete"):
        limpar_estados_modais()
        st.rerun()


# ============================================================================
# FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO
# ============================================================================

def render():
    st.markdown("## Filtro de Ordens de Serviço")
    conn = get_connection()
    role = st.session_state.get("role", "")

    # Verificar permissões
    pode_editar = role in ["admin", "administrativo"]
    pode_deletar = role in ["admin", "administrativo"]

    # Filtros
    with st.expander("Filtros de Pesquisa", expanded=True):
        f_numero_os = st.text_input(
            "Número da OS",
            placeholder="Digite o número da OS para buscar diretamente",
            help="Filtrar por número específico da Ordem de Serviço"
        )

        col1, col2 = st.columns(2)

        with col1:
            f_tipo = st.selectbox("Tipo de OS", ["Todos", "Interna", "Externa"])
            f_status = st.multiselect("Status", STATUS_OPTIONS)
            f_secretaria = st.multiselect("Secretaria", SECRETARIAS)

        with col2:
            f_tecnico = st.multiselect("Técnico", TECNICOS)
            f_categoria = st.multiselect("Categoria", CATEGORIAS)
            f_equipamento = st.multiselect("Equipamento", EQUIPAMENTOS)

        col_data1, col_data2 = st.columns(2)
        with col_data1:
            f_data_inicio = st.date_input("Data Inicial")
        with col_data2:
            f_data_fim = st.date_input("Data Final")

        filtrar = st.button("Aplicar Filtros", use_container_width=True, type="primary")

    # ============================================================================
    # CORREÇÃO CRÍTICA: Detectar mudanças nos filtros e limpar modais
    # ============================================================================

    # Criar snapshot dos filtros atuais
    filtros_atuais = {
        "numero_os": f_numero_os,
        "tipo": f_tipo,
        "status": tuple(f_status) if f_status else (),
        "secretaria": tuple(f_secretaria) if f_secretaria else (),
        "tecnico": tuple(f_tecnico) if f_tecnico else (),
        "categoria": tuple(f_categoria) if f_categoria else (),
        "equipamento": tuple(f_equipamento) if f_equipamento else (),
        "data_inicio": str(f_data_inicio) if f_data_inicio else "",
        "data_fim": str(f_data_fim) if f_data_fim else "",
    }

    # Comparar com filtros anteriores salvos
    filtros_anteriores = st.session_state.get("filtros_anteriores", {})

    # Se os filtros mudaram (mesmo sem clicar no botão), limpar modais
    if filtros_atuais != filtros_anteriores:
        limpar_estados_modais()
        st.session_state.filtros_anteriores = filtros_atuais

    # Executar filtro
    if filtrar or "df_filtrado" in st.session_state:
        if filtrar:
            # Limpar estados dos modais ao aplicar novos filtros
            limpar_estados_modais()

            where_clauses = []
            params = {}

            if f_numero_os and f_numero_os.strip():
                where_clauses.append("numero = :numero_os")
                params["numero_os"] = f_numero_os.strip()

            if f_status:
                placeholders = ",".join([f":st{i}" for i in range(len(f_status))])
                where_clauses.append(f"status IN ({placeholders})")
                for i, st_val in enumerate(f_status):
                    params[f"st{i}"] = st_val

            if f_secretaria:
                placeholders = ",".join([f":sec{i}" for i in range(len(f_secretaria))])
                where_clauses.append(f"secretaria IN ({placeholders})")
                for i, sec in enumerate(f_secretaria):
                    params[f"sec{i}"] = sec

            if f_tecnico:
                placeholders = ",".join([f":tec{i}" for i in range(len(f_tecnico))])
                where_clauses.append(f"tecnico IN ({placeholders})")
                for i, tec in enumerate(f_tecnico):
                    params[f"tec{i}"] = tec

            if f_categoria:
                placeholders = ",".join([f":cat{i}" for i in range(len(f_categoria))])
                where_clauses.append(f"categoria IN ({placeholders})")
                for i, cat in enumerate(f_categoria):
                    params[f"cat{i}"] = cat

            if f_equipamento:
                placeholders = ",".join([f":eq{i}" for i in range(len(f_equipamento))])
                where_clauses.append(f"equipamento IN ({placeholders})")
                for i, eq in enumerate(f_equipamento):
                    params[f"eq{i}"] = eq

            # Filtros de data (só aplicar se não houver busca por número)
            if not (f_numero_os and f_numero_os.strip()):
                if f_data_inicio:
                    where_clauses.append("data >= :data_inicio")
                    params["data_inicio"] = f_data_inicio

                if f_data_fim:
                    where_clauses.append("data <= :data_fim")
                    params["data_fim"] = f_data_fim

            where_str = ""
            if where_clauses:
                where_str = " WHERE " + " AND ".join(where_clauses)

            query_interna_base = "SELECT *, 'Interna' as tipo FROM os_interna"
            query_externa_base = "SELECT *, 'Externa' as tipo FROM os_externa"
            queries_to_union = []

            if f_tipo == "Interna" or f_tipo == "Todos":
                queries_to_union.append(f"({query_interna_base}{where_str})")

            if f_tipo == "Externa" or f_tipo == "Todos":
                queries_to_union.append(f"({query_externa_base}{where_str})")

            if not queries_to_union:
                st.warning("Nenhuma OS encontrada para o tipo selecionado.")
                st.session_state.df_filtrado = pd.DataFrame()
                st.session_state.filtro_page = 1
                return

            query_final = " UNION ALL ".join(queries_to_union)
            query_final += " ORDER BY data DESC, hora DESC"

            try:
                with conn.connect() as con:
                    result = con.execute(text(query_final), params)
                    rows = result.fetchall()
                    columns = result.keys()
                    df = pd.DataFrame(rows, columns=columns)

                st.session_state.df_filtrado = df
                st.session_state.filtro_page = 1
            except Exception as e:
                st.error(f"Erro ao executar filtro: {e}")
                st.exception(e)
                return

        df = st.session_state.df_filtrado

        if df.empty:
            st.info("Nenhuma OS encontrada com os filtros aplicados.")
            return

        st.success(f"**{len(df)} OS(s) encontrada(s)**")

        # Exportar para Excel
        if len(df) > 0:
            excel_data = exportar_filtrados_para_excel(df)
            if excel_data:
                b64 = base64.b64encode(excel_data).decode()
                href = (
                    f'<a href="data:application/vnd.openxmlformats-'
                    f'officedocument.spreadsheetml.sheet;base64,{b64}" '
                    f'download="os_filtradas.xlsx">Baixar Excel</a>'
                )
                st.markdown(href, unsafe_allow_html=True)

        # Paginação
        if "filtro_page" not in st.session_state:
            st.session_state.filtro_page = 1

        ITEMS_PER_PAGE = 10
        total_items = len(df)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

        if st.session_state.filtro_page > total_pages:
            st.session_state.filtro_page = total_pages
        if st.session_state.filtro_page < 1:
            st.session_state.filtro_page = 1

        start_idx = (st.session_state.filtro_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        df_page = df.iloc[start_idx:end_idx]

        st.markdown("---")
        st.info(
            f"Exibindo **{len(df_page)}** de **{total_items}** OS "
            f"(Página {st.session_state.filtro_page}/{total_pages})"
        )

        # Cabeçalho da tabela
        if pode_editar:
            cols_header = st.columns((1, 1, 1.5, 1.5, 1, 1.5, 2))
            headers = ["Número", "Tipo", "Secretaria", "Solicitante", "Status", "Data", "Ações"]
        else:
            cols_header = st.columns((1, 1, 1.5, 1.5, 1, 1.5, 1))
            headers = ["Número", "Tipo", "Secretaria", "Solicitante", "Status", "Data", "Ações"]

        for col, header in zip(cols_header, headers):
            col.markdown(f"**{header}**")

        st.markdown("---")

        # Renderizar linhas
        for idx, row in df_page.iterrows():
            if pode_editar:
                cols = st.columns((1, 1, 1.5, 1.5, 1, 1.5, 2))
            else:
                cols = st.columns((1, 1, 1.5, 1.5, 1, 1.5, 1))

            cols[0].write(str(row["numero"]))
            cols[1].write(str(row["tipo"]))
            cols[2].write(str(row["secretaria"]))
            cols[3].write(str(row["solicitante"]))

            status_val = str(row["status"])
            if status_val == "EM ABERTO":
                cols[4].markdown(f"🔴 {status_val}")
            elif status_val == "AGUARDANDO PEÇA(S)":
                cols[4].markdown(f"🟠 {status_val}")
            elif status_val == "FINALIZADO":
                cols[4].markdown(f"🟢 {status_val}")
            else:
                cols[4].write(status_val)

            try:
                data_formatada = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")
                cols[5].write(data_formatada)
            except Exception:
                cols[5].write(str(row["data"]))

            # Ações
            if pode_editar:
                col_a, col_b, col_c = cols[6].columns(3)

                if col_a.button("👁️", key=f"view_{idx}", help="Visualizar detalhes"):
                    limpar_estados_modais()
                    st.session_state.view_os_id = idx
                    st.rerun()

                if col_b.button("✏️", key=f"edit_{idx}", help="Editar OS"):
                    limpar_estados_modais()
                    st.session_state.edit_os_data = row.to_dict()
                    st.rerun()

                if pode_deletar:
                    if col_c.button("🗑️", key=f"del_{idx}", help="Deletar OS"):
                        limpar_estados_modais()
                        st.session_state.delete_os_data = row.to_dict()
                        st.rerun()
            else:
                if cols[6].button("👁️", key=f"view_{idx}", help="Visualizar detalhes"):
                    limpar_estados_modais()
                    st.session_state.view_os_id = idx
                    st.rerun()

        # Controles de paginação
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if st.button("⏮️ Primeira", disabled=(st.session_state.filtro_page == 1)):
                st.session_state.filtro_page = 1
                st.rerun()

        with col2:
            if st.button("◀️ Anterior", disabled=(st.session_state.filtro_page == 1)):
                st.session_state.filtro_page -= 1
                st.rerun()

        with col3:
            st.markdown(
                f"<div style='text-align: center;'>"
                f"Página {st.session_state.filtro_page} de {total_pages}</div>",
                unsafe_allow_html=True,
            )

        with col4:
            if st.button("▶️ Próxima", disabled=(st.session_state.filtro_page >= total_pages)):
                st.session_state.filtro_page += 1
                st.rerun()

        with col5:
            if st.button("⏭️ Última", disabled=(st.session_state.filtro_page >= total_pages)):
                st.session_state.filtro_page = total_pages
                st.rerun()

    # ============================================================================
    # RENDERIZAÇÃO DOS MODAIS - NO FINAL PARA EVITAR CONFLITOS
    # ============================================================================

    # Renderizar apenas UM modal por vez com verificação exclusiva
    if "view_os_id" in st.session_state and st.session_state.view_os_id is not None:
        try:
            os_data = st.session_state.df_filtrado.iloc[st.session_state.view_os_id]
            modal_detalhes(os_data, conn)
        except (IndexError, KeyError):
            st.error("Erro ao carregar dados da OS. Aplicando filtros novamente.")
            limpar_estados_modais()
            st.rerun()

    elif "edit_os_data" in st.session_state and st.session_state.edit_os_data is not None:
        modal_editar(st.session_state.edit_os_data, conn)

    elif "delete_os_data" in st.session_state and st.session_state.delete_os_data is not None:
        modal_excluir(st.session_state.delete_os_data, conn)