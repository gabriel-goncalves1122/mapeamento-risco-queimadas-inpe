# ==============================================================================
# Script Analítico de Eficiência de Cache - Apache Druid (R + ggplot2)
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
cold_path <- paste0(base_dir, "raw_requests_cold.csv")
warm_path <- paste0(base_dir, "raw_requests_warm.csv")
output_dir <- "../plots/"

cat("Lendo dados de Cache Cold...\n")
df_cold <- read.csv(cold_path)
cat("Lendo dados de Cache Warm...\n")
df_warm <- read.csv(warm_path)

# Empilhando as bases (a flag cache_mode já existe internamente como 'cold' ou 'warm')
df_raw <- bind_rows(df_cold, df_warm)

# Filtrando apenas requisições bem sucedidas e manipulando rótulos
df_clean <- df_raw %>%
  filter(status == "OK") %>%
  mutate(
    cache_mode = factor(cache_mode, levels = c("cold", "warm"), labels = c("Cold (Disco)", "Warm (Memória)")),
    # Previne log10(0) caso existam consultas mágicas de 0ms 
    latencia_ms = ifelse(latencia_ms <= 0, 1, latencia_ms) 
  )

cat("Dados filtrados. Total de execuções válidas:", nrow(df_clean), "\n")

# Gerando Violin Plot com Boxplot interno e escala Log10
p_cache <- ggplot(df_clean, aes(x = cache_mode, y = latencia_ms, fill = cache_mode)) +
  geom_violin(alpha = 0.6, color = "darkgray", trim = FALSE) +
  geom_boxplot(width = 0.15, color = "black", alpha = 0.8, outlier.shape = NA) +
  scale_y_log10(
    breaks = scales::trans_breaks("log10", function(x) 10^x),
    labels = scales::trans_format("log10", scales::math_format(10^.x))
  ) +
  scale_fill_viridis(discrete = TRUE, option = "C", direction = -1) +
  theme_minimal(base_size = 14) +
  labs(
    x = "Mecanismo de Cache do Druid",
    y = "Latência de Execução (Milissegundos)",
    fill = "Estado do Broker"
  ) +
  theme(legend.position = "none")

ggsave(filename = paste0(output_dir, "cache_violin_new.png"), plot = p_cache, width = 7, height = 6, dpi = 300)

cat("Gráfico Violino gerado com sucesso em:", output_dir, "\n")
