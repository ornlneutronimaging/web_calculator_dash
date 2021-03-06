from dash.dependencies import Input, Output, State

from _app import app
from _utilities import *
import plotly.tools as tls
import matplotlib.pyplot as plt
# from bem.matter import Atom, Lattice, Structure
# from bem import xscalc
# from bem.matter import loadCif
# import numpy as np

# Bragg-edge tool

app_name = 'app5'
app_id_dict = init_app_ids(app_name=app_name)

# Create app layout
layout = html.Div(
    [
        # init_app_links(current_app=app_name, app_dict_all=app_dict),

        # # Experiment input
        # html.Div(
        #     [
        #         html.H3('Instrument Parameters:'),
        #         html.Div(
        #             [
        #                 html.H6('Source-to-detector distance:'),
        #                 html.Div(
        #                     [
        #                         dcc.Input(id=app_id_dict['distance_id'], type='number', value=distance_default,
        #                                   min=0,
        #                                   inputMode='numeric',
        #                                   step=0.01,
        #                                   className='nine columns'),
        #                         html.P('(m)', className='one column',
        #                                style={'marginBottom': 10, 'marginTop': 5},
        #                                # style={'verticalAlign': 'middle'},
        #                                ),
        #                     ], className='row', style={'verticalAlign': 'middle'},
        #                 ),
        #             ], className=col_width_5,
        #         ),
        #
        #         html.Div(
        #             [
        #                 html.H6('Delay:'),
        #                 html.Div(
        #                     [
        #                         dcc.Input(id=app_id_dict['delay_id'], type='number', value=delay_default,
        #                                   min=0,
        #                                   inputMode='numeric',
        #                                   step=0.01,
        #                                   className='nine columns'),
        #                         html.P('(us)', className='one column',
        #                                style={'marginBottom': 10, 'marginTop': 5},
        #                                # style={'verticalAlign': 'middle'},
        #                                ),
        #                     ], className='row', style={'verticalAlign': 'middle'},
        #                 ),
        #             ], className=col_width_5, style={'verticalAlign': 'middle'},
        #         ),
        #     ], className='row',
        # ),

        html.Div(
            [
                html.H6('Wavelength band (\u212B):'),
                dcc.Input(id=app_id_dict['band_min_id'], type='number',
                          inputMode='numeric',
                          placeholder='Min.',
                          step=0.001,
                          # className='one columns',
                          ),
                dcc.Input(id=app_id_dict['band_max_id'], type='number',
                          inputMode='numeric',
                          placeholder='Max.',
                          step=0.001,
                          # className='one columns',
                          ),
            ], className='row', style={'verticalAlign': 'middle'},
        ),

        html.H3('Upload cif file/files:'),

        html.Div(
            [
                dcc.Upload(id=app_id_dict['cif_upload_id'],
                           children=html.Div([
                               'Drag and Drop or ',
                               html.A('Select Files'),
                           ]),
                           style={
                               'width': '100%',
                               'height': '60px',
                               'lineHeight': '60px',
                               'borderWidth': '1px',
                               'borderStyle': 'dashed',
                               'borderRadius': '5px',
                               'textAlign': 'center',
                               'margin': '10px'
                           },
                           # Allow multiple files to be uploaded
                           multiple=True,
                           last_modified=0,
                           ),
                html.Div(id=app_id_dict['cif_upload_fb_id']),

                # html.H6('Background (optional):'),
                # dcc.Upload(id=app_id_dict['background_upload_id'],
                #            children=html.Div([
                #                'Drag and Drop or ',
                #                html.A('Select Files'),
                #            ]),
                #            style={
                #                'width': '100%',
                #                'height': '60px',
                #                'lineHeight': '60px',
                #                'borderWidth': '1px',
                #                'borderStyle': 'dashed',
                #                'borderRadius': '5px',
                #                'textAlign': 'center',
                #                'margin': '10px'
                #            },
                #            # Allow multiple files to be uploaded
                #            multiple=False,
                #            last_modified=0,
                #            ),
                # html.Div(id=app_id_dict['background_upload_fb_id']),

                html.Div(id=app_id_dict['hidden_upload_time_id'], style={'display': 'none'}, children=0),
            ]
        ),

        # Error message div
        html.Div(id=app_id_dict['error_id'], children=None),

        # Output div
        html.Div(
            [
                html.H3('Plot:'),
                html.Div(
                    [
                        html.Div(
                            [
                                html.P('X options: '),
                                dcc.RadioItems(id='x_type',
                                               options=[
                                                   {'label': 'Energy (eV)', 'value': 'energy'},
                                                   {'label': 'Wavelength (\u212B)', 'value': 'lambda'},
                                                   {'label': 'Time-of-flight (\u03BCs)', 'value': 'time'},
                                                   {'label': 'Image index (#)', 'value': 'number'},
                                               ],
                                               value='number',
                                               # n_clicks_timestamp=0,
                                               )
                            ], className=col_width_3
                        ),
                        html.Div(
                            [
                                html.P('Y options: '),
                                dcc.RadioItems(id='y_type',
                                               options=[
                                                   {'label': 'Transmission', 'value': 'transmission'},
                                                   {'label': 'Attenuation', 'value': 'attenuation'},
                                               ],
                                               value='transmission',
                                               # n_clicks_timestamp=0,
                                               )
                            ], className=col_width_3
                        ),
                        html.Div(
                            [
                                html.P('Scale options: '),
                                dcc.RadioItems(id='plot_scale',
                                               options=[
                                                   {'label': 'Linear', 'value': 'linear'},
                                                   {'label': 'Log x', 'value': 'logx'},
                                                   {'label': 'Log y', 'value': 'logy'},
                                                   {'label': 'Loglog', 'value': 'loglog'},
                                               ],
                                               value='linear',
                                               # n_clicks_timestamp=0,
                                               )
                            ], className=col_width_3
                        ),
                    ], className='row'
                ),
                # Transmission at CG-1D and stack info
                html.Div(id=app_id_dict['result_id']),
                # Plot
                html.Div(id=app_id_dict['plot_div_id'], children=plot_loading, className='container'),
            ],
            id=app_id_dict['output_id'],
            style={'display': 'none'},
        ),
    ]
)


