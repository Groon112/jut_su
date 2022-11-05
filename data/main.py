from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.properties import NumericProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.label import Label
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button

Builder.load_string('''

<SelectableLabel>:
    # Draw a background to indicate selection
    background_color: (.8, .8, .8, .5) if self.selected else (1, 1, 1, 1)
    # canvas.before:
    #     Color:
    #         rgba: (.8, .8, .8, .2) if self.selected else (.8, .8, .8, .5)
    #     Rectangle:
    #         pos: self.pos
    #         size: self.size
<RV>:
    viewclass: 'SelectableLabel'
    SelectableRecycleGridLayout:
        spacing: 1
        default_size: None, dp(56)
        default_size_hint: 1, None
        cols: 5
        size_hint_y: None
        height: self.minimum_height
        # orientation: 'vertical'
        multiselect: True
        touch_multiselect: True

<RVScreen>:
    BoxLayout:
        orientation: "vertical"
        RV:
''')


class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
                                  RecycleGridLayout):
    """ Adds selection and focus behaviour to the view. """

    def on_selected_nodes(self, grid, nodes):
        print("Selected nodes = {0}".format(nodes))


class SelectableLabel(RecycleDataViewBehavior, Button):
    """ Add selection support to the Label """
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        """ Add selection on touch down """

        # if super(SelectableLabel, self).on_touch_down(touch):
        #     print('otd true')
        #     return True

        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """ Respond to the selection of items in the view. """
        self.selected = is_selected
        # if is_selected:
        #     print("selection changed to {0}".format(rv.data[index]))
        # else:
        #     print("selection removed for {0}".format(rv.data[index]))


class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = [{'text': str(x)} for x in range(1000)]


class RVScreen(Screen):
    pass


class ScreenManagerApp(App):

    def build(self):
        root = ScreenManager()
        # root.add_widget(CustomScreen(name='CustomScreen'))
        root.add_widget(RVScreen(name='RVScreen'))
        return root


if __name__ == '__main__':
    ScreenManagerApp().run()
