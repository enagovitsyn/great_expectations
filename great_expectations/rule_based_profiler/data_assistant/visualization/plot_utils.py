from typing import Dict, List, Optional

import altair as alt
import pandas as pd

from great_expectations.rule_based_profiler.types import (
    ALTAIR_DEFAULT_CONFIGURATION,
    FULLY_QUALIFIED_PARAMETER_NAME_ATTRIBUTED_VALUE_KEY,
    FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY,
    Domain,
    ParameterNode,
)
from great_expectations.types import ColorPalettes, Colors


def get_attributed_metrics_by_domain(
    metrics_by_domain: Dict[Domain, Dict[str, ParameterNode]]
) -> Dict[Domain, Dict[str, ParameterNode]]:
    doain: Domain
    parameter_values_for_fully_qualified_parameter_names: Dict[str, ParameterNode]
    fully_qualified_parameter_name: str
    parameter_value: ParameterNode
    metrics_attributed_values_by_domain: Dict[Domain, Dict[str, ParameterNode]] = {
        domain: {
            parameter_value[
                FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY
            ].metric_configuration.metric_name: parameter_value[
                FULLY_QUALIFIED_PARAMETER_NAME_ATTRIBUTED_VALUE_KEY
            ]
            for fully_qualified_parameter_name, parameter_value in parameter_values_for_fully_qualified_parameter_names.items()
        }
        for domain, parameter_values_for_fully_qualified_parameter_names in metrics_by_domain.items()
    }
    return metrics_attributed_values_by_domain


def get_expect_domain_values_to_be_between_chart(
    df: pd.DataFrame,
    metric: str,
    metric_type: str,
    x_axis_name: str,
    x_axis_type: str,
) -> alt.Chart:
    opacity: float = 0.9
    line_color: alt.HexColor = alt.HexColor(ColorPalettes.HEATMAP.value[4])
    fill_color: alt.HexColor = alt.HexColor(ColorPalettes.HEATMAP.value[5])

    metric_title: str = metric.replace("_", " ").title()
    x_axis_title: str = x_axis_name.title()

    batch_id: str = "batch_id"
    batch_id_type: str = "nominal"
    min_value: str = "min_value"
    min_value_type: str = "quantitative"
    max_value: str = "max_value"
    max_value_type: str = "quantitative"

    tooltip: list[alt.Tooltip] = [
        alt.Tooltip(field=batch_id, type=batch_id_type),
        alt.Tooltip(field=metric, type=metric_type, format=","),
        alt.Tooltip(field=min_value, type=min_value_type, format=","),
        alt.Tooltip(field=max_value, type=max_value_type, format=","),
    ]

    lower_limit: alt.Chart = (
        alt.Chart(data=df)
        .mark_line(color=line_color, opacity=opacity)
        .encode(
            x=alt.X(
                x_axis_name,
                type=x_axis_type,
                title=x_axis_title,
            ),
            y=alt.Y(min_value, type=metric_type, title=metric_title),
            tooltip=tooltip,
        )
    )

    upper_limit: alt.Chart = (
        alt.Chart(data=df)
        .mark_line(color=line_color, opacity=opacity)
        .encode(
            x=alt.X(
                x_axis_name,
                type=x_axis_type,
                title=x_axis_title,
            ),
            y=alt.Y(max_value, type=metric_type, title=metric_title),
            tooltip=tooltip,
        )
    )

    band: alt.Chart = (
        alt.Chart(data=df)
        .mark_area(fill=fill_color, fillOpacity=opacity)
        .encode(
            x=alt.X(
                x_axis_name,
                type=x_axis_type,
                title=x_axis_title,
            ),
            y=alt.Y(min_value, title=metric_title, type=metric_type),
            y2=alt.Y2(max_value, title=metric_title),
        )
    )

    predicate = (
        (alt.datum.min_value > alt.datum.table_row_count)
        & (alt.datum.max_value > alt.datum.table_row_count)
    ) | (
        (alt.datum.min_value < alt.datum.table_row_count)
        & (alt.datum.max_value < alt.datum.table_row_count)
    )
    point_color_condition: alt.condition = alt.condition(
        predicate=predicate,
        if_false=alt.value(Colors.GREEN.value),
        if_true=alt.value(Colors.PINK.value),
    )
    anomaly_coded_line: alt.Chart = get_line_chart(
        df=df,
        metric=metric,
        metric_type=metric_type,
        x_axis_name=x_axis_name,
        x_axis_type=x_axis_type,
        point_color_condition=point_color_condition,
        tooltip=tooltip,
    )

    return band + lower_limit + upper_limit + anomaly_coded_line


def get_line_chart(
    df: pd.DataFrame,
    metric: str,
    metric_type: str,
    x_axis_name: str,
    x_axis_type: str,
    line_color: Optional[str] = Colors.BLUE_2.value,
    point_color: Optional[str] = Colors.GREEN.value,
    point_color_condition: Optional[alt.condition] = None,
    tooltip: Optional[List[alt.Tooltip]] = None,
) -> alt.Chart:
    metric_title: str = metric.replace("_", " ").title()
    x_axis_title: str = x_axis_name.title()
    title: str = f"{metric_title} by {x_axis_title}"

    batch_id: str = "batch_id"
    batch_id_type: str = "nominal"

    if tooltip is None:
        tooltip: List[alt.Tooltip] = [
            alt.Tooltip(field=batch_id, type=batch_id_type),
            alt.Tooltip(field=metric, type=metric_type, format=","),
        ]

    line: alt.Chart = (
        alt.Chart(data=df, title=title)
        .mark_line(color=line_color)
        .encode(
            x=alt.X(
                x_axis_name,
                type=x_axis_type,
                title=x_axis_title,
            ),
            y=alt.Y(metric, type=metric_type, title=metric_title),
            tooltip=tooltip,
        )
    )

    if point_color_condition is not None:
        points: alt.Chart = (
            alt.Chart(data=df, title=title)
            .mark_point(opacity=1.0)
            .encode(
                x=alt.X(
                    x_axis_name,
                    type=x_axis_type,
                    title=x_axis_title,
                ),
                y=alt.Y(metric, type=metric_type, title=metric_title),
                stroke=point_color_condition,
                fill=point_color_condition,
                tooltip=tooltip,
            )
        )
    else:
        points: alt.Chart = (
            alt.Chart(data=df, title=title)
            .mark_point(stroke=point_color, fill=point_color, opacity=1.0)
            .encode(
                x=alt.X(
                    x_axis_name,
                    type=x_axis_type,
                    title=x_axis_title,
                ),
                y=alt.Y(metric, type=metric_type, title=metric_title),
                tooltip=tooltip,
            )
        )

    return line + points


def display(charts: List[alt.Chart]) -> None:
    """
    Display each chart passed in Jupyter Notebook
    """
    chart: alt.Chart
    for chart in charts:
        chart.configure(**ALTAIR_DEFAULT_CONFIGURATION).display()