@app.callback(
    [
        Output(app_id_dict['plot_div_id'], 'children'),
        Output(app_id_dict['output_id'], 'style'),
        Output(app_id_dict['cif_upload_fb_id'], 'children'),
    ],
    [
        Input(app_id_dict['cif_upload_id'], 'contents'),
        Input('x_type', 'value'),
        Input('y_type', 'value'),
        Input('plot_scale', 'value'),
    ],
    [
        State(app_id_dict['cif_upload_id'], 'filename'),
        State(app_id_dict['cif_upload_id'], 'last_modified'),
        State(app_id_dict['output_id'], 'style'),
    ])
def plot(cif_contents, x_type, y_type, plot_scale,
         cif_names, cif_last_modified_time, output_style):
    error_div_list = []
    df_plot = pd.DataFrame()
    loaded = []
    data_fb = []
    print(cif_contents)

    if cif_contents is not None:
        for each_index, each_content in enumerate(cif_contents):
            _df_data, data_error_div = parse_cif_content(content=each_content,
                                                         name=cif_names[each_index],
                                                         header=0)
            if data_error_div is None:
                df_plot[cif_names[each_index]] = _df_data['Y']
                loaded.append('data')
                data_fb.append(html.Div(['\u2705 Data file "{}" uploaded.'.format(cif_names[each_index])]))
            else:
                data_fb.append(data_error_div)
                error_div_list.append(data_error_div)

    # Plot
    if len(error_div_list) == 0:
        if y_type == 'attenuation':
            df_plot = 1 - df_plot
        df_plot['X'] = df_spectra[0]
        df_plot = shape_df_to_plot(x_type=x_type, df=df_plot, distance=distance, delay=delay)
        x_label = x_type_to_x_label(x_type)
        y_label = y_type_to_y_label(y_type)
        output_style['display'] = 'block'
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        # Plot
        try:
            ax1 = df_plot.set_index(keys='X').plot(legend=False, ax=ax1)
        except TypeError:
            pass
        ax1.set_ylabel(y_label)
        ax1.set_xlabel(x_label)
        plotly_fig = tls.mpl_to_plotly(fig)

        # Layout
        plotly_fig.layout.showlegend = True
        plotly_fig.layout.autosize = True
        plotly_fig.layout.height = 600
        plotly_fig.layout.width = 900
        plotly_fig.layout.margin = {'b': 52, 'l': 80, 'pad': 0, 'r': 15, 't': 15}
        plotly_fig.layout.xaxis1.tickfont.size = 15
        plotly_fig.layout.xaxis1.titlefont.size = 18
        plotly_fig.layout.yaxis1.tickfont.size = 15
        plotly_fig.layout.yaxis1.titlefont.size = 18
        plotly_fig.layout.xaxis.autorange = True
        plotly_fig['layout']['yaxis']['autorange'] = True

        if plot_scale == 'logx':
            plotly_fig['layout']['xaxis']['type'] = 'log'
            plotly_fig['layout']['yaxis']['type'] = 'linear'
        elif plot_scale == 'logy':
            if y_type not in ['attenuation', 'transmission']:
                plotly_fig['layout']['xaxis']['type'] = 'linear'
                plotly_fig['layout']['yaxis']['type'] = 'log'
        elif plot_scale == 'loglog':
            if y_type not in ['attenuation', 'transmission']:
                plotly_fig['layout']['xaxis']['type'] = 'log'
                plotly_fig['layout']['yaxis']['type'] = 'log'
        else:
            plotly_fig['layout']['xaxis']['type'] = 'linear'
            plotly_fig['layout']['yaxis']['type'] = 'linear'
        return html.Div([dcc.Graph(figure=plotly_fig,
                                   id=app_id_dict['plot_fig_id'])]), output_style, data_fb
    else:
        output_style['display'] = 'none'
        return plot_loading, output_style, data_fb
