# Clean data and create derived variables for GEE analysis

library(tidyverse)

# Load data
dat <- read_csv("data/ecls_long.csv", show_col_types = FALSE)

# Recode ECLS-K missing codes to NA
recode_missing <- function(x) {
  if (is.numeric(x)) {
    x[x < 0] <- NA
  }
  return(x)
}

dat <- dat %>% mutate(across(where(is.numeric), recode_missing))

# Create derived variables
dat <- dat %>%
  group_by(childid) %>%
  arrange(wave) %>%
  mutate(
    # Time variable for GEE
    time = case_when(wave == 2 ~ 0, wave == 4 ~ 1, wave == 9 ~ 2),

    # Food security baseline and change
    fs_baseline = first(fs_scale[!is.na(fs_scale)]),
    fs_change = fs_scale - fs_baseline,
    fs_cumulative = cumsum(!is.na(fs_status) & fs_status >= 2),

    # Teacher relationship quality
    tch_quality = tch_close - tch_conflict,

    # SES quartiles for moderation analysis
    ses_q = ntile(x12sesl, 4)
  ) %>%
  ungroup()

# Save cleaned data
write_csv(dat, "data/ecls_clean.csv")
cat("Cleaned data saved to data/ecls_clean.csv\n")
cat(sprintf("  %s observations, %s children\n",
            format(nrow(dat), big.mark=","),
            format(n_distinct(dat$childid), big.mark=",")))
