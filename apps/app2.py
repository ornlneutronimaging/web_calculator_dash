import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import numpy as np
import pandas as pd
from ImagingReso._utilities import ev_to_angstroms
from ImagingReso._utilities import ev_to_s
from dash.dependencies import Input, Output, State

from _utilities import init_reso_from_tb, unpack_sample_tb_df_and_add_layer, \
    add_del_tb_rows, form_stack_table, plot_option_div, calculate_transmission_cg1d
from app import app

energy_name = 'Energy (eV)'
wave_name = 'Wavelength (\u212B)'
tof_name = 'Time-of-flight (\u03BCs)'
chem_name = 'Chemical formula'
thick_name = 'Thickness (mm)'
density_name = 'Density (g/cm\u00B3)'
ele_name = 'Element'

df_range = pd.DataFrame({
    energy_name: [1, 100],
    wave_name: [np.NaN, np.NaN],
    tof_name: [np.NaN, np.NaN],
})

df_sample = pd.DataFrame({
    chem_name: ['Ag'],
    thick_name: ['1'],
    density_name: [''],
})

col_3 = 'three columns'
col_6 = 'six columns'

# Create app2 layout
layout = html.Div(
    [
        dcc.Link('Home', href='/'),
        html.Br(),
        dcc.Link('Cold neutron transmission', href='/apps/cg1d'),
        html.H1('Neutron resonance'),
        # Global parameters
        html.Div(
            [
                # Range input
                html.H6('Energy range:'),
                html.Div(
                    [
                        # Energy slider
                        dcc.RangeSlider(
                            id='e_range_slider',
                            min=-5,
                            max=6,
                            value=[0, 2],
                            allowCross=False,
                            dots=False,
                            step=0.01,
                            updatemode='drag',
                            marks={i: '{} eV'.format(pow(10, i)) for i in range(-5, 7, 1)},
                            className='ten columns offset-by-one',
                        ),
                    ], className='row'
                ),
                html.Br(),
                # html.H6('Range selected:'),
                html.Div([
                    dt.DataTable(
                        rows=df_range.to_dict('records'),
                        # optional - sets the order of columns
                        columns=[energy_name, wave_name, tof_name],
                        # sortColumn=False,
                        editable=False,
                        row_selectable=False,
                        filterable=False,
                        sortable=True,
                        id='range_table'
                    ),
                ]),
                html.Div(
                    [
                        # Step input
                        html.Div(
                            [
                                html.H6('Energy step:'),
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id='e_step',
                                            options=[
                                                {'label': '0.001 (eV)', 'value': 0.001},
                                                {'label': '0.01 (eV)', 'value': 0.01},
                                                {'label': '0.1 (eV)', 'value': 0.1},
                                                {'label': '1 (eV)', 'value': 1},
                                                {'label': '10 (eV)', 'value': 10},
                                                {'label': '100 (eV)', 'value': 100},
                                            ],
                                            value=0.01,
                                            searchable=False,
                                            clearable=False,
                                        ),
                                    ]
                                ),
                                dcc.Markdown(
                                    '''NOTE: Pick a suitable energy step base on the energy range selected.'''),
                            ], className='five columns',
                        ),
                        html.Div(
                            [
                                html.H6('Source-to-detector (optional):'),
                                html.Div(
                                    [
                                        dcc.Input(id='distance', type='number', value=16.45, min=1,
                                                  inputmode='numeric',
                                                  step=0.01,
                                                  className='nine columns'),
                                        html.P('(m)', className='one column',
                                               style={'marginBottom': 10, 'marginTop': 5}),
                                    ], className='row'
                                ),
                                dcc.Markdown(
                                    '''NOTE: Please ignore the above input field if **NOT** 
                                    interested in display of time-of-flight (TOF).'''),
                            ], className='seven columns',
                        ),
                    ], className='row',
                ),
            ]
        ),

        # Sample input
        html.H3('Sample info'),
        html.Div([
            html.Div(
                [
                    html.Button('+', id='button_add'),
                    html.Button('-', id='button_del'),
                ], className='row'
            ),

            dt.DataTable(
                rows=df_sample.to_dict('records'),
                # optional - sets the order of columns
                columns=[chem_name, thick_name, density_name],
                editable=True,
                row_selectable=False,
                filterable=False,
                sortable=False,
                id='sample_table'
            ),
            dcc.Markdown(
                '''NOTE: density input can be omitted (leave as blank) only if the input formula is single element,
                 density available [here](http://periodictable.com/Properties/A/Density.al.html) will be used.'''),
            html.Button('Submit', id='button_submit'),
        ]
        ),

        # Plot
        html.Div(id='plot_options'),
        html.Div(id='plot'),

        # Stack display
        html.Div(
            [
                # Transmission at CG-1D
                html.Div(id='result'),
                # Sample stack
                html.Div(id='stack'),
            ],
        ),
    ]
)


