from model import InitForm
from model import SampleForm
import flask
from flask import render_template, request
from compute import init_reso, add_layer, load_beam_shape
from flask import Flask
import io
import os
import matplotlib.pyplot as plt
import base64
from scipy.interpolate import interp1d
from ImagingReso.resonance import Resonance
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pprint
from ImagingReso._utilities import ev_to_angstroms
from ImagingReso._utilities import ev_to_s
import math

# Setup app
server = Flask(__name__)
server.secret_key = os.environ.get('secret_key', 'secret')

app = dash.Dash(__name__)
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

# Create app layout
app.layout = html.Div(
    [
        # Heading section
        html.Div(
            [
                html.H1(
                    children='ImagingReso',
                    className='nine columns'
                ),
                html.Img(
                    src="http://static1.squarespace.com/static/546fb494e4b08c59a7102fbc/t/591e105a6a496334b96b8e47/1497495757314/.png",
                    className='three columns',
                    style={
                        'height': '7%',
                        'width': '7%',
                        'float': 'right',
                        'position': 'relative',
                        'padding-top': 0,
                        'padding-right': 0
                    },
                ),
            ], className="row"
        ),
        html.Div(
            children='''
                A web application for *Neutron Imaging*.
                ''',
            className='row'
        ),
        html.H3('Global parameters'),
        # Global parameters
        html.Div(
            [
                # Range input
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Checklist(id='check_energy',
                                              options=[
                                                  {'label': 'Energy (eV)', 'value': True, 'disabled': True},
                                              ],
                                              values=[True],
                                              labelStyle={'display': 'inline-block'}
                                              ),
                                html.Div(
                                    [
                                        dcc.Input(id='e_min', type='number', value=1, min=0,
                                                  inputmode='numeric',
                                                  step=1,
                                                  ),
                                        dcc.Input(id='e_max', type='number', value=100, max=1e5,
                                                  inputmode='numeric',
                                                  step=1,
                                                  ),
                                    ]
                                ),
                            ],
                            className='three columns',
                        ),

                        html.Div(
                            [
                                dcc.Checklist(id='check_lambda',
                                              options=[
                                                  {'label': 'Wavelength (\u212B)', 'value': True},
                                              ],
                                              values=[],
                                              labelStyle={'display': 'inline-block'}
                                              ),
                                html.Div(id='range_lambda'),
                            ],
                            className='three columns',
                        ),

                        html.Div(
                            [

                                dcc.Checklist(id='check_tof',
                                              options=[
                                                  {'label': 'Time-of-flight (\u03BCs)', 'value': True},
                                              ],
                                              values=[],
                                              labelStyle={'display': 'inline-block'}
                                              ),
                                html.Div(id='range_tof'),
                            ],
                            className='three columns',
                        ),

                        html.Div(
                            [
                                html.P('Source-to-detector (m)'),
                                # html.P('(ONLY for TOF)'),
                                dcc.Input(id='distance', type='number', value=16.45, min=1,
                                          inputmode='numeric',
                                          step=0.01,
                                          # size=5
                                          # className='six columns',
                                          )
                            ],
                            className='three columns',
                        ),

                    ], className='row',
                ),

                # html.Br(),

                # Step input
                html.Div(
                    [
                        html.Div(
                            [
                                html.P('Step in energy (eV)'),
                                # dcc.Input(id='e_step', type='number', value=0.01, min=0.001, max=1),
                                dcc.Dropdown(
                                    id='e_step',
                                    options=[
                                        {'label': '0.001', 'value': 0.001},
                                        {'label': '0.01', 'value': 0.01},
                                        {'label': '0.1', 'value': 0.1},
                                        {'label': '1', 'value': 1},
                                        {'label': '10', 'value': 10},
                                        {'label': '100', 'value': 100},
                                    ],
                                    value=0.01,
                                    searchable=False,
                                    clearable=False,
                                    # placeholder="Pick a step size",
                                )
                            ], className='three columns'
                        ),

                        html.Div(
                            [
                                # Energy slider
                                # html.P('Energy range slider'),
                                html.Br(),
                                dcc.RangeSlider(
                                    id='e_range_slider',
                                    min=-5,
                                    max=6,
                                    value=[0, 2],
                                    allowCross=False,
                                    dots=False,
                                    step=0.01,
                                    # updatemode='drag'
                                    marks={i: '{} eV'.format(pow(10, i)) for i in range(-5, 7, 1)},
                                    className='row',
                                ),
                            ], className='nine columns'
                        ),
                    ], className='row'
                ),
            ]
        ),

        html.H3('Sample info'),

        # Sample input
        html.Div(
            [
                html.P('Chemical formula'),
                dcc.Input(id='formula', value='Ag', type='text', minlength=1),

                html.P('Thickness (mm)'),
                dcc.Input(id='thickness', value=0.5, type='number', min=1e-9, inputmode="numeric", step=0.01),

                html.P('Density (g/cm3)'),
                # html.P('(Input is optional only for solid single element layer)'),
                dcc.Input(id='density', type='number', min=1e-9, placeholder='Optional if standard', step=0.001),
            ]
        ),
        # html.Label('Slider 1'),
        # dcc.Slider(id='slider-1'),
        html.Div(
            [
                dcc.RadioItems(id='y_type',
                               options=[
                                   {'label': 'Attenuation', 'value': 'attenuation'},
                                   {'label': 'Transmission', 'value': 'transmission'},
                                   {'label': 'Total cross-section', 'value': 'sigma'}
                               ],
                               value='attenuation',
                               labelStyle={'display': 'inline-block'}
                               )
            ]
        ),
        html.Div(
            [
                dcc.RadioItems(id='x_type',
                               options=[
                                   {'label': 'Energy', 'value': 'energy'},
                                   {'label': 'Wavelength', 'value': 'lambda'},
                                   {'label': 'Time', 'value': 'time'},
                               ],
                               value='energy',
                               labelStyle={'display': 'inline-block'}
                               )
            ]
        ),
        html.Div(
            [
                dcc.RadioItems(id='time_unit',
                               options=[
                                   {'label': 's', 'value': 's'},
                                   {'label': 'us', 'value': 'us'},
                                   {'label': 'ns', 'value': 'ns'},
                               ],
                               value='us',
                               labelStyle={'display': 'inline-block'}
                               )
            ]
        ),
        html.Div(
            [
                dcc.Checklist(id='log_scale',
                              options=[
                                  {'label': 'x in log', 'value': 'logx'},
                                  {'label': 'y in log', 'value': 'logy'},
                                  {'label': 'None', 'value': 'none'}
                              ],
                              values=['none'],
                              labelStyle={'display': 'inline-block'}
                              )
            ]
        ),

        html.Div(
            [
                html.Button('Submit', id='button_submit'),
            ]
        ),

        # html.Button('Show plot', id='button-3'),
        # html.Hr(),
        # html.Div(id='plot'),
        #
        dcc.Graph(id='plot'),
        html.Div(id='result'),
        html.Hr(),

        html.Div(
            [
                html.Div(id='stack'),
            ],
        ),
        html.Hr(),

    ], className='ten columns offset-by-one')


