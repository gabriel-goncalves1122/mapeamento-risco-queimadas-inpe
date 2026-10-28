# ==============================================================================
# SCRIPT R: Consumo de Recursos (CPU e RAM dos Containers)
# Projeto: IC - DataOps
# ==============================================================================

library(tidyverse)

# ------------------------------------------------------------------------------
# 1. Configurar Caminho do Arquivo
# ------------------------------------------------------------------------------
data_dir <- "/home/gabriel/Documentos/UNIFEI/IC - DataOps/data/results/performance/druid_capacity/20260818_212232"
file_path <- file.path(data_dir, "docker_peaks.csv")

# ------------------------------------------------------------------------------
# 2. Leitura e Preparação
# ------------------------------------------------------------------------------
df_docker <- read_csv(file_path, show_col_types = FALSE)

# Filtrar apenas os nós mais relevantes e padronizar nomes
df_docker <- df_docker %>%
  filter(container %in% c("broker", "historical", "middlemanager")) %>%
  mutate(
    scenario = factor(scenario, levels = c("scenario_01_baseline", "scenario_02_balanced", "scenario_03_query_heavy"),
                      labels = c("Baseline (1 CPU)", "Balanced (1.5 CPU)", "Heavy (2 CPU)"))
  )

# ------------------------------------------------------------------------------
# 3. Gráfico 1: Picos de Consumo de CPU
# ------------------------------------------------------------------------------
plot_cpu <- ggplot(df_docker, aes(x = container, y = cpu_max_percent, fill = scenario)) +
  geom_col(position = "dodge", color = "black", alpha = 0.8) +
  geom_hline(yintercept = 100, linetype = "dashed", color = "red") + # Limite de 1 CPU (Pode passar de 100% no Docker se tiver mais de 1 core disponível/limitado)
  scale_fill_manual(values = c("#d73027", "#fdae61", "#4575b4")) +
  labs(
    x = "Nó do Apache Druid",
    y = "Pico de Consumo de CPU (%)",
    fill = "Hardware Disponível"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "bottom")

print(plot_cpu)

# ------------------------------------------------------------------------------
# 4. Gráfico 2: Picos de Consumo de RAM
# ------------------------------------------------------------------------------
plot_ram <- ggplot(df_docker, aes(x = container, y = mem_max_percent, fill = scenario)) +
  geom_col(position = "dodge", color = "black", alpha = 0.8) +
  scale_fill_manual(values = c("#d73027", "#fdae61", "#4575b4")) +
  labs(
    x = "Nó do Apache Druid",
    y = "Pico de Consumo de Memória (%)",
    fill = "Hardware Disponível"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "bottom")

print(plot_ram)

ggsave("/home/gabriel/Documentos/UNIFEI/IC - DataOps/docs/latex_report/images/cpu_peaks.png", plot_cpu, width = 10, height = 6)
# ggsave("/home/gabriel/Documentos/UNIFEI/IC - DataOps/docs/latex_report/images/ram_peaks.png", plot_ram, width = 10, height = 6)

# Fim do script