@app.callback(
    Output('range_table', 'rows'),
    [
        Input('e_range_slider', 'value'),
        Input('distance', 'value'),
    ])
def show_range_table(slider, distance):
    transformed_value = [pow(10, v) for v in slider]
    e_min = round(transformed_value[0], 5)
    e_max = round(transformed_value[1], 5)
    lambda_1 = round(ev_to_angstroms(array=e_min), 4)
    lambda_2 = round(ev_to_angstroms(array=e_max), 4)
    tof_1 = round(ev_to_s(array=e_min, source_to_detector_m=distance, offset_us=0) * 1e6, 4)
    tof_2 = round(ev_to_s(array=e_max, source_to_detector_m=distance, offset_us=0) * 1e6, 4)
    _df_range = pd.DataFrame({
        energy_name: [e_min, e_max],
        wave_name: [lambda_1, lambda_2],
        tof_name: [tof_1, tof_2],
    })
    return _df_range.to_dict('records')


@app.callback(
    Output('sample_table', 'rows'),
    [
        Input('button_add', 'n_clicks'),
        Input('button_del', 'n_clicks'),
    ],
    [
        State('sample_table', 'rows'),
    ])
def add_del_row(n_add, n_del, sample_tb_rows):
    _df_sample = add_del_tb_rows(n_add, n_del, sample_tb_rows)
    return _df_sample.to_dict('records')


@app.callback(
    Output('plot_scale', 'options'),
    [
        Input('y_type', 'value'),
    ])
def enable_logx_when_not_plot_sigma(y_type):
    if y_type == 'sigma':
        options = [
            {'label': 'Linear', 'value': 'linear'},
            {'label': 'Log x', 'value': 'logx'},
            {'label': 'Log y', 'value': 'logy'},
            {'label': 'Loglog', 'value': 'loglog'},
        ]
    else:
        options = [
            {'label': 'Linear', 'value': 'linear'},
            {'label': 'Log x', 'value': 'logx'},
        ]
    return options


@app.callback(
    Output('plot_options', 'children'),
    [
        Input('button_submit', 'n_clicks'),
    ])
def show_plot_options(n_submit):
    if n_submit is not None:
        return plot_option_div
    else:
        return html.Div(plot_option_div, style={'display': 'none'})


@app.callback(
    Output('plot', 'children'),
    [
        Input('button_submit', 'n_clicks'),
        Input('y_type', 'value'),
        Input('x_type', 'value'),
        Input('plot_scale', 'value'),
        Input('show_opt', 'values'),
    ],
    [
        State('range_table', 'rows'),
        State('e_step', 'value'),
        State('distance', 'value'),
        State('sample_table', 'rows'),
    ])
