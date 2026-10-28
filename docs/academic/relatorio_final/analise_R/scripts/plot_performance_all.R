# ==============================================================================
# Script Analítico de Performance - Apache Druid (R + ggplot2)
# Autor: Agent Antigravity
# ==============================================================================

# 1. Preparação do Ambiente ---------------------------------------------------
if (!require(ggplot2)) install.packages("ggplot2", repos = "http://cran.us.r-project.org")
if (!require(dplyr)) install.packages("dplyr", repos = "http://cran.us.r-project.org")
if (!require(viridis)) install.packages("viridis", repos = "http://cran.us.r-project.org")

library(ggplot2)
library(dplyr)
library(viridis)

csv_path <- "../../../../performance/druid_capacity/20260818_212232/tables/capacity_enriched.csv"
output_dir <- "../plots/"

df <- read.csv(csv_path)

# Ordenando a concorrência como fator quantitativo
df$concurrency_factor <- factor(df$concurrency, levels = sort(unique(df$concurrency)))
# Ajustando Rótulos para ficar mais elegante
df$scenario_label <- gsub("Cenario 1 - Baseline", "Baseline (1.0 CPU)", df$scenario_label)
df$scenario_label <- gsub("Cenario 2 - Balanced", "Balanced (1.5 CPU)", df$scenario_label)
df$scenario_label <- gsub("Cenario 3 - Query Heavy", "Query Heavy (2.0 CPU)", df$scenario_label)

# 2. Curva de Saturação Exponencial (QPS vs. Concorrência) --------------------
p_qps <- ggplot(df, aes(x = concurrency, y = qps, color = scenario_label, group = scenario_label)) +
  geom_line(linewidth = 1.2) +
  geom_point(size = 3) +
  theme_minimal(base_size = 14) +
  scale_color_viridis(discrete = TRUE, option = "D") +
  scale_x_continuous(breaks = unique(df$concurrency)) +
  labs(
    x = "Nº de Usuários Concorrentes (Threads)",
    y = "Queries Per Second (QPS)",
    color = "Hardware Analítico"
  ) +
  theme(legend.position = "bottom")

ggsave(filename = paste0(output_dir, "qps_saturation_new.png"), plot = p_qps, width = 9, height = 6, dpi = 300)

# 3. A "Explosão" da Latência (Gráfico de Área para P95) ----------------------
p_lat <- ggplot(df, aes(x = concurrency, y = lat_p95_ms, fill = scenario_label, color = scenario_label)) +
  geom_area(alpha = 0.4, position = "identity", linewidth = 1) +
  theme_minimal(base_size = 14) +
  scale_fill_viridis(discrete = TRUE, option = "C") +
  scale_color_viridis(discrete = TRUE, option = "C") +
  scale_x_continuous(breaks = unique(df$concurrency)) +
  labs(
    x = "Nº de Usuários Concorrentes (Threads)",
    y = "Latência P95 (Milissegundos)",
    fill = "Hardware Analítico",
    color = "Hardware Analítico"
  ) +
  theme(legend.position = "bottom")

ggsave(filename = paste0(output_dir, "p95_latency_new.png"), plot = p_lat, width = 9, height = 6, dpi = 300)



# 5. Retorno sobre o Investimento em CPU (Eficiência) -------------------------
# Filtramos para observar a eficiência no momento máximo de tensão (16 threads, ou máxima onde a query heavy sobreviveu)
df_efficiency <- df %>% 
  group_by(scenario_label) %>%
  summarise(avg_efficiency = mean(qps_per_allocated_cpu_pair, na.rm=TRUE)) %>%
  arrange(avg_efficiency)

df_efficiency$scenario_label <- factor(df_efficiency$scenario_label, levels = df_efficiency$scenario_label)

p_eff <- ggplot(df_efficiency, aes(x = scenario_label, y = avg_efficiency)) +
  geom_segment(aes(x = scenario_label, xend = scenario_label, y = 0, yend = avg_efficiency), color = "gray", linewidth = 2) +
  geom_point(color = "#2c7bb6", size = 6) +
  coord_flip() +
  theme_minimal(base_size = 14) +
  labs(
    x = "",
    y = "Eficiência Média (QPS / CPU)"
  )

ggsave(filename = paste0(output_dir, "cpu_efficiency_new.png"), plot = p_eff, width = 8, height = 4, dpi = 300)

cat("Gráficos avançados gerados em:", output_dir, "\n")
