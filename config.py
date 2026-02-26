# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/config.py
import os

# ============ DATABASE CONFIG ============
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ordens_servico")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_PORT = os.getenv("DB_PORT", "5432")

# ============ APPLICATION CONFIG ============
SECRET_KEY = os.getenv("SECRET_KEY", "sua_chave_secreta_aqui")

# ============ ROLES AND PERMISSIONS ============
VALID_ROLES = ["admin", "tecnico", "tecnico_recarga", "administrativo"]

ROLES_DISPLAY = {
    "admin": "Administrador",
    "tecnico": "Técnico",
    "tecnico_recarga": "Técnico Recarga",
    "administrativo": "Administrativo"
}

# ============ SISTEMA DE OS - SECRETARIAS ============
# "Selecione..." foi removido desta lista
SECRETARIAS = [
    "CIDADANIA", "COMUNICAÇÃO", "CONTROLE INTERNO",
    "CULTURA E ESPORTES", "DESENVOLVIMENTO ECONÔMICO", "EDUCAÇÃO",
    "FAZENDA", "FORÇA POLICIAL", "GOVERNO", "INFRAESTRUTURA", "OUTROS",
    "PROCURADORIA", "SAÚDE", "SEGURANÇA", "SUSTENTABILIDADE"
]

# ============ SISTEMA DE OS - TÉCNICOS ============
# "Selecione..." foi removido desta lista
TECNICOS = [
    "ABIMADÉSIO", "ANTONY CAUÃ", "DIEGO CARDOSO",
    "DIEL BATISTA", "JOSAFÁ MEDEIROS", "MAYKON RODOLFO", "ROMÉRIO CIRQUEIRA",
    "VALMIR FRANCISCO", "CLEBER QUINTINO"
]

# ============ SISTEMA DE OS - CATEGORIAS ============
# "Selecione..." foi removido desta lista
CATEGORIAS = [
    "CFTV", "COMPUTADORES", "IMPRESSORAS", "OUTROS",
    "REDES", "SISTEMAS", "TELEFONIA", "CONFIGURAÇÃO", "INSTALAÇÃO", "MANUTENÇÃO"
]

# ============ SISTEMA DE OS - EQUIPAMENTOS ============
# "Selecione..." foi removido desta lista
EQUIPAMENTOS = [
    "CAMERA", "CELULAR", "COMPUTADOR", "IMPRESSORA",
    "MONITOR", "NOBREAK", "NOTEBOOK", "PERIFÉRICO", "TABLET", "TRANSFORMADOR",
    "ROTEADOR", "SISTEMA", "SOFTWARE", "TELEFONE"
]

# ============ SISTEMA DE OS - STATUS ============
# Esta lista permanece como está, pois "Todos" é um filtro funcional
STATUS_OPTIONS = [
    "EM ABERTO", "AGUARDANDO PEÇA(S)", "FINALIZADO", "AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"
]

# Filtros para dashboard/relatórios
STATUS_FILTRO = [
    "Todos", "EM ABERTO", "AGUARDANDO PEÇA(S)", "FINALIZADO", "AGUARDANDO RETIRADA", "ENTREGUE AO CLIENTE"
]

# ============ SISTEMA DE LAUDOS - COMPONENTES ============
# "Selecione..." foi removido desta lista
COMPONENTES_LAUDO = [
    "PROCESSADOR (CPU)", "MEMÓRIA RAM", "HD/SSD SATA",
    "SSD M.2 NVME", "PLACA MÃE", "PLACA DE VÍDEO", "FONTE DE ALIMENTAÇÃO",
    "COOLER/VENTOINHA", "PASTA TÉRMICA", "BATERIA (NOTEBOOK)", "TELA/DISPLAY",
    "TECLADO", "TOUCHPAD", "WEBCAM", "CABO/CONECTOR", "OUTRO"
]

# ============ SISTEMA DE LAUDOS - STATUS ============
# Esta lista permanece como está, pois não tinha placeholder
STATUS_LAUDO = [
    "PENDENTE", "APROVADO", "NEGADO"
]

# ============ SISTEMA DE EQUIPAMENTOS - CATEGORIAS ============
# "Selecione..." foi removido desta lista
CATEGORIAS_EQUIP = [
    "COMPUTADOR", "NOTEBOOK", "IMPRESSORA", "SCANNER",
    "MONITOR", "SWITCH", "ROTEADOR", "ACCESS POINT", "FIREWALL",
    "SERVIDOR", "NOBREAK", "ESTABILIZADOR", "CAMERA", "DVR/NVR",
    "TELEFONE IP", "PERIFÉRICO", "OUTRO"
]