# Data visualizations for ECLS-K analysis

library(tidyverse)
library(ggpubr)
library(corrplot)
library(scales)

dat <- read_csv("data/ecls_clean.csv", show_col_types = FALSE)
dir.create("results/figures", recursive = TRUE, showWarnings = FALSE)

# Figure 1: Sample sizes by wave
sample_n <- dat %>%
  group_by(wave) %>%
  summarize(
    total = n(),
    has_fs = sum(!is.na(fs_status)),
    has_math = sum(!is.na(math)),
    both = sum(!is.na(fs_status) & !is.na(math))
  )

p1 <- sample_n %>%
  pivot_longer(cols = -wave) %>%
  mutate(name = factor(name, levels = c("total", "has_fs", "has_math", "both"),
                      labels = c("Total", "Food security", "Math", "Both"))) %>%
  ggplot(aes(x = factor(wave), y = value, fill = name)) +
  geom_col(position = position_dodge(), width = 0.7) +
  geom_text(aes(label = comma(value)), position = position_dodge(0.7), vjust = -0.3, size = 3) +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.1))) +
  labs(x = "Wave", y = "N", fill = NULL) +
  theme_classic()

ggsave("results/figures/1_sample_sizes.png", p1, width = 7, height = 4, dpi = 300)

# Figure 2: Food security over time
fs_prev <- dat %>%
  filter(!is.na(fs_status)) %>%
  mutate(fs_cat = factor(fs_status, 1:3, c("Secure", "Low", "Very Low"))) %>%
  count(wave, fs_cat) %>%
  group_by(wave) %>%
  mutate(pct = n/sum(n)*100)

p2 <- ggplot(fs_prev, aes(x = factor(wave), y = pct, fill = fs_cat)) +
  geom_col() +
  geom_text(aes(label = sprintf("%.1f%%", pct)),
            position = position_stack(vjust = 0.5), color = "white") +
  scale_fill_manual(values = c("#2E7D32", "#F57C00", "#C62828")) +
  labs(x = "Wave", y = "Percent", fill = "Food security") +
  theme_classic() +
  theme(legend.position = "bottom")

ggsave("results/figures/2_food_security_prevalence.png", p2, width = 6, height = 4, dpi = 300)

# Figure 3: Math trajectories
set.seed(123)
sample_ids <- dat %>%
  group_by(childid) %>%
  filter(sum(!is.na(math)) == 3) %>%
  slice(1) %>%
  ungroup() %>%
  slice_sample(n = 150) %>%
  pull(childid)

p3a <- dat %>%
  filter(childid %in% sample_ids) %>%
  ggplot(aes(x = time, y = math, group = childid)) +
  geom_line(alpha = 0.2) +
  geom_smooth(aes(group = 1), method = "loess", color = "blue", linewidth = 1.2) +
  scale_x_continuous(breaks = 0:2, labels = c("K", "1st", "5th")) +
  labs(x = "Grade", y = "Math score", title = "Individual trajectories (n=150)") +
  theme_classic()

p3b <- dat %>%
  filter(!is.na(math) & !is.na(fs_status)) %>%
  mutate(fs_cat = factor(fs_status, 1:3, c("Secure", "Low", "Very Low"))) %>%
  group_by(wave, fs_cat) %>%
  summarize(m = mean(math), se = sd(math)/sqrt(n()), .groups = "drop") %>%
  ggplot(aes(x = wave, y = m, color = fs_cat, group = fs_cat)) +
  geom_line(linewidth = 1) +
  geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = m - 1.96*se, ymax = m + 1.96*se), width = 0.2) +
  scale_color_manual(values = c("#2E7D32", "#F57C00", "#C62828")) +
  scale_x_continuous(breaks = c(2, 4, 9), labels = c("K", "1st", "5th")) +
  labs(x = "Grade", y = "Mean math score", color = "Food security") +
  theme_classic() +
  theme(legend.position = "bottom")

