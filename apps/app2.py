from dash.dependencies import Input, Output, State
from _app import app
import json
import plotly.tools as tls
from _utilities import *

energy_range_df_default = pd.DataFrame({
    'column_1': [1, 100],
    'column_2': [0.28598, 0.0286],
    'column_3': [13832.93, 138329.29],
    'column_4': [1189.1914, 118.9191],
    'column_5': ['Epithermal', 'Epithermal'],
})

sample_df_default = pd.DataFrame({
    'column_1': ['Ag'],
    'column_2': ['1'],
    'column_3': [''],
})

plot_data_filename = "plot_data.csv"

app_name = 'app2'
slider_id = app_name + '_e_range_slider'
range_table_id = app_name + '_range_table'
e_step_id = app_name + '_e_step'
distance_id = app_name + '_distance'
add_row_id = app_name + '_add_row'
del_row_id = app_name + '_del_row'
sample_table_id = app_name + '_sample_table'
iso_check_id = app_name + '_iso_check'
iso_div_id = app_name + '_iso_input'
iso_table_id = app_name + '_iso_table'
submit_button_id = app_name + '_submit'
error_id = app_name + '_error'
output_id = app_name + '_output'
result_id = app_name + '_result'
hidden_range_tb_id = app_name + '_hidden_range_table'
hidden_range_input_type_id = app_name + '_hidden_range_input_type'
hidden_df_json_id = app_name + '_hidden_df_json'
plot_id = app_name + '_plot'
plot_options_div_id = app_name + '_plot_options'

# Create app2 layout
layout = html.Div(
    [
        dcc.Link('Home', href='/'),
        html.Br(),
        dcc.Link('Cold neutron transmission', href='/apps/cg1d'),
        html.Br(),
        dcc.Link('Composition converter', href='/apps/converter'),
        html.H1('Neutron resonance'),
        # Global parameters
        html.Div(
            [
                # Range input
                html.H6('Energy range:'),
                html.Div([
                    dt.DataTable(
                        data=energy_range_df_default.to_dict('records'),
                        # optional - sets the order of columns
                        columns=energy_range_header_df.to_dict('records'),
                        editable=True,
                        row_selectable=False,
                        filtering=False,
                        sorting=False,
                        row_deletable=False,
                        style_cell_conditional=even_5_col,
                        style_data_conditional=gray_range_cols,
                        id=range_table_id
                    ),
                ]),
                dcc.Markdown('''NOTE: '**Energy (eV)**' and '**Wavelength (\u212B)**' are editable.'''),

                # Hidden div to store previous range table
                html.Div(id=hidden_range_tb_id, style={'display': 'none'}),
                # Hidden div to store range input type
                html.Div(id=hidden_range_input_type_id, children='energy', style={'display': 'none'}),

                # Step/distance input
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6('Energy step:'),
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id=e_step_id,
                                            options=[
                                                {'label': '0.001 (eV)  (NOT recommended if energy range > 10 eV)',
                                                 'value': 0.001},
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
                            ], className='five columns', style={'verticalAlign': 'middle'},
                        ),
                        html.Div(
                            [
                                html.H6('Source-to-detector (optional):'),
                                html.Div(
                                    [
                                        dcc.Input(id=distance_id, type='number', value=16.45, min=1,
                                                  inputmode='numeric',
                                                  step=0.01,
                                                  className='nine columns'),
                                        html.P('(m)', className='one column',
                                               style={'marginBottom': 10, 'marginTop': 5},
                                               # style={'verticalAlign': 'middle'},
                                               ),
                                    ], className='row', style={'verticalAlign': 'middle'},
                                ),
                                dcc.Markdown(
                                    '''NOTE: Please ignore the above input field if you are **NOT** 
                                    interested in displaying results in time-of-flight (TOF).'''),
                            ], className=col_width_6,
                        ),
                    ], className='row',
                ),
            ]
        ),

        # Sample input
        html.H3('Sample info'),
        html.Div(
            [
                html.Button('+', id=add_row_id, n_clicks_timestamp=0),
                html.Button('-', id=del_row_id, n_clicks_timestamp=0),
                dt.DataTable(
                    data=sample_df_default.to_dict('records'),
                    # optional - sets the order of columns
                    columns=sample_header_df.to_dict('records'),
                    editable=True,
                    row_selectable=False,
                    filtering=False,
                    sorting=False,
                    row_deletable=True,
                    style_cell_conditional=even_3_col,
                    id=sample_table_id
                ),
                markdown_sample,
                # Input table for isotopic ratios
                dcc.Checklist(id=iso_check_id,
                              options=[
                                  {'label': 'Modify isotopic ratios', 'value': True},
                              ], values=[],
                              ),
                html.Div(
                    [
                        markdown_iso,
                        init_iso_table(id_str=iso_table_id)
                    ],
                    id=iso_div_id,
                    style={'display': 'none'},
                ),
                html.Button('Submit', id=submit_button_id),
            ]
        ),

        # Error message
        html.Div(id=error_id, children=None),

        # Hidden div to store stack
        html.Div(id=hidden_df_json_id, style={'display': 'none'}),

        # Output div
        html.Div(
            [
                # Plot options
                html.Div(id=plot_options_div_id, children=plot_option_div),

                # html.Div(
                #     [
                #         dcc.Checklist(id='app2_export_clip',
                #                       options=[
                #                           {'label': 'Clipboard', 'value': False},
                #                       ], values=[],
                #                       ),
                #         # html.A(
                #         #     'Download Plot Data',
                #         #     id='app2_download_link',
                #         #     download=plot_data_filename,
                #         #     href="",
                #         #     target="_blank",
                #         #     style={'display': 'inline-block'},
                #         # ),
                #     ], className='row'
                # ),

                # Plot
                html.Div(id=plot_id, className='container'),
                # html.Div([dcc.Graph(id=plot_id)],
                #          className='container'),

                # Transmission at CG-1D and sample stack
                html.Div(id=result_id),
            ],
            id=output_id,
            style={'display': 'none'},
        ),
    ]
)


