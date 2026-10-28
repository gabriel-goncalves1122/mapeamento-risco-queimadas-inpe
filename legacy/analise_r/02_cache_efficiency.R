# ==============================================================================
# SCRIPT R: Eficiência do Warm Cache (Broker/Historical)
# Projeto: IC - DataOps
# ==============================================================================

library(tidyverse)

# ------------------------------------------------------------------------------
# 1. Configurar Caminho do Arquivo
# ------------------------------------------------------------------------------
data_dir <- "/home/gabriel/Documentos/UNIFEI/IC - DataOps/data/results/performance/druid_capacity/20260818_212232"
file_path <- file.path(data_dir, "cache_gain_by_query.csv")

# ------------------------------------------------------------------------------
# 2. Leitura e Preparação
# ------------------------------------------------------------------------------
df_cache <- read_csv(file_path, show_col_types = FALSE)

# Filtrar apenas o cenário Heavy para vermos o poder máximo do cache,
# ou manter todos para comparar se o cache ganha mais em máquinas fracas.
df_cache <- df_cache %>%
  mutate(
    scenario_limpo = gsub("0[0-9]_", "", query_scenario),
    capacity_scenario = factor(capacity_scenario, levels = c("scenario_01_baseline", "scenario_02_balanced", "scenario_03_query_heavy"),
                               labels = c("Baseline", "Balanced", "Heavy"))
  )

# ------------------------------------------------------------------------------
# 3. Gráfico 1: Ganho Percentual do Cache por Tipo de Query
# ------------------------------------------------------------------------------
# Boxplot mostrando a dispersão do ganho de P95 para diferentes eixos analíticos
plot_cache_box <- ggplot(df_cache, aes(x = scenario_limpo, y = p95_gain_percent, fill = scenario_limpo)) +
  geom_boxplot(alpha = 0.7, outlier.size = 2, outlier.color = "red") +
  geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
  labs(
    x = "Família de Queries",
    y = "Ganho de Performance P95 (%)"
  ) +
  theme_minimal(base_size = 14) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1), legend.position = "none")

print(plot_cache_box)

# ------------------------------------------------------------------------------
# 4. Gráfico 2: Tempo Frio vs Tempo Quente
# ------------------------------------------------------------------------------
plot_scatter <- ggplot(df_cache, aes(x = cold_p95_ms, y = warm_p95_ms, color = capacity_scenario)) +
  geom_point(size = 3, alpha = 0.8) +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "black") + # Linha de 1x1
  scale_x_log10(labels = scales::comma) +
  scale_y_log10(labels = scales::comma) +
  labs(
    x = "Latência P95 SEM Cache (ms)",
    y = "Latência P95 COM Cache (ms)",
    color = "Cenário de Infraestrutura"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "bottom")

print(plot_scatter)

ggsave("/home/gabriel/Documentos/UNIFEI/IC - DataOps/docs/latex_report/images/cache_boxplot.png", plot_cache_box, width = 10, height = 6)
# ggsave("/home/gabriel/Documentos/UNIFEI/IC - DataOps/docs/latex_report/images/cache_scatter.png", plot_scatter, width = 10, height = 6)

# Fim do script
