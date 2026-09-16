Creator Performance & Partner Support Analysis
================
Marlon Nurse

## Overview

This project examines synthetic creator performance and support data for
2025. The goal is to compare activity, growth, and support operations
across regions, categories, and partner tiers. The analysis is
descriptive and does not establish cause and effect.

``` r
library(dplyr)
library(ggplot2)

creators <- read.csv("https://raw.githubusercontent.com/mj-nurse/creator-performance-partner-support/refs/heads/main/data/raw/creators.csv")
performance <- read.csv("https://raw.githubusercontent.com/mj-nurse/creator-performance-partner-support/refs/heads/main/data/raw/monthly_performance.csv")
support_cases <- read.csv("https://raw.githubusercontent.com/mj-nurse/creator-performance-partner-support/refs/heads/main/data/raw/support_cases.csv")
```

## Data checks

``` r
nrow(creators)
```

    ## [1] 750

``` r
nrow(performance)
```

    ## [1] 9000

``` r
nrow(support_cases)
```

    ## [1] 2076

``` r
sum(duplicated(creators$creator_id))
```

    ## [1] 0

``` r
sum(duplicated(support_cases$case_id))
```

    ## [1] 0

``` r
sum(is.na(performance$views))
```

    ## [1] 0

## Monthly activity

``` r
monthly_summary <- performance %>%
  group_by(performance_month) %>%
  summarise(
    active_creators = sum(uploads > 0),
    total_uploads = sum(uploads),
    total_views = sum(views),
    new_subscribers = sum(new_subscribers)
  )

monthly_summary
```

    ## # A tibble: 12 × 5
    ##    performance_month active_creators total_uploads total_views new_subscribers
    ##    <chr>                       <int>         <int>       <int>           <int>
    ##  1 2025-01                       661          3497    58046480          561038
    ##  2 2025-02                       647          3390    59122299          566367
    ##  3 2025-03                       651          3397    57918098          546917
    ##  4 2025-04                       653          3482    61445900          579994
    ##  5 2025-05                       656          3432    60445260          566995
    ##  6 2025-06                       653          3430    63778911          617063
    ##  7 2025-07                       643          3357    64288337          622647
    ##  8 2025-08                       668          3517    65072897          634466
    ##  9 2025-09                       654          3503    66191067          611983
    ## 10 2025-10                       662          3551    68218614          654470
    ## 11 2025-11                       659          3456    67997165          660904
    ## 12 2025-12                       652          3345    68909063          651970

``` r
ggplot(monthly_summary, aes(x = performance_month, y = active_creators, group = 1)) +
  geom_line(color = "#3367D6") +
  geom_point(color = "#3367D6") +
  labs(
    title = "Monthly Active Creators",
    subtitle = "Synthetic creator data, January-December 2025",
    x = "Month",
    y = "Active creators"
  ) +
  theme_minimal()
```

![](creator_support_analysis_files/figure-gfm/monthly-chart-1.png)<!-- -->

## Performance by partner tier

``` r
performance_by_tier <- performance %>%
  left_join(creators, by = "creator_id") %>%
  group_by(partner_tier) %>%
  summarise(
    creators = n_distinct(creator_id),
    avg_monthly_uploads = mean(uploads),
    avg_monthly_views = mean(views),
    avg_monthly_subscribers = mean(new_subscribers)
  ) %>%
  arrange(desc(avg_monthly_views))

performance_by_tier
```

    ## # A tibble: 3 × 5
    ##   partner_tier creators avg_monthly_uploads avg_monthly_views avg_monthly_subscribers
    ##   <chr>           <int>               <dbl>             <dbl>                   <dbl>
    ## 1 Established       108                8.17           313951.                   3008.
    ## 2 Growth            235                5.50            94469.                    902.
    ## 3 Emerging          407                3.12            18049.                    171.

``` r
ggplot(performance_by_tier, aes(x = reorder(partner_tier, avg_monthly_views), y = avg_monthly_views)) +
  geom_col(fill = "#3367D6") +
  labs(
    title = "Average Monthly Views by Partner Tier",
    subtitle = "Synthetic creator data, 2025",
    x = "Partner tier",
    y = "Average monthly views"
  ) +
  theme_minimal()
```

![](creator_support_analysis_files/figure-gfm/tier-chart-1.png)<!-- -->

## Support operations

``` r
support_summary <- support_cases %>%
  filter(case_status == "Closed") %>%
  group_by(case_type) %>%
  summarise(
    cases = n(),
    avg_resolution_hours = mean(resolution_hours),
    first_contact_resolution_rate = mean(first_contact_resolved),
    avg_satisfaction = mean(satisfaction_score)
  ) %>%
  arrange(desc(cases))

support_summary
```

    ## # A tibble: 5 × 5
    ##   case_type          cases avg_resolution_hours first_contact_resolution_rate avg_satisfaction
    ##   <chr>              <int>                <dbl>                         <dbl>            <dbl>
    ## 1 Technical Issue      498                13.1                          0.673             4.27
    ## 2 Monetization         488                15.4                          0.676             4.17
    ## 3 Policy Question      399                14.9                          0.707             4.18
    ## 4 Analytics Question   284                 9.52                         0.623             4.48
    ## 5 Account Access       278                11.6                          0.691             4.34

``` r
ggplot(support_summary, aes(x = reorder(case_type, avg_resolution_hours), y = avg_resolution_hours)) +
  geom_col(fill = "#3367D6") +
  coord_flip() +
  labs(
    title = "Average Resolution Time by Support Case Type",
    subtitle = "Closed synthetic support cases from 2025",
    x = "Case type",
    y = "Average resolution hours"
  ) +
  theme_minimal()
```

![](creator_support_analysis_files/figure-gfm/support-chart-1.png)<!-- -->

## Interpretation

The analysis should be used to identify segments for further
investigation. Differences between partner tiers or regions may reflect
creator size, category mix, tenure, or other factors. They should not be
interpreted as evidence that support activity caused creator growth or
decline.