@app.callback(
    Output(hidden_range_input_type_id, 'children'),
    [
        Input(range_table_id, 'data_timestamp'),
    ],
    [
        State(range_table_id, 'data'),
        State(hidden_range_tb_id, 'children'),
    ])
def update_range_input_type(timestamp, new_range_tb_rows, old_range_tb_json):
    old_range_tb_df = pd.read_json(old_range_tb_json, orient='split')
    diff_indices = pd.DataFrame(new_range_tb_rows) == old_range_tb_df
    _cord = np.where(diff_indices == False)
    modified_cord = (_cord[0][0], _cord[1][0])
    print(modified_cord)
    if not all(diff_indices[column_2] == True):
        return 'lambda'
    else:
        return 'energy'


@app.callback(
    Output(range_table_id, 'data'),
    [
        Input(range_table_id, 'data_timestamp'),
        Input(distance_id, 'value'),
        Input(hidden_range_input_type_id, 'children'),
    ],
    [
        State(range_table_id, 'data'),
    ])
def form_range_table(timestamp, distance, range_input_type, range_table_rows):
    if range_input_type == 'energy':
        df_range = update_range_tb_by_energy(range_table_rows=range_table_rows, distance=distance)
    else:
        df_range = update_range_tb_by_lambda(range_table_rows=range_table_rows, distance=distance)
    return df_range.to_dict('records')


@app.callback(
    Output(hidden_range_tb_id, 'children'),
    # Output(hidden_range_tb_id, 'data'),
    [
        Input(range_table_id, 'data_timestamp'),
        Input(distance_id, 'value'),
        Input(hidden_range_input_type_id, 'children'),
    ],
    [
        State(range_table_id, 'data'),
    ])
def store_prev_range_table_in_json(timestamp, distance, range_input_type, range_table_rows):
    if range_input_type == 'energy':
        df_range = update_range_tb_by_energy(range_table_rows=range_table_rows, distance=distance)
    else:
        df_range = update_range_tb_by_lambda(range_table_rows=range_table_rows, distance=distance)
    return df_range.to_json(date_format='iso', orient='split')