def plot(n_submit, y_type, x_type, plot_scale, show_opt,
         range_tb_rows, e_step, distance_m,
         sample_tb_rows,
         ):
    if n_submit is not None:
        o_reso = init_reso_from_tb(range_tb_rows, e_step)
        df_sample_tb = pd.DataFrame(sample_tb_rows)
        o_reso = unpack_sample_tb_df_and_add_layer(o_reso=o_reso,
                                                   sample_tb_df=df_sample_tb)
        if plot_scale == 'logx':
            _log_x = True
            _log_y = False
        elif plot_scale == 'logy':
            _log_x = False
            _log_y = True
        elif plot_scale == 'loglog':
            _log_x = True
            _log_y = True
        else:
            _log_x = False
            _log_y = False
        show_total = False
        show_layer = False
        show_ele = False
        show_iso = False
        if 'total' in show_opt:
            show_total = True
        if 'layer' in show_opt:
            show_layer = True
        if 'ele' in show_opt:
            show_ele = True
        if 'iso' in show_opt:
            show_iso = True
        plotly_fig = o_reso.plot(plotly=True,
                                 y_axis=y_type,
                                 x_axis=x_type,
                                 time_unit='us',
                                 logy=_log_y,
                                 logx=_log_x,
                                 mixed=show_total,
                                 all_layers=show_layer,
                                 all_elements=show_ele,
                                 all_isotopes=show_iso,
                                 source_to_detector_m=distance_m)
        plotly_fig.layout.showlegend = True
        return html.Div(
            [
                dcc.Graph(id='reso_plot', figure=plotly_fig),
                html.Div([
                    html.Button('Export plot data to clipboard', id='button_export'),
                    html.Div(id='export_done'),
                ], className='row'),
            ]
        )


@app.callback(
    Output('export_done', 'children'),
    [
        Input('button_export', 'n_clicks'),
    ],
    [
        State('y_type', 'value'),
        State('x_type', 'value'),
        State('show_opt', 'values'),
        State('range_table', 'rows'),
        State('e_step', 'value'),
        State('distance', 'value'),
        State('sample_table', 'rows'),
    ])
def export(n_export_to_clipboard,
           y_type, x_type, show_opt,
           range_tb_rows, e_step, distance_m,
           sample_tb_rows
           ):
    o_reso = init_reso_from_tb(range_tb_rows, e_step)
    df_sample_tb = pd.DataFrame(sample_tb_rows)
    o_reso = unpack_sample_tb_df_and_add_layer(o_reso=o_reso,
                                               sample_tb_df=df_sample_tb)
    show_total = False
    show_layer = False
    show_ele = False
    show_iso = False
    if 'total' in show_opt:
        show_total = True
    if 'layer' in show_opt:
        show_layer = True
    if 'ele' in show_opt:
        show_ele = True
    if 'iso' in show_opt:
        show_iso = True

    if n_export_to_clipboard is not None:
        o_reso.export(y_axis=y_type,
                      x_axis=x_type,
                      time_unit='us',
                      mixed=show_total,
                      all_layers=show_layer,
                      all_elements=show_ele,
                      all_isotopes=show_iso,
                      source_to_detector_m=distance_m)
        if n_export_to_clipboard == 1:
            return html.P('Data copied {} time.'.format(n_export_to_clipboard),
                          style={'marginBottom': 10, 'marginTop': 5})
        else:
            return html.P('Data copied {} times.'.format(n_export_to_clipboard),
                          style={'marginBottom': 10, 'marginTop': 5})


@app.callback(
    Output('result', 'children'),
    [
        Input('button_submit', 'n_clicks'),
    ],
    [
        State('y_type', 'value'),
        State('sample_table', 'rows'),
    ])
def calculate_transmission(n_clicks, y_type, sample_tb_rows):
    total_trans = calculate_transmission_cg1d(sample_tb_rows)
    if n_clicks is not None:
        if y_type == 'transmission':
            return html.Div(
                [
                    html.H5('Sample transmission:'),
                    html.P('The total neutron transmission at CG-1D (ORNL): {} %'.format(total_trans)),
                ])
        else:
            return html.Div(
                [
                    html.H5('Sample attenuation:'),
                    html.P('The total neutron attenuation at CG-1D (ORNL): {} %'.format(100 - total_trans)),
                ])


@app.callback(
    Output('stack', 'children'),
    [
        Input('button_submit', 'n_clicks'),
    ],
    [
        State('sample_table', 'rows'),
    ])
def show_stack(n_clicks, sample_tb_rows):
    if n_clicks is not None:
        div_list = form_stack_table(sample_tb_rows)
        return html.Div([html.H5('Sample stack:'), html.Div(div_list)])