# def transform_value(value):
#     return 10 ** value


@app.callback(
    Output('range_lambda', 'children'),
    [
        Input('check_lambda', 'values'),
        Input('e_min', 'value'),
        Input('e_max', 'value'),
    ])
def show_range_in_lambda(boo, e_min, e_max):
    if boo:
        lambda_1 = ev_to_angstroms(array=e_min)
        lambda_2 = ev_to_angstroms(array=e_max)
        return html.Div(
            [
                dcc.Input(id='lambda_1', type='number', value=lambda_1, inputmode='numeric', step=0.01),
                dcc.Input(id='tambda_2', type='number', value=lambda_2, inputmode='numeric', step=0.01),
            ]
        )


@app.callback(
    Output('range_tof', 'children'),
    [
        Input('check_tof', 'values'),
        Input('distance', 'value'),
        Input('e_min', 'value'),
        Input('e_max', 'value'),
    ])
def show_range_in_tof(boo, distance, e_min, e_max):
    if boo:
        tof_1 = ev_to_s(array=e_min, source_to_detector_m=distance, offset_us=0) * 1e6
        tof_2 = ev_to_s(array=e_max, source_to_detector_m=distance, offset_us=0) * 1e6
        return html.Div(
            [
                dcc.Input(id='tof_1', type='number', value=tof_1, inputmode='numeric', step=1),
                dcc.Input(id='tof_2', type='number', value=tof_2, inputmode='numeric', step=1),
            ]
        )


@app.callback(
    Output('e_min', 'value'),
    [
        Input('e_range_slider', 'value'),
    ])