@app.callback(
    Output(sample_table_id, 'data'),
    [
        Input(add_row_id, 'n_clicks_timestamp'),
        Input(del_row_id, 'n_clicks_timestamp')
    ],
    [
        State(sample_table_id, 'data'),
        State(sample_table_id, 'columns')
    ])
def update_rows(n_add, n_del, rows, columns):
    if n_add > n_del:
        rows.append({c['id']: '' for c in columns})
    elif n_add < n_del:
        rows = rows[:-1]
    else:
        rows = rows
    return rows


@app.callback(
    Output(iso_table_id, 'data'),
    [
        Input(sample_table_id, 'data'),
    ],
    [
        State(iso_table_id, 'data'),
    ])
def update_iso_table(compos_tb_dict, prev_iso_tb_dict):
    compos_tb_df = pd.DataFrame(compos_tb_dict)
    prev_iso_tb_df = pd.DataFrame(prev_iso_tb_dict)
    sample_df = creat_sample_df_from_compos_df(compos_tb_df=compos_tb_df)
    new_iso_df = form_iso_table(sample_df=sample_df)

    new_iso_df = update_new_iso_table(prev_iso_df=prev_iso_tb_df, new_iso_df=new_iso_df)
    return new_iso_df.to_dict('records')


@app.callback(
    Output(iso_div_id, 'style'),
    [
        Input(iso_check_id, 'values'),
    ])
def show_hide_iso_table(iso_changed):
    if iso_changed:
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    Output('plot_scale', 'value'),
    [
        Input('y_type', 'value'),
    ],
    [
        State('plot_scale', 'value'),
    ])
def enable_logx_when_not_plot_sigma(y_type, prev_value):
    if y_type[:5] == 'sigma':
        if prev_value in ['logy', 'loglog']:
            return prev_value
        else:
            return 'logy'
    else:
        return prev_value


@app.callback(
    Output('show_opt', 'options'),
    [
        Input('y_type', 'value'),
    ])
def disable_total_layer_when_plotting_sigma(y_type):
    if y_type[:5] != 'sigma':
        options = [
            {'label': 'Total', 'value': 'total'},
            {'label': 'Layer', 'value': 'layer'},
            {'label': 'Element', 'value': 'ele'},
            {'label': 'Isotope', 'value': 'iso'},
        ]
    else:
        if y_type[-3:] == 'raw':
            options = [
                {'label': 'Isotope', 'value': 'iso'},
            ]
        else:
            options = [
                {'label': 'Element', 'value': 'ele'},
                {'label': 'Isotope', 'value': 'iso'},
            ]
    return options


@app.callback(
    Output(output_id, 'style'),
    [
        Input(submit_button_id, 'n_clicks'),
        Input(error_id, 'children'),
    ])
def show_output_div(n_submit, test_passed):
    if n_submit is not None:
        if test_passed is True:
            return {'display': 'block'}
        else:
            return {'display': 'none'}
    else:
        return {'display': 'none'}


@app.callback(
    Output(error_id, 'children'),
    [
        Input(submit_button_id, 'n_clicks'),
    ],
    [
        State(sample_table_id, 'data'),
        State(iso_table_id, 'data'),
        State(range_table_id, 'data'),
    ])