p3 <- ggarrange(p3a, p3b, ncol = 2)
ggsave("results/figures/3_math_trajectories.png", p3, width = 10, height = 4, dpi = 300)

# Figure 4: Distributions
p4a <- dat %>%
  filter(wave == 2) %>%
  ggplot(aes(x = x12sesl)) +
  geom_histogram(bins = 40, fill = "steelblue", alpha = 0.7) +
  labs(x = "Baseline SES", y = "Count") +
  theme_classic()

p4b <- dat %>%
  filter(!is.na(math)) %>%
  ggplot(aes(x = math, fill = factor(wave))) +
  geom_density(alpha = 0.5) +
  scale_fill_brewer(palette = "Set1") +
  labs(x = "Math score", y = "Density", fill = "Wave") +
  theme_classic() +
  theme(legend.position = "bottom")

p4c <- dat %>%
  filter(!is.na(fs_scale)) %>%
  ggplot(aes(x = fs_scale, fill = factor(wave))) +
  geom_density(alpha = 0.5) +
  scale_fill_brewer(palette = "Set1") +
  labs(x = "Food insecurity scale", y = "Density", fill = "Wave") +
  theme_classic() +
  theme(legend.position = "bottom")

p4d <- dat %>%
  filter(!is.na(tch_quality) & wave %in% c(2,4)) %>%
  ggplot(aes(x = tch_quality, fill = factor(wave))) +
  geom_density(alpha = 0.5) +
  scale_fill_brewer(palette = "Set1") +
  labs(x = "Teacher relationship", y = "Density", fill = "Wave") +
  theme_classic() +
  theme(legend.position = "bottom")

p4 <- ggarrange(p4a, p4b, p4c, p4d, ncol = 2, nrow = 2)
ggsave("results/figures/4_distributions.png", p4, width = 8, height = 7, dpi = 300)

# Figure 5: Correlations (wave 2 only, numeric vars only)
cor_data <- dat %>%
  filter(wave == 2) %>%
  select(math, science, fs_scale, tch_quality, x12sesl) %>%
  na.omit()

cor_mat <- cor(cor_data)

png("results/figures/5_correlations.png", width = 2000, height = 2000, res = 300)
corrplot(cor_mat, method = "color", type = "upper",
         addCoef.col = "black", number.cex = 0.9,
         tl.col = "black", tl.srt = 45,
         col = colorRampPalette(c("#C62828", "white", "#2E7D32"))(100))
dev.off()

# Figure 6: SES moderation
mod_data <- dat %>%
  filter(!is.na(math) & !is.na(fs_status) & !is.na(ses_q)) %>%
  mutate(
    fs_cat = factor(fs_status, 1:3, c("Secure", "Low", "Very Low")),
    ses_label = factor(ses_q, 1:4, c("Q1 Low", "Q2", "Q3", "Q4 High"))
  )

p6 <- mod_data %>%
  group_by(wave, ses_label, fs_cat) %>%
  summarize(m = mean(math), .groups = "drop") %>%
  ggplot(aes(x = wave, y = m, color = fs_cat, linetype = ses_label,
             group = interaction(fs_cat, ses_label))) +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2) +
  scale_color_manual(values = c("#2E7D32", "#F57C00", "#C62828")) +
  scale_x_continuous(breaks = c(2, 4, 9), labels = c("K", "1st", "5th")) +
  labs(x = "Grade", y = "Mean math score",
       color = "Food security", linetype = "SES") +
  theme_classic() +
  theme(legend.position = "bottom")

ggsave("results/figures/6_ses_moderation.png", p6, width = 8, height = 5, dpi = 300)

# Save summary stats
sink("results/descriptive_stats.txt")
cat("Sample sizes:\n")
print(sample_n)
cat("\n\nFood security prevalence:\n")
print(fs_prev %>% select(wave, fs_cat, n, pct))
cat("\n\nMath scores by wave:\n")
print(dat %>% group_by(wave) %>%
      summarize(n = sum(!is.na(math)),
                mean = mean(math, na.rm=T),
                sd = sd(math, na.rm=T)))
sink()
