import json
import os.path
import re
from datetime import datetime
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup
from loguru import logger

links = {}
down_links = []
headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/99.0.4844.84 Safari/537.36 OPR/85.0.4341.79"}


def write_json(file_name: str, value: dict):
    with open(f'{file_name}', 'w', encoding='utf-8') as f:
        json.dump(value, fp=f, ensure_ascii=False, indent=4)


def check_time(*a_args: str) -> any:
    def name_func(func):
        def wrapper(*args, **kwargs):
            start = datetime.now()
            result = func(*args, **kwargs)
            print(f'Функция "{" ".join(a_args)}" отработала за: {datetime.now() - start}')
            return result

        return wrapper

    return name_func


def check_anime_global(link: str) -> Tuple[BeautifulSoup, bool]:
    anime_global = False
    links.clear()
    req = requests.get(link, headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    all_anime_global = soup.find_all('div', class_='all_anime_global')

    if not all_anime_global:
        name = soup.find('h1', class_='header_video allanimevideo anime_padding_for_title').text \
            .replace('Смотреть ', '').replace(' все серии и сезоны', '').replace(' все серии', '')
    else:
        name = soup.find('h1', class_='mail_h').text.replace('Все серии аниме ', '')
        anime_global = True

    links.update({"link": link, "last_series": "", "select_series": "", "select_season": "", "name": name})
    return soup, anime_global


def get_episodes(soup: BeautifulSoup, anime_global: bool) -> Optional[dict]:
    """
    # Аниме_глобал - это Наруто. Мб найду что-то ещё.
    # По умолчанию False. В данном случае на одной странице все ссылки на серии.
    # Парсим именно их
    """
    if not anime_global:
        try:
            episodes = soup.findAll('a', class_="short-btn")
            # Список сезонов на русском
            season_titles = [i.text for i in soup.find_all('h2', class_="the-anime-season")]

        # Если сезонов нет или что-то пошло не так - возвращаем ничего
        except requests.exceptions.MissingSchema:
            return None

        # Парсим эпизоды, они же кнопки серии.
        for i in episodes:
            # Собирает все серии со страницы
            episode_title = re.search(r'\d+\s+\w+$', i.text).group()
            link_episode = i['href']
            if "https://jut.su" not in link_episode:
                link_episode = "https://jut.su" + link_episode

            if re.search(r'season+-\d+', link_episode):
                season = re.search(r'season+-\d+', link_episode).group()
                # Находим номер сезона для серии
                season_title = int(re.search(r'\d+', season).group())
                if season_titles[season_title - 1] not in links.keys():
                    # Минус 1, т.к. s_title - это номер сезона s_titles же - список сезонов.
                    # Чтобы найти нужный - вычитаем 1, т.к. отсчёт идёт с нуля.
                    links.update(
                        {season_titles[season_title - 1]: {"name": season_titles[season_title - 1], 'series': {}}})
                links[season_titles[season_title - 1]]['series'].update({episode_title: link_episode})

            elif re.search(r'film-\d+', link_episode):
                if season_titles[-1] not in links.keys():
                    links.update({season_titles[-1]: {"name": season_titles[-1], 'series': {}}})
                links[season_titles[-1]]['series'].update({episode_title: link_episode})
            else:
                if "Все серии" not in links.keys():
                    links.update({'Все серии': {"name": "Все серии", "series": {}}})
                links['Все серии']['series'].update({episode_title: link_episode})

    else:
        seasons = soup.find_all('div', class_='all_anime_global')
        for season_global in seasons:
            season_title = season_global.find('div', class_='aaname').text \
                .replace(season_global.find('span', class_='the_invis').text, '')
            link = season_global.find('a', href=True)['href']
            if "https://jut.su" not in link:
                link = "https://jut.su" + link
            links.update({season_title: {"name": season_title, "series": {}}})
            req = requests.get(link, headers=headers)
            soup = BeautifulSoup(req.content, 'html.parser')
            episodes = soup.findAll('a', class_="short-btn")
            if not episodes:
                ova_data = soup.find('div', class_='watch_list_item').find_all('a', href=True)
                for i in ova_data:
                    # Собирает все серии со страницы
                    link_episode = i['href']
                    if "https://jut.su" not in link_episode:
                        link_episode = "https://jut.su" + link_episode
                    links[season_title]['series'].update({i.text: link_episode})

            for i in episodes:
                # Собирает все серии со страницы
                episode_title = re.search(r'\d+\s+\w+$', i.text).group()
                link_episode = i['href']
                if "https://jut.su" not in link_episode:
                    link_episode = "https://jut.su" + link_episode
                links[season_title]['series'].update({episode_title: link_episode})
        return links

    if not links:
        return None
    else:
        return links


def get_download_link(link: str) -> str or None:
    req1 = requests.get(link, headers=headers)
    soup = BeautifulSoup(req1.content, 'html.parser')
    try:
        if soup.find("source", attrs={"label": "720p"}).get('src'):
            download_link = soup.find("source", attrs={"label": "720p"}).get('src')
        elif soup.find("source", attrs={"label": "480p"}).get('src'):
            download_link = soup.find("source", attrs={"label": "480p"}).get('src')
        elif soup.find("source", attrs={"label": "360p"}).get('src'):
            download_link = soup.find("source", attrs={"label": "360p"}).get('src')
        else:
            # exit()
            return None
    except AttributeError:
        return None

    return download_link


@logger.catch
def dwn(video: list, path: list):
    # logger.info(video)
    if isinstance(video, list):
        for link, names in zip(video, path):
            if not download_list_of_series(link, names):
                download_list_of_series(link, names)
    logger.info(f"Успешно загружены серии - {path}")


def get_file_size(link: str) -> int:
    return int(requests.get(link, stream=True, headers=headers).headers['Content-Length'])


def download_list_of_series(link: str, name: str):
    try:
        session = requests.Session()
        d_video = session.get(link, stream=True, headers=headers)
        d_video.raise_for_status()
        f = open(f'{name}.mp4', 'wb')
        file_size = int(d_video.headers['Content-Length'])
        last = file_size
        logger.info(f"Начинаем загрузку файла - {name}.mp4. Размер файла - {str(file_size / 1000000)} МБ")
        t = datetime.now()
        for chunk in d_video.iter_content(chunk_size=1024):  # chunk_size=8192
            f.write(chunk)
            last -= len(chunk)
        f.close()
        logger.debug("Время загрузки: " + str(datetime.now() - t))
        if file_size == os.path.getsize(name + ".mp4"):
            logger.info(f"Файл успешно загружен - {name}.mp4")
            return True
        else:
            logger.warning(f"Файл загружен не полностью. Не загрузилось {file_size - os.path.getsize(name + '.mp4')}")
            return False
    except ConnectionAbortedError:
        logger.warning("ConnectionAbortedError")
        return False

    except requests.exceptions.ChunkedEncodingError:
        logger.warning("ChunkedEncodingError")
        return False

    except requests.exceptions.HTTPError:
        logger.warning("requests.exceptions.HTTPError")
        return False

    except FileNotFoundError:
        logger.warning("FileNotFoundError")
        return False


def main(start_link: str = None) -> Optional[dict]:
    if re.fullmatch(r'https://jut\.su/.+/', start_link):
        soup, a_global = check_anime_global(start_link)
        if not get_episodes(soup, a_global):
            return None
    elif re.fullmatch(r'https://jut\.su/.+/(episode|film).+', start_link):
        soup, a_global = check_anime_global(re.search(r'https://jut\.su/[^/]+/', start_link).group())
        if not get_episodes(soup, a_global):
            return None
    else:
        return None

    return links


if __name__ == '__main__':
    main()