def error(n_submit, sample_tb_rows, iso_tb_rows, range_tb_rows):
    if n_submit is not None:
        # Convert all number str to numeric and keep rest invalid input
        sample_tb_dict = force_dict_to_numeric(input_dict_list=sample_tb_rows)
        sample_tb_df = pd.DataFrame(sample_tb_dict)

        iso_tb_dict = force_dict_to_numeric(input_dict_list=iso_tb_rows)
        iso_tb_df = pd.DataFrame(iso_tb_dict)

        range_tb_dict = force_dict_to_numeric(input_dict_list=range_tb_rows)
        range_tb_df = pd.DataFrame(range_tb_dict)

        # Test input format
        test_passed_list, output_div_list = validate_sample_input(sample_df=sample_tb_df,
                                                                  iso_df=iso_tb_df,
                                                                  sample_schema=sample_dict_schema,
                                                                  iso_schema=iso_dict_schema)
        # Test range table
        if range_tb_df[column_1][0] == range_tb_df[column_1][1]:
            test_passed_list.append(False)
            output_div_list.append(
                html.P("INPUT ERROR: {}: ['Energy min. can not equal energy max.']".format(str(energy_name))))
        else:
            test_passed_list.append(True)
            output_div_list.append(None)

        # Return result
        if all(test_passed_list):
            return True
        else:
            return output_div_list
    else:
        return None


@app.callback(
    Output(hidden_df_json_id, 'children'),
    [
        Input(submit_button_id, 'n_clicks'),
        Input(error_id, 'children'),
    ],
    [
        State(range_table_id, 'data'),
        State(e_step_id, 'value'),
        State(distance_id, 'value'),
        State(sample_table_id, 'data'),
        State(iso_table_id, 'data'),
        State(iso_check_id, 'values'),
    ])
def store_reso_df_in_json(n_submit,
                          test_passed,
                          range_tb_rows, e_step, distance_m,
                          sample_tb_rows, iso_tb_rows,
                          iso_changed):
    if test_passed is True:
        # Modify input for testing
        sample_tb_dict = force_dict_to_numeric(input_dict_list=sample_tb_rows)
        iso_tb_dict = force_dict_to_numeric(input_dict_list=iso_tb_rows)
        sample_tb_df = pd.DataFrame(sample_tb_dict)
        if iso_changed:
            iso_tb_df = pd.DataFrame(iso_tb_dict)
        else:
            iso_tb_df = form_iso_table(sample_df=sample_tb_df)

        # Calculation starts
        range_tb_df = pd.DataFrame(range_tb_rows)
        o_reso = init_reso_from_tb(range_tb_df=range_tb_df, e_step=e_step)
        o_reso = unpack_sample_tb_df_and_add_layer(o_reso=o_reso, sample_tb_df=sample_tb_df)
        o_reso = unpack_iso_tb_df_and_update(o_reso=o_reso, iso_tb_df=iso_tb_df, iso_changed=iso_changed)

        # Get dfs from o_reso stacks
        df_trans = o_reso.export(y_axis='transmission',
                                 x_axis='energy',
                                 time_unit='us',
                                 mixed=True,
                                 all_layers=True,
                                 all_elements=True,
                                 all_isotopes=True,
                                 source_to_detector_m=distance_m,
                                 output_type='df')

        df_sigma_b = o_reso.export(y_axis='sigma',
                                   x_axis='energy',
                                   time_unit='us',
                                   mixed=False,
                                   all_layers=False,
                                   all_elements=True,
                                   all_isotopes=True,
                                   source_to_detector_m=distance_m,
                                   output_type='df')

        df_sigma_raw = o_reso.export(y_axis='sigma_raw',
                                     x_axis='energy',
                                     time_unit='us',
                                     mixed=False,
                                     all_layers=False,
                                     all_elements=True,
                                     all_isotopes=True,
                                     source_to_detector_m=distance_m,
                                     output_type='df')

        df_x = pd.DataFrame()
        df_x[energy_name] = df_trans[energy_name][:]
        df_x = fill_df_x_types(df=df_x, distance_m=distance_m)

        df_trans.drop(columns=[df_trans.columns[0]], inplace=True)
        df_trans.rename(columns={'Total_transmission': 'Total'}, inplace=True)
        df_attenu = 1 - df_trans
        df_sigma_b.drop(columns=[df_sigma_b.columns[0]], inplace=True)
        df_sigma_raw.drop(columns=[df_sigma_raw.columns[0], df_sigma_raw.columns[2]],
                          inplace=True)

        datasets = {
            'df_x': df_x.to_json(orient='split', date_format='iso'),
            'df_trans': df_trans.to_json(orient='split', date_format='iso'),
            'df_attenu': df_attenu.to_json(orient='split', date_format='iso'),
            'df_sigma_b': df_sigma_b.to_json(orient='split', date_format='iso'),
            'df_sigma_raw': df_sigma_raw.to_json(orient='split', date_format='iso'),
        }
        return json.dumps(datasets)
    else:
        return None


