# Growth Convergence Tracker

Does starting out poor in 1990 mean a country grew faster over the next three decades, or did the rich just keep pulling further ahead? I built this to actually check, on real data, instead of repeating whatever answer sounded right.

## Why I built this

This question sits right at the center of growth economics, and I've been curious about it since studying political economy at Oxford, where growth and institutions were never far from the conversation. Robert Solow's 1956 growth model is where the idea starts: because capital runs into diminishing returns, a poor country with little capital should, in theory, grow faster and eventually catch up to a rich one. William Baumol tested that empirically in 1986 and found real convergence, but only among a set of countries that had already succeeded, which turned out to be a selection bias problem (a sample picked because it succeeded will always look like a success story). Robert Barro and Xavier Sala-i-Martin cleaned this up in their 1992 paper "Convergence," coining the terms beta convergence and sigma convergence that are still the standard vocabulary today, and found convergence holds cleanly across U.S. states but only conditionally across countries, once you control for things like education and institutions. Greg Mankiw, David Romer, and David Weil added human capital to Solow's model that same year and got a much better fit to the real cross-country numbers. Then Lant Pritchett came along in 1997 with "Divergence, Big Time" and pointed out that whatever the regressions say, the actual income gap between rich and poor countries got dramatically wider between 1870 and 1990, not narrower.

So depending on which paper you read, the honest answer to "do poor countries catch up" lands somewhere between "yes, conditionally" and "not even close, historically." I wanted to run the simplest version of that test myself, on a fixed and recent window, and see where the data actually lands.

## What it does

I pulled GDP per capita, adjusted for local cost of living so it's a fair comparison across countries, for every country the World Bank has clean data for, in 1990 and again in 2023. For each country I worked out how fast its income grew per year over that span, then ran one regression: growth rate against how rich the country started out in 1990. If poorer countries grew faster on average, that line slopes down. That's the whole test, the same one Barro and Sala-i-Martin ran, done here from scratch on a fixed 33-year window.

## What I found

Across 184 countries, the line does slope down, and it's not just noise. Countries that started poorer in 1990 grew about 0.39 percentage points faster per year for every log-point they started behind, and a result like that would show up by chance less than once in a thousand tries if there were really no relationship at all. So yes, there's real convergence in this window. But look at the R-squared: 0.085. Starting income only explains about 8.5% of why some countries grew faster than others. The trend is real, but income level barely scratches the surface of what actually drives growth.

The country-level stories make that obvious. China and Equatorial Guinea grew at almost the exact same blistering rate, close to 8% a year, for completely different reasons: one built manufacturing capacity, the other exported oil that showed up in per-capita GDP without transforming the country the way it did in China. Meanwhile the three biggest fallers, the UAE, Brunei, and Nauru, were all oil or mineral rich in 1990 and simply saw output per person shrink as reserves and prices moved against them. Convergence on paper can hide very different realities underneath it, which a single coefficient will never show you by itself.

## Robustness checks

The headline regression above treats every country as one data point, Nauru (population about 12,000) and China (population 1.4 billion) each get exactly one vote. That's the honest answer to the question I originally asked, "do poorer countries grow faster," but it's worth checking whether it survives a different, equally reasonable question: "did poorer *people* converge," where big countries count more because more people actually live through what happened there.

So I reran the same regression weighted by each country's 1990 population. The slope goes from -0.0039 to -0.0156, four times steeper, and R-squared jumps from 0.085 to 0.505, meaning starting income now explains about half the variation instead of less than a tenth. Both results are still statistically significant. This isn't a coincidence or a data artifact, it's the well-documented gap between country-level and population-weighted convergence that Xavier Sala-i-Martin wrote about directly in ["The World Distribution of Income: Falling Poverty and...Convergence, Period"](https://academic.oup.com/qje/article-abstract/121/2/351/1883992) (Quarterly Journal of Economics, 2006): once you weight by population, China and India's growth since 1990 does most of the work, because roughly a third of humanity lived in those two countries and both went from poor to middle-income over this exact window.

Neither number is "more correct," they answer different questions. The unweighted regression is the fair test of whether being a poor country predicts faster growth. The weighted one is closer to asking whether the average person alive in 1990 ended up converging toward the average person in a rich country, and by that measure the picture looks a lot more like a convergence success story.

## Data

GDP per capita, PPP-adjusted, from the World Bank's free API, no key needed. 1990 and 2023 specifically, a fixed window rather than an open-ended pull, to keep the comparison clean. 184 countries made the cut; everything else was missing a usable number in one of the two years, mostly small territories plus a handful of countries like Afghanistan and South Sudan where consistent data collection has been genuinely difficult. Each country also carries its 1990 total population, pulled from the same API, used only for the population-weighted robustness check below.

## Structure

```
growth-convergence/
README.md
fetch_data.py        <- pulls GDP per capita from the World Bank API, stdlib only
convergence.py        <- growth rates, the regression (written from scratch, no scipy), the plot
cli.py                 <- menu driven demo
tests.py               <- test suite, including a from-scratch p-value check against t-tables
convergence_plot.png   <- the scatter plot this project produces
data/
    gdp_per_capita_1990_2023.json  <- bundled snapshot for offline use
```

## Run it

```bash
python cli.py
```

From the menu: run the regression and see the headline result, browse the fastest- and slowest-growing countries, save the scatter plot, refresh the dataset live from the World Bank (needs internet), or run the population-weighted robustness check.

```bash
python -m unittest tests.py -v
```

## Limitations

This measures correlation, not causation, and it deliberately leaves out everything Barro's later work found mattered, education, institutions, investment rates, so it's the raw, unconditional version of convergence, not the fuller "conditional convergence" story. Using only two endpoint years means a single bad or unusually good year right at 1990 or 2023 can distort a country's whole growth number. And PPP conversion factors get revised by statistical agencies over time, so today's "1990 dollars" aren't quite the same figure that would have been reported back in 1990. None of this is a forecast or a policy recommendation, it's a starting point for the question, not the final word on it.
