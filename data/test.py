from kivy.animation import Animation
from kivy.properties import ColorProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.lang import Builder
from kivymd.app import MDApp
import json

from kivymd.uix.menu import MDDropdownMenu

from Package import jut_su_parse as j_parse
from math import ceil
from kivymd.uix.snackbar import Snackbar
from kivymd.theming import ThemeManager
from kivy.metrics import dp

Builder.load_file("../kv/start_window.kv")
BUTTON_HEIGHT = 50
series_dict = {}
anime_dict = {}


def write_json(file_name: str, value: dict):
    with open(f'{file_name}', 'w', encoding='utf-8') as f:
        json.dump(value, fp=f, ensure_ascii=False, indent=4)


def load_json(file_name: str):
    with open(f'{file_name}', encoding='utf-8') as f:
        value = json.load(f)
    return value


def bad_link():
    Snackbar(text="Вставьте корректную ссылку!",
             snackbar_x="20dp",
             snackbar_y="20dp",
             size_hint_x=(Window.width - 40) / Window.width).open()


class Main(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @j_parse.check_time("main", "on enter")
    def on_enter(self):
        global anime_dict
        anime_dict = load_json('anime_list.json')
        b_height = len(anime_dict['film_list']) * BUTTON_HEIGHT
        self.ids.favourites_list.height = b_height
        for i in anime_dict['film_list']:
            b_height -= BUTTON_HEIGHT
            self.ids.favourites_list.add_widget(
                Button(text=str(i['name']), on_press=self.pressing, size_hint=(1, None),
                       height=BUTTON_HEIGHT - 2, pos=(0, b_height)))

    def pressing(self, instance):
        global series_dict
        for i in anime_dict['film_list']:
            if i['name'] == instance.text:
                data = j_parse.main(i['link'])
                if data:
                    series_dict = data
                    self.manager.transition.direction = 'left'
                    self.manager.current = 'second'
                else:
                    bad_link()

    @j_parse.check_time("check for link")
    def find_by_link(self):
        global series_dict
        a = j_parse.main(self.ids.input_name.text)
        if a:
            series_dict = a
            self.manager.current = 'second'
        else:
            bad_link()


class Second(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.series_count = []
        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": "Скачать всё",
                "height": dp(56),
                "on_release": lambda x="Скачать всё": self.menu_callback(x)
            },
            {
                "viewclass": "OneLineListItem",
                "text": "Настройки",
                "height": dp(56),
                "on_release": lambda x="Настройки": self.menu_callback(x)
            }
        ]
        self.menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )

    def on_enter(self):
        self.ids.ani.title = series_dict["name"]
        series_count = list(series_dict.keys())[5:]
        b_height = len(series_count) * BUTTON_HEIGHT
        self.ids.season_list.height = b_height
        for i in series_count:
            name = series_dict[i]['name']
            b_height -= BUTTON_HEIGHT
            self.ids.season_list.add_widget(
                Button(text=name, on_press=self.pressing, size_hint=(1, None),
                       height=BUTTON_HEIGHT - 2, pos=(0, b_height)))

        temp_dict = {"name": series_dict['name'],
                     "link": series_dict['link'],
                     "last_series": series_dict['last_series']}
        if temp_dict in anime_dict['film_list']:
            self.ids.ani.right_action_items = [["star-off-outline", lambda x: self.add_favourite()],
                                               ["dots-vertical", lambda x: self.callback(x)]]
        else:
            self.ids.ani.right_action_items = [["star-outline", lambda x: self.add_favourite()],
                                               ["dots-vertical", lambda x: self.callback(x)]]

    def pressing(self, instance):
        global series_dict
        if self.manager.current != 'Second':
            series_dict["select_season"] = instance.text
            self.manager.transition.direction = 'left'
            if len(series_dict[instance.text]['series'].keys()) > 50:
                self.manager.current = 'fourth'
            else:
                self.manager.current = self.manager.next()

    def on_leave(self):
        self.ids.season_list.clear_widgets()
        self.ids.ani.title = ''

    def set_previous_screen(self):
        if self.manager.current != 'Main':
            self.manager.transition.direction = 'right'
            self.manager.current = self.manager.previous()

    def add_favourite(self):
        temp_dict = {"name": series_dict['name'],
                     "link": series_dict['link'],
                     "last_series": series_dict['last_series']}

        if self.ids.ani.right_action_items[0][0] == "star-outline":
            anime_dict['film_list'].append(temp_dict)
            self.ids.ani.right_action_items = [["star-off-outline", lambda x: self.add_favourite()],
                                               ["dots-vertical", lambda x: x]]

        else:
            anime_dict['film_list'].remove(temp_dict)
            self.ids.ani.right_action_items = [["star-outline", lambda x: self.add_favourite()],
                                               ["dots-vertical", lambda x: x]]
        write_json('anime_list.json', anime_dict)

    def callback(self, button):
        self.menu.caller = button
        self.menu.open()

    def menu_callback(self, text_item: str):
        self.menu.dismiss()
        print(text_item)


