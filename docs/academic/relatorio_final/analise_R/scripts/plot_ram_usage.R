# ==============================================================================
# Script Analítico de Consumo de RAM (Docker Stats)
# Autor: Agent Antigravity
# ==============================================================================

if (!require(ggplot2)) install.packages("ggplot2", repos = "http://cran.us.r-project.org")
if (!require(dplyr)) install.packages("dplyr", repos = "http://cran.us.r-project.org")
if (!require(viridis)) install.packages("viridis", repos = "http://cran.us.r-project.org")

library(ggplot2)
library(dplyr)
library(viridis)

# Diretório base
base_dir <- "../../../../../pipelines/gold/data/results/performance/druid_capacity/20260818_212232/scenario_02_balanced/"
stats_path <- paste0(base_dir, "docker_stats.csv")
output_dir <- "../plots/"

cat("Lendo dados físicos do Docker...\n")
df_stats <- read.csv(stats_path)

# Tratamento de dados: Convertendo strings de tempo para valores numéricos contínuos (minutos)
df_clean <- df_stats %>%
  filter(container %in% c("broker", "historical")) %>% # Isolando motores analíticos
  mutate(
    timestamp = as.POSIXct(timestamp, format="%Y-%m-%dT%H:%M:%S", tz="UTC"),
    # Define a contagem de tempo do 0 (minutos de execução)
    tempo_minutos = as.numeric(difftime(timestamp, min(timestamp, na.rm=TRUE), units="mins")),
    container = tools::toTitleCase(container) # Deixa Broker e Historical maiúsculos
  )

# Removendo NAs por segurança
df_clean <- df_clean[!is.na(df_clean$tempo_minutos) & !is.na(df_clean$mem_percent), ]

cat("Gerando plot de Linha Temporal (Memory Footprint)...\n")

p_ram <- ggplot(df_clean, aes(x = tempo_minutos, y = mem_percent, color = container)) +
  geom_line(linewidth = 1.2, alpha = 0.8) +
  scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 20)) +
  scale_color_viridis(discrete = TRUE, option = "D", begin = 0.2, end = 0.8) +
  theme_minimal(base_size = 14) +
  labs(
    x = "Tempo Decorrido (Minutos)",
    y = "Uso de Memória RAM (%)",
    color = "Nó do Druid"
  ) +
  theme(legend.position = "top")

ggsave(filename = paste0(output_dir, "ram_usage_new.png"), plot = p_ram, width = 8, height = 5, dpi = 300)

cat("Gráfico salvo em:", output_dir, "\n")