def update_e_min_from_slider(slider):
    transformed_value = [pow(10, v) for v in slider]
    _min = transformed_value[0]
    # if _min != min_input:
    #     return _min
    return _min


@app.callback(
    Output('e_max', 'value'),
    [
        Input('e_range_slider', 'value'),
    ])
def update_e_max_from_slider(slider):
    transformed_value = [pow(10, v) for v in slider]
    _max = transformed_value[1]
    # if _max != max_input:
    #     return _max
    return _max


# @app.callback(
#     Output('e_range_slider', 'value'),
#     [
#         Input('e_min', 'value'),
#         Input('e_max', 'value'),
#     ])
# def update_slider_from_input(e_min, e_max):
#     # transformed_value = [math.pow(10, v) for v in slider_value]
#     # _min = transformed_value[0]
#     # _max = transformed_value[1]
#     min_slider = math.log10(e_min)
#     max_slider = math.log10(e_max)
#     return [min_slider, max_slider]


@app.callback(
    Output('stack', 'children'),
    [
        Input('button_submit', 'n_clicks'),
    ],
    [
        State('e_min', 'value'),
        State('e_max', 'value'),
        State('e_step', 'value'),
        State('formula', 'value'),
        State('thickness', 'value'),
        State('density', 'value'),
    ])
def compute(n_clicks, e_min, e_max, e_step, formula, thickness, density):
    # if n_clicks is not None:
    o_reso = Resonance(energy_min=e_min, energy_max=e_max, energy_step=e_step)
    if density is not None:
        o_reso.add_layer(formula=formula,
                         thickness=thickness,
                         density=density)
    else:
        o_reso.add_layer(formula=formula,
                         thickness=thickness)
    stack = o_reso.stack
    p_stack = pprint.pformat(o_reso.stack)
    layer = list(stack.keys())
    for each_layer in stack.keys():
        current_layer = stack[each_layer]
        elements = current_layer['elements']
    return [
        html.P("Stack: {}".format(p_stack)),
        html.P("Layer: {}".format(layer)),
        html.P("Element: {}".format(elements)),
        html.P("Clicks: {}".format(n_clicks)),
        html.P("e_min_slider: {}".format(e_min)),
        html.P("e_max_slider: {}".format(e_max)),
        html.P("e_step_slider: {}".format(e_step)),
    ]


# else:
#     return None


@app.callback(
    Output('plot', 'figure'),
    [
        Input('button_submit', 'n_clicks'),
    ],
    [
        State('e_min', 'value'),
        State('e_max', 'value'),
        State('e_step', 'value'),
        State('formula', 'value'),
        State('thickness', 'value'),
        State('density', 'value'),
        State('y_type', 'value'),
        State('x_type', 'value'),
        State('time_unit', 'value'),
    ])
def plot(n_clicks, e_min, e_max, e_step, formula, thickness, density, y_type, x_type, time_unit):
    o_reso = Resonance(energy_min=e_min, energy_max=e_max, energy_step=e_step)
    if density is not None:
        o_reso.add_layer(formula=formula,
                         thickness=thickness,
                         density=density)
    else:
        o_reso.add_layer(formula=formula,
                         thickness=thickness)
    plotly_fig = o_reso.plot(plotly=True, y_axis=y_type, x_axis=x_type, time_unit=time_unit, all_elements=True,
                             all_isotopes=True)
    plotly_fig.layout.showlegend = True
    return plotly_fig


# def plot(n_clicks, e_min, e_max, e_step, formula, thickness, density):
#     if n_clicks is not None:
#         o_reso = Resonance(energy_min=e_min, energy_max=e_max, energy_step=e_step)
#         if density is not None:
#             o_reso.add_layer(formula=formula,
#                              thickness=thickness,
#                              density=density)
#         else:
#             o_reso.add_layer(formula=formula,
#                              thickness=thickness)
#         plotly_fig = o_reso.plot(plotly=True, all_elements=True, all_isotopes=True)
#         plotly_fig.layout.showlegend = True
#         return plotly_fig
#     else:
#         return None


@app.callback(
    Output('result', 'children'),
    [
        Input('button_submit', 'n_clicks'),
    ],
    [
        State('formula', 'value'),
        State('thickness', 'value'),
        State('density', 'value'),
        State('y_type', 'value'),
    ])
