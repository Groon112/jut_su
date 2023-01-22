import json
import os
import threading

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivymd.uix.behaviors.focus_behavior import FocusBehavior
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.recyclegridlayout import MDRecycleGridLayout
from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.snackbar import Snackbar
from loguru import logger

from Package import jut_su_parse as j_parse

Builder.load_file("kv/start_window.kv")
BUTTON_HEIGHT = 50
series_dict = {}
anime_dict = {}
select_series = []
platform_path = ""
download_dir = ""

if platform == "android":
    from android.permissions import Permission, request_permissions

    def callback(permission, result):
        if all([res for res in result]):
            logger.info(f"Got all permissions - {permission}")
        else:
            logger.info(f"Did not get all permissions - {permission}")

    request_permissions([Permission.READ_EXTERNAL_STORAGE,
                         Permission.WRITE_EXTERNAL_STORAGE,
                         Permission.INTERNET], callback)

    platform_path = "/data/data/org.jut.su.download.jutsu/files/app/"
    BUTTON_HEIGHT = 120
    download_dir = "/storage/emulated/0/Movies/JutSu/"


elif platform == "linux":
    download_dir = "/home/groon/Видео/JutSu/"

else:
    download_dir = "C:/JutSu/"

if not os.path.exists(download_dir):
    os.makedirs(download_dir)

logger.add(download_dir + "debug.log", format="{time} {level} {message}", level="DEBUG", rotation="100 MB")


def write_json(file_name: str, value: dict):
    with open(f'{file_name}', 'w', encoding='utf-8') as f:
        json.dump(value, fp=f, ensure_ascii=False, indent=4)


def load_json(file_name: str):
    with open(f'{file_name}', encoding='utf-8') as f:
        value = json.load(f)
    return value


def bad_link(text: str):
    logger.warning(text)
    Snackbar(text=text,
             snackbar_x="20dp",
             snackbar_y="20dp",
             size_hint_x=(Window.width - (dp(20) * 2)) / Window.width).open()


class Main(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        logger.info("Открылся main screen")
        global anime_dict
        anime_dict = load_json(platform_path + 'data/anime_list.json')
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
            try:
                if i['name'] == instance.text:
                    data = j_parse.main(i['link'])
                    if data:
                        series_dict = data
                        self.manager.transition.direction = 'left'
                        self.manager.current = 'second'
                    else:
                        bad_link("Введите корректную ссылку!")
            except Exception as e:
                logger.exception(e)

    def find_by_link(self):
        global series_dict
        a = j_parse.main(self.ids.input_name.text)
        if a:
            series_dict = a
            self.manager.current = 'second'
        else:
            bad_link("Введите корректную ссылку!")


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
            self.manager.current = 'RVScreen'

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
        write_json(platform_path + 'data/anime_list.json', anime_dict)

    def callback(self, button):
        self.menu.caller = button
        self.menu.open()

    def menu_callback(self, text_item: str):
        self.menu.dismiss()


class CustomButton(Button):
    root_widget = ObjectProperty()

    def on_release(self, **kwargs):
        super(CustomButton, self).on_release()
        self.root_widget.select_series(self.text)


class ScrollerSeries(MDRecycleView):
    def __init__(self, **kwargs):
        super(ScrollerSeries, self).__init__(**kwargs)

    def refreshView(self):
        select_season = None
        series_list = list(series_dict.keys())[5:]
        for season in series_list:
            if series_dict['select_season'] == series_dict[season]['name']:
                select_season = series_dict[season]['series']
        self.data = [{"text": series, "root_widget": self} for series in select_season]

    def select_series(self, text):
        pass


class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
                                  MDRecycleGridLayout):
    """ Adds selection and focus behaviour to the view. """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid = None
        self.select_series = None

    def on_selected_nodes(self, grid, nodes):
        global select_series
        select_series = nodes

    def clear(self):
        ss = select_series.copy()
        for i in ss:
            self.deselect_node(i)
        self.clear_selection()
        self.selected_nodes = []


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

        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """ Respond to the selection of items in the view. """
        self.selected = is_selected


class RV(MDRecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def refreshView(self):
        select_season = None
        series_list = list(series_dict.keys())[5:]
        for season in series_list:
            if series_dict['select_season'] == series_dict[season]['name']:
                select_season = series_dict[season]['series']
        self.data = [{"text": series} for series in select_season]

    def clear(self):
        self.ids.scroll_rec_grid_lay.clear()
        self.scroll_y = 1


class RVScreen(Screen):

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
                "text": "Скачать выбранные",
                "height": dp(56),
                "on_release": lambda x="Выбрать серии": self.menu_callback(x)
            }
        ]
        self.menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )

    def on_enter(self, *args):
        self.ids.ani.title = series_dict['select_season']
        self.ids.series_list.refreshView()

    def on_leave(self, *args):
        self.ids.series_list.clear()
        pass

    def menu_callback(self, text_item):
        global select_series
        select_season = None
        series_list = list(series_dict.keys())[5:]
        for season in series_list:
            if series_dict['select_season'] == series_dict[season]['name']:
                select_season = series_dict[season]['series']
        select_series_with_name = ([list(select_season.keys())[int(x)] for x in select_series])
        threading.Thread(target=self.download_series, args=(select_season, select_series_with_name)).start()
        self.menu.dismiss()

    def download_series(self, select_season: dict, select_series_name: list):
        link = []
        name = []
        bad_series = []
        self.ids.p_bar.value = 0
        for series in select_series_name:
            download_link = j_parse.get_download_link(select_season[series])
            if download_link:
                # logger.info(f"Серия - {series}. Download link - {download_link}")
                link.append(download_link)
                name.append(f"{download_dir}{series_dict['name']} {series_dict['select_season']} {series}")
            else:
                logger.error(f"Не удалось получить ссылку на скачивание - {select_season[series]}")
                bad_series.append(series)

        if bad_series and not name and not link:
            logger.warning("Не удалось получить ссылки на скачивание.")
            return
        elif bad_series and name and link:
            logger.warning(f"Не удалось получить ссылки: {'; '.join(bad_series)}")

        logger.info(f"Начало загрузки серий - {name}")
        # _time = datetime.now()
        #
        # _size = 0
        # for i, l in enumerate(link):
        #     one_size = j_parse.get_file_size(l)
        #     # print(f"{i}:  {str(one_size/1000000)} Мб")
        #     _size += one_size
        # print(f"Общий размер: {str(_size/1000000)} Мб")
        #
        # print(datetime.now() - _time)
        j_parse.dwn(link, name)

    def select_all(self, item):
        self.menu.dismiss()

    def callback(self, button):
        self.menu.caller = button
        self.menu.open()

    def set_previous_screen(self):
        if self.manager.current != 'third':
            self.manager.transition.direction = 'right'
            self.manager.current = 'second'


class TestApp(MDApp):

    def __init__(self, **kwargs):
        self.theme_cls = ThemeManager()
        self.title = "Jut.su"
        self.icon = "Sources/favicon.ico"
        super().__init__(**kwargs)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        sm = ScreenManager()
        sm.add_widget(Main(name='first'))
        sm.add_widget(Second(name='second'))
        sm.add_widget(RVScreen(name='RVScreen'))
        return sm


if __name__ == "__main__":
    logger.info("Приложение запустилось")
    TestApp().run()