@app.callback(
    Output(plot_id, 'children'),
    [
        Input(submit_button_id, 'n_clicks'),
        Input(error_id, 'children'),
        Input('y_type', 'value'),
        Input('x_type', 'value'),
        Input('plot_scale', 'value'),
        Input('show_opt', 'values'),
        Input(hidden_df_json_id, 'children'),
    ])
def plot(n_submit, test_passed, y_type, x_type, plot_scale, show_opt, jsonified_data):
    if test_passed is True:
        # Load and shape the data
        datasets = json.loads(jsonified_data)
        df_x = pd.read_json(datasets['df_x'], orient='split')
        df_trans = pd.read_json(datasets['df_trans'], orient='split')
        df_attenu = pd.read_json(datasets['df_attenu'], orient='split')
        df_sigma_b = pd.read_json(datasets['df_sigma_b'], orient='split')
        df_sigma_raw = pd.read_json(datasets['df_sigma_raw'], orient='split')

        df_sigma_b.drop(columns=[df_sigma_b.columns[0]], inplace=True)
        df_sigma_raw.drop(columns=[df_sigma_raw.columns[0]], inplace=True)

        if y_type == 'transmission':
            df = df_trans
            _y_label = 'Transmission'
        elif y_type == 'attenuation':
            df = df_attenu
            _y_label = 'Attenuation'
        elif y_type == 'sigma':
            df = df_sigma_b
            _y_label = 'Cross-sections (barn)'
        else:
            df = df_sigma_raw
            _y_label = 'Cross-sections (barn)'

        if x_type == 'energy':
            x_tag = energy_name
        elif x_type == 'lambda':
            x_tag = wave_name
        else:
            x_tag = tof_name

        df.insert(loc=0, column=x_tag, value=df_x[x_tag])

        print(df.head())
        print(df.tail())

        _log_log = False
        _log_y = False
        _log_x = False
        if plot_scale == 'logx':
            _log_x = True
        elif plot_scale == 'logy':
            _log_y = True
        elif plot_scale == 'loglog':
            _log_log = True

        # show_total = False
        # show_layer = False
        # show_ele = False
        # show_iso = False
        # if 'total' in show_opt:
        #     show_total = True
        # if 'layer' in show_opt:
        #     show_layer = True
        # if 'ele' in show_opt:
        #     show_ele = True
        # if 'iso' in show_opt:
        #     show_iso = True

        if 'total' in show_opt:
            _num = 0
        if 'layer' in show_opt:
            _num = 1
        if 'ele' in show_opt:
            _num = 1
        if 'iso' in show_opt:
            _num = 2

        # Plotting starts
        # data = [
        #     go.Scatter(
        #         x=df[energy_name],  # assign x as the dataframe column 'x'
        #         y=df[df_trans.columns[1]]
        #     )
        # ]
        # plotly_fig = go.Figure(data=data)

        ax_mpl = df.set_index(keys=x_tag).plot(legend=False, logx=_log_x, logy=_log_y, loglog=_log_log)
        ax_mpl.set_ylabel(_y_label)
        fig_mpl = ax_mpl.get_figure()
        plotly_fig = tls.mpl_to_plotly(fig_mpl)

        plotly_fig.layout.showlegend = True
        plotly_fig.layout.autosize = True
        plotly_fig.layout.height = 600
        plotly_fig.layout.width = 900
        plotly_fig.layout.margin = {'b': 52, 'l': 80, 'pad': 0, 'r': 15, 't': 15}
        plotly_fig.layout.xaxis1.tickfont.size = 15
        plotly_fig.layout.xaxis1.titlefont.size = 18
        plotly_fig.layout.yaxis1.tickfont.size = 15
        plotly_fig.layout.yaxis1.titlefont.size = 18

        return html.Div([dcc.Graph(figure=plotly_fig)])
        # return plotly_fig
    else:
        return None


