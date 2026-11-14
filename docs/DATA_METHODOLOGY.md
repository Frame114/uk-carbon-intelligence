# Data Methodology and Interpretation

## Carbon intensity

The API reports electricity carbon intensity in gCO₂/kWh. It is an indicative estimate of CO₂ associated with electricity in the Great Britain system, not a lifecycle greenhouse-gas score and not a direct measurement at an individual property.

The provider's methodology includes metered power stations, interconnector imports, transmission and distribution losses, electricity demand, and embedded wind and solar. Regional estimates use a reduced GB network model and power-flow calculations to attribute emissions to electricity consumed in each region.

## Forecast and actual

- forecast: provider forecast for the interval.
- actual: provider's estimated actual value; the official website describes it as an estimate from metered generation.
- index: provider classification. Supported labels: very low, low, moderate, high, very high.

Do not merge these fields. Some future intervals will not have an actual value; some historic data may lack forecast. Do not substitute zero for null.

## Generation mix

generationmix[].perc represents a fuel's percentage contribution to the reported mix. It is not a generation quantity or carbon intensity.

Keep these concepts separate:

- Renewable generation: only fuel groups with a defensible renewable classification.
- Low-carbon generation: may include nuclear, but is not synonymous with renewable.
- Imports: preserve as a distinct fuel category; the emission factor can vary by origin.
- Biomass and other: do not silently assume a universal emission factor or renewable classification.

Do not estimate provider carbon intensity using a simple weighted average of fuel share and emission factors: NESO's methodology accounts for demand, imports, network flows, losses and embedded generation.

## Time

Store all intervals as UTC-aware timestamps. The UI can render Europe/London local time. During daylight-saving changes, UTC intervals remain unambiguous while local labels may skip or repeat an hour. Keep the source UTC time available in drill-downs and exports.

## Forecast-based activity windows

Low-intensity windows are comparative opportunities based on the forecast data available at calculation time, not guarantees of savings or advice about the carbon footprint of an entire activity. Include the forecast issue/fetch time and uncertainty caveat where available.

## Source methodology

- https://carbonintensity.org.uk/
- https://github.com/carbon-intensity/methodology
- https://www.neso.energy/data-portal/national-carbon-intensity-forecast/national_carbon_intensity_forecast_methodology
- https://www.neso.energy/data-portal/regional-carbon-intensity-forecast/regional_carbon_intensity_forecast_methodology