class Third(Screen):
    overlay_color = ColorProperty("#5b5b5b")
    default_color = ColorProperty("#808080")
    progress_round_color = "#bcbcbc"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.season = {}
        self.series_name = ""
        self.selection_series = []
        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": "Скачать всё",
                "height": dp(56),
                "on_release": lambda x="Скачать всё": self.select_all(x)
            },
            {
                "viewclass": "OneLineListItem",
                "text": "Выбрать серии",
                "height": dp(56),
                "on_release": lambda x="Выбрать серии": self.menu_callback(x)
            }
        ]
        self.menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )

    @j_parse.check_time('third enter')
    def on_enter(self, *args):
        select_season = None
        self.ids.ani.title = series_dict['select_season']
        series_list = list(series_dict.keys())[5:]
        for season in series_list:
            if series_dict['select_season'] == series_dict[season]['name']:
                select_season = series_dict[season]['series']

        b_height = ceil((len(select_season)/4)) * BUTTON_HEIGHT
        self.ids.series_list.height = b_height + 5
        for series in select_season:
            if len(series) > 29 and self.ids.series_list.cols != 1:
                self.ids.series_list.cols = 1
            b_height -= BUTTON_HEIGHT
            self.ids.series_list.add_widget(Button(text=series, on_release=self.pressing, size_hint=(1, None),
                                                   height=BUTTON_HEIGHT))

    def set_previous_screen(self):
        if self.manager.current != 'second':
            self.manager.transition.direction = 'right'
            self.manager.current = self.manager.previous()

    def pressing(self, instance):
        global series_dict
        if self.manager.current != 'Second':
            series_dict["select_series"] = instance.text
            self.manager.transition.direction = 'left'

    def on_leave(self):
        self.ids.series_list.clear_widgets()
        self.ids.ani.title = ''

    def download(self, link_list):
        s = [i.instance_item.text for i in self.selection_series]
        print(s)

    def select_all(self, item):
        self.ids.series_list.selected_all()
        self.menu.dismiss()

    def callback(self, button):
        self.menu.caller = button
        self.menu.open()

    def menu_callback(self, text_item):
        self.menu.dismiss()
        print(text_item)

    def set_selection_mode(self, instance_selection_list, mode):
        if mode:
            md_bg_color = self.overlay_color
            left_action_items = [
                [
                    "close",
                    lambda x: self.ids.series_list.unselected_all(),
                ]
            ]
            right_action_items = [["download", lambda x: self.download(x)], ["dots-vertical"]]
        else:
            md_bg_color = self.default_color
            left_action_items = [["arrow-left", lambda x: self.set_previous_screen()]]
            right_action_items = [["magnify", lambda x: self.download(x)],
                                  ["dots-vertical", lambda x: self.callback(x)]]
            self.ids.ani.title = series_dict['select_season']

        Animation(md_bg_color=md_bg_color, d=.5).start(self.ids.ani)
        self.ids.ani.left_action_items = left_action_items
        self.ids.ani.right_action_items = right_action_items

    def on_selected(self, instance_selection_list, instance_selection_item):
        self.ids.ani.title = str(
            len(instance_selection_list.get_selected_list_items())
        )
        self.selection_series = instance_selection_list.get_selected_list_items()

    def on_unselected(self, instance_selection_list, instance_selection_item):
        if instance_selection_list.get_selected_list_items():
            self.ids.ani.title = str(
                len(instance_selection_list.get_selected_list_items())
            )


class Fourth(Screen):  # Для примера. Нужно переделать
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.list_buttons = [
            '7', '8', '9',
            '4', '5', '6',
            '1', '2', '3',
            'None', '0', 'None',
        ]
        for i in self.list_buttons:
            self.ids.this_layout.add_widget(Button(text=i, on_press=self.pressing))

    def pressing(self, instance):
        self.manager.current = 'first'


class TestApp(MDApp):

    def __init__(self, **kwargs):
        self.theme_cls = ThemeManager()
        self.title = "Jut.su"
        self.icon = "../Sources/favicon.ico"
        super().__init__(**kwargs)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        sm = ScreenManager()
        sm.add_widget(Main(name='first'))
        sm.add_widget(Second(name='second'))
        sm.add_widget(Third(name='third'))
        sm.add_widget(Fourth(name='fourth'))
        return sm


if __name__ == "__main__":
    TestApp().run()
