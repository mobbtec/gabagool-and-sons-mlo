# Gabagool and Sons

Редактируемый интерьер LONG PIG для FiveM в районе Rancho. В магазине есть торговый зал, прилавок деликатесов, табачная витрина, кухня, служебные помещения и режим After Hours. Имя ресурса — `gabagool_sons_mlo`.

## Где что редактировать

| Часть проекта | Исходник |
| --- | --- |
| Основная сцена интерьера | [gs_prototype_mlo.blend](source/blender/prototype/gs_prototype_mlo.blend) |
| Интерактивный реквизит | [lp_props.blend](source/blender/props/lp_props.blend) |
| Металлические ставни | [lp_shutters.blend](source/blender/shutters/lp_shutters.blend) |
| Группы марок, шаг пачек и лотки | [gs_v302_shelf.py](source/scripts/gs_v302_shelf.py) |
| Отделка холодильника и следы износа на стене | [gs_v302_finish.py](source/scripts/gs_v302_finish.py) |
| Дневной и ночной свет | [lp_timecycle.xml](source/fivem/gabagool_sons_mlo/lp_timecycle.xml) и [night.lua](source/fivem/gabagool_sons_mlo/client/night.lua) |
| Клиентские и серверные скрипты, звуки и настройки | [source/fivem](source/fivem/gabagool_sons_mlo) |
| Текстуры, атласы и исходные звуки | [source/textures](source/textures) и [source/audio](source/audio) |

Сцены Blender можно открыть сразу после распаковки проекта. Для изменений, которые должны попасть в следующую автоматическую сборку, правьте генераторы в [source/scripts](source/scripts). Сборщик заново создаёт сцены и экспортирует их с помощью Sollumz. После экспорта скрипты в [tools](tools) очищают геометрию и слоты материалов и выставляют зазор у оконной рамы.

## Собрать и установить

Понадобятся Python 3.10+, Blender 5.1 с Sollumz и нативным экспортом Gen8, а также установленная GTA V Legacy. Укажите путь к игре и свободную папку вывода.

```powershell
py tools/build.py --gta "D:/Games/GTAV" --blender "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe" --output "./out/3.0.2"
```

Скопируйте полученную папку `out/3.0.2/gabagool_sons_mlo` в ресурсы сервера и добавьте `ensure gabagool_sons_mlo` в `server.cfg`. В полном архиве релиза также есть исходные загрузки материалов CC0 для повторной обработки текстур. [Подробности сборки](BUILD.md) · [Релиз 3.0.2](https://github.com/mobbtec/gabagool-and-sons-mlo/releases/tag/v3.0.2)

## Версия 3.0.2

Свет в зале немного ярче днём и ночью. На табачной витрине семь рядов по десять пачек, сгруппированных по маркам. Исправлены наложения панелей кабинок и кожуха холодильника. У мелких товаров сокращена дальность отрисовки, а из четырёх моделей удалены неиспользуемые слоты материалов.

Сборка проверена офлайн на GTA V Legacy. Проверки охватывают 85 файлов ресурса, 30 моделей YDR, пять порталов и положение пачек на полках. Замеры FPS и проверка света в клиенте FiveM остаются открытыми. [Отчёты](docs/qa)

## Лицензии

Авторская часть опубликована под MIT. Материалы ambientCG и Poly Haven имеют лицензию CC0. Игровые файлы для квартала сборщик получает из локальной копии GTA V Legacy. [MIT](LICENSE) · [Авторы и происхождение ассетов](assets/CREDITS.md)