@app.callback(
    Output(result_id, 'children'),
    [
        Input(submit_button_id, 'n_clicks'),
    ],
    [
        State(sample_table_id, 'data'),
        State(iso_table_id, 'data'),
        State(iso_check_id, 'values'),
    ])
def output_transmission_and_stack(n_submit, sample_tb_rows, iso_tb_rows, iso_changed):
    output_div = output_cg1d_result_stack(n_submit=n_submit,
                                          sample_tb_rows=sample_tb_rows,
                                          iso_tb_rows=iso_tb_rows,
                                          iso_changed=iso_changed)
    return output_div

# @app.callback(
#     Output('app2_download_link', 'href'),
#     [
#         Input(error_id, 'children'),
#         Input('y_type', 'value'),
#         Input('x_type', 'value'),
#         Input('show_opt', 'values'),
#         Input('app2_export_clip', 'values'),
#     ],
#     [
#         State(range_table_id, 'data'),
#         State(e_step_id, 'value'),
#         State(distance_id, 'value'),
#         State(sample_table_id, 'data'),
#         State(iso_table_id, 'data'),
#         State(iso_check_id, 'values'),
#     ])
# def export_plot_data(test_passed,
#                      y_type, x_type, show_opt, export_clip,
#                      range_tb_rows, e_step, distance_m,
#                      sample_tb_rows, iso_tb_rows,
#                      iso_changed):
#     if test_passed:
#         # Modify input for testing
#         sample_tb_dict = force_dict_to_numeric(input_dict_list=sample_tb_rows)
#         iso_tb_dict = force_dict_to_numeric(input_dict_list=iso_tb_rows)
#         sample_tb_df = pd.DataFrame(sample_tb_dict)
#         if iso_changed:
#             iso_tb_df = pd.DataFrame(iso_tb_dict)
#         else:
#             iso_tb_df = form_iso_table(sample_df=sample_tb_df)
#
#         # Test input format
#         test_passed_list, output_div_list = validate_sample_input(sample_df=sample_tb_df,
#                                                                   iso_df=iso_tb_df,
#                                                                   sample_schema=sample_dict_schema,
#                                                                   iso_schema=iso_dict_schema)
#
#         # Calculation starts
#         if all(test_passed_list):
#             range_tb_df = pd.DataFrame(range_tb_rows)
#             o_reso = init_reso_from_tb(range_tb_df=range_tb_df, e_step=e_step)
#             o_reso = unpack_sample_tb_df_and_add_layer(o_reso=o_reso, sample_tb_df=sample_tb_df)
#             o_reso = unpack_iso_tb_df_and_update(o_reso=o_reso, iso_tb_df=iso_tb_df, iso_changed=iso_changed)
#
#             show_total = False
#             show_layer = False
#             show_ele = False
#             show_iso = False
#             if 'total' in show_opt:
#                 show_total = True
#             if 'layer' in show_opt:
#                 show_layer = True
#             if 'ele' in show_opt:
#                 show_ele = True
#             if 'iso' in show_opt:
#                 show_iso = True
#             if export_clip:
#                 _type = 'clip'
#             else:
#                 _type = 'df'
#
#             # if n_link_click is not None:
#             df = o_reso.export(y_axis=y_type,
#                                x_axis=x_type,
#                                time_unit='us',
#                                mixed=show_total,
#                                all_layers=show_layer,
#                                all_elements=show_ele,
#                                all_isotopes=show_iso,
#                                source_to_detector_m=distance_m,
#                                output_type=_type)
#             # if export_type == 'download':
#             csv_string = df.to_csv(index=False, encoding='utf-8')
#             csv_string = "data:text/csv;charset=utf-8,%EF%BB%BF" + urllib.parse.quote(csv_string)
#             return csv_string
#         else:
#             return None
#     else:
#         return None
