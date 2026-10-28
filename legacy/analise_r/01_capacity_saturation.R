# ==============================================================================
# SCRIPT R: Saturação de Capacidade e Latência
# Projeto: IC - DataOps
# ==============================================================================

# Carregar pacotes
library(tidyverse)
library(scales)

# ------------------------------------------------------------------------------
# 1. Configurar Caminho do Arquivo
# ------------------------------------------------------------------------------
# Mude este caminho para apontar para a pasta do seu último teste:
data_dir <- "/home/gabriel/Documentos/UNIFEI/IC - DataOps/data/results/performance/druid_capacity/20260818_212232"
file_path <- file.path(data_dir, "capacity_comparison.csv")

# ------------------------------------------------------------------------------
# 2. Leitura e Preparação dos Dados
# ------------------------------------------------------------------------------
df_capacity <- read_csv(file_path, show_col_types = FALSE)

# Ajustar fatores para garantir ordem nos gráficos
df_capacity <- df_capacity %>%
  mutate(
    scenario = factor(scenario, levels = c("scenario_01_baseline", "scenario_02_balanced", "scenario_03_query_heavy"),
                      labels = c("Baseline (1 CPU)", "Balanced (1.5 CPU)", "Heavy (2 CPU)")),
    saturado = as.factor(saturado)
  )

# ------------------------------------------------------------------------------
# 3. Gráfico 1: Vazão (QPS) vs Concorrência
# ------------------------------------------------------------------------------
plot_qps <- ggplot(df_capacity, aes(x = concurrency, y = qps, color = scenario, group = scenario)) +
  geom_line(linewidth = 1.2) +
  geom_point(aes(shape = saturado), size = 3) +
  scale_x_continuous(breaks = unique(df_capacity$concurrency)) +
  scale_color_manual(values = c("#d73027", "#fdae61", "#4575b4")) +
  labs(
    x = "Usuários Simultâneos (Concorrência)",
    y = "Queries por Segundo (QPS)",
    color = "Cenário de Hardware",
    shape = "Saturado"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "bottom")

print(plot_qps)

# ------------------------------------------------------------------------------
# 4. Gráfico 2: Latência Extrema (P95)
# ------------------------------------------------------------------------------
plot_p95 <- ggplot(df_capacity, aes(x = factor(concurrency), y = lat_p95_ms / 1000, fill = scenario)) +
  geom_col(position = "dodge", alpha = 0.8) +
  geom_hline(yintercept = 10, linetype = "dashed", color = "red", linewidth = 1) + # SLA de 10s
  scale_fill_manual(values = c("#d73027", "#fdae61", "#4575b4")) +
  labs(
    x = "Usuários Simultâneos (Concorrência)",
    y = "Latência P95 (Segundos)",
    fill = "Cenário de Hardware"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "bottom")

print(plot_p95)

# Opcional: Salvar gráficos em disco
ggsave("/home/gabriel/Documentos/UNIFEI/IC - DataOps/docs/latex_report/images/qps_saturation.png", plot_qps, width = 10, height = 6)
ggsave("/home/gabriel/Documentos/UNIFEI/IC - DataOps/docs/latex_report/images/p95_latency.png", plot_p95, width = 10, height = 6)

# Gráficos salvos com sucesso
