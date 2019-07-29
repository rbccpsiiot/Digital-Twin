# GUI Front-end for the SMT_simulator
# built using Kivy (https://kivy.org/#home)

# Author: Neha Karanjkar


# Kivy-related imports:
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label  import Label
from kivy.uix.button  import Button
from kivy.uix.splitter import Splitter
from kivy.uix.textinput  import TextInput
from kivy.uix.image  import Image
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, Rectangle

# Simulator-related
import SMT_simulation


Builder.load_string("""
<SMT_dashboard>:

    do_default_tab: False
    TabbedPanelItem:
        text: 'Overview'
        GridLayout:
            rows:2
            spacing:10
            padding:10
            Label:
                text: 'The SMT line Model'
                size_hint_y:None
                height:40
            Image:
                source:"SMT_line.png"
                keep_ratio:True
    TabbedPanelItem:
        text: 'Parameters'
        GridLayout:
            cols:1
            spacing:10
            padding:10
            
            Label:
                text:"Enter machine parameters:"
                size_hint_y:None
                height:40
            
            ScrollView:
                ParameterSetup:
                    id:id_parameter_setup
            Button:
                text: 'Set'
                on_press:root.set_parameters()
                size_hint_y:None
                height:40

    TabbedPanelItem:
        text: 'Simulation'
        GridLayout:
            rows:6
            row_force_default:False
            spacing:10
            padding:10

            Label:
                text: 'Run Simulation'
                size_hint_y:None
                height:40
            
            GridLayout:
                cols:2
                rows:2
                spacing:5
                padding:5
                size_hint_y:None
                height:100
                
                Label:
                    text: 'Enter simulation time (in seconds):'
                IntegerInput:
                    id: param_simulation_time
                    multiline:False
                    input_type:'number'
                    text:str(app.param_simulation_time_default)
                
                Label:
                    text: 'Generate detailed activity log:'
                CheckBox:
                    id:checkbox_enable_activity_log
            Button:
                text: 'Run Simulation'
                on_press:root.run_simulation()
                size_hint_y:None
                height:60
            Label:
                id: activity_log
                text: ""
                font_size: 15
                text_size: None, None           
                size_hint: None, None
                width: self.texture_size[0]
                height: self.texture_size[1]
            Splitter:
                sizable_from: 'top'
                ScrollView:
                    text: 'Simulation Results'
                    Label:
                        id:simulation_results
                        text: "\\nSimulation Results:"
                        font_size: 15
                        text_size: None, None           
                        size_hint: None, None
                        width: self.texture_size[0]
                        height: self.texture_size[1]
  """)

# The following code can be used for displaying 
# a part of the activity log, if required.
#
# TabbedPanelItem:
#       text: 'Activity Log'
#       ScrollView:
#           text: "Label1"
#           Label:
#               id: activity_log
#               text: "<empty>"
#               font_size: 15
#               text_size: None, None           
#               size_hint: None, None
#               width: self.texture_size[0]
#               height: self.texture_size[1]



from io import StringIO


#A TextInput widget that allows only numbers(integers)
#to be entered.
class IntegerInput(TextInput):

    def insert_text(self, substring, from_undo=False):
        s=""
        try:
            num = int(substring)
            s=str(num)
        except ValueError as verr:
            num = 0
            s=""
        return super(IntegerInput, self).insert_text(str(s), from_undo=from_undo)

import re
#Widget that allows only float input
class FloatInput(TextInput):

    pat = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


PARAM_HEIGHT= 40
PARAM_FONT_SIZE=15

class SingleParameterSetup(GridLayout):
    def __init__(self, parameter, **kwargs):
        super(SingleParameterSetup, self).__init__(**kwargs)
        self.rows=1
        self.cols=2
        self.add_widget(Label(text=parameter[1]["label"],size_hint_y=None,height=PARAM_HEIGHT, font_size=PARAM_FONT_SIZE))
        parameter_format = parameter[1]["format"]
        if(parameter_format == "float"):
            input_box = FloatInput(multiline=False, text=str(parameter[1]["default_value"]),size_hint_y=None,height=PARAM_HEIGHT,font_size=PARAM_FONT_SIZE)
        elif(parameter_format == "int"):
            input_box = IntegerInput(multiline=False, text=str(parameter[1]["default_value"]),size_hint_y=None,height=PARAM_HEIGHT,font_size=PARAM_FONT_SIZE)

        self.add_widget(input_box)
        # add a reference to the newly created widget into the dictionary
        parameter[1]["input_widget_ref"]=input_box


class ParameterSetup(GridLayout):
    def __init__(self, **kwargs):
        super(ParameterSetup, self).__init__(**kwargs)
        self.cols=1
        self.padding=5
        self.spacing=5
        self.size_hint_y=None
 
    def add_parameters(self, model_parameters):
        
        total_lines=0
        #Input boxes for entering parameters of each machine:
        for machine in model_parameters.items():
            self.add_widget(Label(text=machine[1]["label"],size_hint_y=None, height=60, font_size=15))
            total_lines+=1
            for param in machine[1]["parameters"].items():
                self.add_widget(SingleParameterSetup(param))
                total_lines+=1

        self.height=(total_lines)*70


class SMT_dashboard(TabbedPanel):
    
    def __init__(self,**kwargs):
        # Create a simulator object
        self.simulator  = SMT_simulation.SMT_simulation()
        # Obtain the default parameter values:
        self.model_parameters = self.simulator.model_parameters
        super(SMT_dashboard, self).__init__(**kwargs)

        #add input boxes for setting model parameters:
        self.ids.id_parameter_setup.add_parameters(self.model_parameters)
        
    def set_parameters(self):
        # read values of the model parameters
        # from the GUI input and save them into the dictionary
        
        for machine in self.model_parameters.items():
            for param in machine[1]["parameters"].items():
                parameter_format = param[1]["format"] 
                if(parameter_format=="int"):
                    param[1]["value"] = int(param[1]["input_widget_ref"].text)
                elif(parameter_format=="float"):
                    param[1]["value"] = float(param[1]["input_widget_ref"].text)
        print("Model parameter values updated:")
        print(self.model_parameters)


    def run_simulation(self):
        # run simulation for the specified amount of time
        simulation_time = int(self.ids.param_simulation_time.text)
        assert(simulation_time>=1 and simulation_time<1e10)
        if(self.ids.checkbox_enable_activity_log.active==True):
            generate_activity_log= True
            self.ids.activity_log.text = "Activity log generated in file ./activity_log.txt"
        else:
            generate_activity_log= False
            self.ids.activity_log.text = ""
        
        
        results_string = self.simulator.run_simulation(simulation_time,generate_activity_log)
        
        #display aggregate results 
        self.ids.simulation_results.text="\nSimulation Results:\n"+ results_string.getvalue()
        pass


class SMT_dashboardApp(App):
    param_simulation_time_default = 300
    def build(self):
        return SMT_dashboard()


if __name__ == '__main__':
    SMT_dashboardApp().run()