def calculate_transmission_cg1d(n_clicks, formula, thickness, density, y_type):
    _main_path = os.path.abspath(os.path.dirname(__file__))
    _path_to_beam_shape = os.path.join(_main_path, 'static/instrument_file/beam_shape_cg1d.txt')
    df = load_beam_shape(_path_to_beam_shape)
    o_reso = init_reso(e_min=0.00025,
                       e_max=0.12525,
                       e_step=0.000625)
    if density is not None:
        o_reso.add_layer(formula=formula,
                         thickness=thickness,
                         density=density)
    else:
        o_reso.add_layer(formula=formula,
                         thickness=thickness)
    # interpolate with the beam shape energy ()
    interp_type = 'cubic'
    energy = o_reso.total_signal['energy_eV']
    trans = o_reso.total_signal['transmission']
    interp_function = interp1d(x=energy, y=trans, kind=interp_type)
    # add interpolated transmission value to beam shape df
    trans = interp_function(df['energy_eV'])
    # calculated transmitted flux
    trans_flux = trans * df['flux']
    stack = o_reso.stack
    # stack = pprint.pformat(o_reso.stack)

    _total_trans = sum(trans_flux) / sum(df['flux']) * 100
    total_trans = round(_total_trans, 3)
    if y_type == 'transmission':
        return html.P('The total neutron transmission at CG-1D: {} %'.format(total_trans))
    else:
        return html.P('The total neutron attenuation at CG-1D: {} %'.format(100 - total_trans))


# @app.server.route('/reso_plot', methods=['GET', 'POST'])
# def index():
#     init_form = InitForm(request.form)
#     sample_form = SampleForm(request.form)
#     if request.method == 'POST':
#
#         if init_form.validate() and sample_form.validate():
#             o_reso = init_reso(init_form.e_min.data,
#                                init_form.e_max.data,
#                                init_form.e_step.data)
#             o_reso.add_layer(sample_form.formula.data,
#                              sample_form.thickness.data,
#                              sample_form.density.data)
#         result = o_reso.stack
#         plot = o_reso.plot(plotly=True)
#         # pprint.pprint(plot)
#         # app_dash.layout = html.Div(children=[
#         #     html.H1(children='Resonance Plot'),
#         #
#         #     html.Div(children='''
#         #             A web application for resonance imaging.
#         #         '''),
#         #
#         #     dcc.Graph(plot)
#         # ])
#     else:
#         result = None
#         plot = None
#
#     return render_template('view_reso.html',
#                            init_form=init_form,
#                            sample_form=sample_form,
#                            result=result,
#                            plot=plot)

# @app_flask.route('/cg1d', methods=['GET', 'POST'])
# def cg1d():
#     sample_form = SampleForm(request.form)
#     _main_path = os.path.abspath(os.path.dirname(__file__))
#     _path_to_beam_shape = os.path.join(_main_path, 'static/instrument_file/beam_shape_cg1d.txt')
#     df = load_beam_shape(_path_to_beam_shape)
#     if request.method == 'POST' and sample_form.validate():
#         o_reso = init_reso(e_min=0.00025,
#                            e_max=0.12525,
#                            e_step=0.000625)
#         o_reso.add_layer(sample_form.formula.data,
#                          sample_form.thickness.data,
#                          sample_form.density.data)
#         # interpolate with the beam shape energy ()
#         interp_type = 'cubic'
#         energy = o_reso.total_signal['energy_eV']
#         trans = o_reso.total_signal['transmission']
#         interp_function = interp1d(x=energy, y=trans, kind=interp_type)
#         # add interpolated transmission value to beam shape df
#         trans = interp_function(df['energy_eV'])
#         # calculated transmitted flux
#         trans_flux = trans * df['flux']
#         stack = o_reso.stack
#         # stack = pprint.pformat(o_reso.stack)
#
#         _total_trans = sum(trans_flux) / sum(df['flux']) * 100
#         total_trans = round(_total_trans, 3)
#     else:
#         total_trans = None
#         stack = None
#     return render_template('view_cg1d.html',
#                            sample_form=sample_form,
#                            total_trans=total_trans,
#                            stack=stack)
#
#
@app.server.route('/plot')
def build_plot():
    img = io.BytesIO()

    y = [1, 2, 3, 4, 5]
    x = [0, 2, 1, 3, 4]
    plt.plot(x, y)
    plt.savefig(img, format='png')
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue()).decode()

    return '<img src="data:image/png;base64,{}">'.format(plot_url)


if __name__ == '__main__':
    app.run_server(debug=True)
