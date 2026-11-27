from pathlib import Path
import json, html, csv, shutil

ROOT=Path('C:/Users/sgkomc/Documents/Persona/output/Taktera_Brand_Package_v3.2')
DOC=ROOT/'10_documentation'
DOC.mkdir(exist_ok=True)
tokens=json.loads((ROOT/'04_tokens/taktera.tokens.json').read_text(encoding='utf-8'))
chapters=[]

class Chapter:
    def __init__(self, slug, title):
        self.slug,self.title=slug,title
        self.md=[f'# {title}\n\nTaktera · редакция 3.2 · 18 октября 2026\n']
        self.ht=[f'<h2>{html.escape(title)}</h2>']
    def p(self,s):
        self.md.append(s+'\n'); self.ht.append('<p>'+html.escape(s)+'</p>')
    def h(self,s):
        self.md.append('## '+s+'\n'); self.ht.append('<h3>'+html.escape(s)+'</h3>')
    def li(self,items):
        self.md.append('\n'.join('- '+x for x in items)+'\n')
        self.ht.append('<ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in items)+'</ul>')
    def table(self,heads,rows):
        self.md.append('| '+' | '.join(heads)+' |\n| '+' | '.join('---' for _ in heads)+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n')
        self.ht.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+html.escape(h)+'</th>' for h in heads)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>')
    def code(self,s,lang=''):
        self.md.append('```'+lang+'\n'+s+'\n```\n'); self.ht.append('<pre><code>'+html.escape(s)+'</code></pre>')
    def save(self):
        (DOC/(self.slug+'.md')).write_text('\n'.join(self.md),encoding='utf-8'); chapters.append(self)

c=Chapter('01-brand-decisions','01. Основа бренда и принятые решения')
c.p('Taktera — единый бренд платформы и продуктовых направлений. Узнаваемость создают постоянная форма знака, отдельная точка, единая типографика и спокойная нейтральная основа. Цвет помогает различать продукты.')
c.h('Что закреплено')
c.li(['Используется силуэт из последнего выбранного макета exec-2c59ddad-28a1-490b-bddb-32688ba23231.png. На изображении он подписан «03 / Ясная T». Ориентир — форма из этого файла.', 'Основной знак всегда чёрный #000000 на светлом фоне или белый #FFFFFF на тёмном.', 'В продуктовой композиции точка и название направления имеют один акцентный цвет. Английские подписи: platform, clinic, beauty, spa, fitness, travel. Русские: taktera платформа, taktera клиника, taktera красота, taktera спа, taktera фитнес, taktera путешествия.', 'Fitness — красный; Travel — жёлтый. Остальная палитра сохранена.', 'В корпоративной композиции подпись taktera чёрная или белая, точка использует цвет Platform.', 'В одноцветной печати допустима вся композиция чёрным или белым.'])
c.h('Архитектура и написание')
c.table(['Контекст','Форма'],[['Бренд в обычном тексте','Taktera'],['Названия продуктов в обычном тексте','Taktera Platform, Taktera Clinic, Taktera Beauty, Taktera Spa, Taktera Fitness, Taktera Travel'],['Корпоративный логотип','Фирменный знак + точка + taktera'],['Продуктовый логотип EN','Фирменный знак + точка + строчное имя направления'],['Продуктовый логотип RU','Фирменный знак + точка + taktera + русское имя направления'],['Ссылка на продукт','Фактический адрес сайта; запись Taktera.clinic не подтверждает регистрацию домена']])
c.p('Точка — часть фирменного знака. Её не дублируют после названия. Английская краткая версия содержит имя направления; русская полная версия содержит taktera и русское имя направления. В русской версии taktera чёрное или белое, направление цветное. В интерфейсе выбора продукта название показывают явно: цвет не должен быть единственным отличием.')
c.h('Приоритет материалов')
c.p('Последние решения пользователя определяют направление. Для производства используются актуальный брендбук 3.2, SVG-мастера и токены из этого комплекта. При расхождении материалов исправляют весь комплект, а не создают локальную вариацию. Каталог 08_reference содержит историю и источник формы; его материалы не служат готовыми ресурсами для внедрения.')
c.p('Nexus, «Собранная T» и варианты с обычной симметричной заглавной T не являются текущим мастер-знаком. Название концепции не используется как самостоятельное имя продукта.')
c.h('Статус комплекта')
c.p('Визуальная система и ресурсы подготовлены для передачи команде. Вектор оптически восстановлен по растровому образцу. Код приложений в этой работе не изменён. Брендбук не является заключением о регистрации или охраноспособности товарного знака.')
c.save()

c=Chapter('02-logo-standard','02. Логотип: конструкция и применение')
c.p('Готовые SVG — основной источник для макетов и разработки. Буквы переведены в контуры; установленный шрифт не требуется. PNG предназначены для сред, где SVG не поддерживается.')
c.table(['Параметр','Значение'],[['Рабочая область знака','88 × 74'],['Контур','M12 16H29Q49 16 49 36V58'],['Толщина штриха','20 единиц'],['Окончания и соединения','round'],['Центр точки','75, 15'],['Радиус точки','10 единиц'],['Охранное поле','Минимум один диаметр точки со всех сторон всей композиции']])
c.p('Левое горизонтальное плечо плавно переходит в вертикальную стойку справа. Правое плечо не добавляют. Точку не сдвигают относительно знака. Охранное поле добавляют в макете: внутренние поля SVG его не заменяют. При масштабе s относительно viewBox охранное поле составляет 20 × s.')
c.h('Минимальные размеры')
c.table(['Применение','Минимум'],[['Favicon','16 px; готовый экспорт из 03_icons'],['Знак в интерфейсе','24 px по ширине'],['Полная композиция EN','180 px по ширине'],['Полная композиция RU','280 px по ширине'],['Композиция EN в печати','35 мм по ширине'],['Композиция RU в печати','55 мм по ширине']])
c.p('Если композиция не помещается, используют знак с доступным текстовым названием рядом либо полное название в другом элементе навигации. Подпись нельзя уменьшать до нечитаемого размера. Для app icon охранное поле и масштаб уже заданы в готовом квадратном файле.')
c.h('Фон и версии')
c.li(['Суффикс light означает ресурс для светлого фона: чёрный знак. dark — для тёмного: белый знак.', 'На фотографии или неоднородном фоне используйте спокойную однотонную область, сохранив охранное поле.', 'Прозрачный логотип находится в 02_logos. Иконка с собственной подложкой — в 03_icons/app. Эти ресурсы имеют разные назначения.', 'Для монохромного производства используйте готовые mark-mono-light / mark-mono-dark. Полную композицию при необходимости переводят целиком в чёрный или белый, сохраняя контуры.'])
c.h('Недопустимые изменения')
c.li(['Окрашивать основной знак продуктовым акцентом.', 'Растягивать по одной оси, поворачивать, менять толщину, диаметр или положение точки.', 'Перенабирать подпись другим шрифтом либо вручную менять интервалы.', 'Добавлять градиент, свечение, обводку, объём или тень внутрь логотипа.', 'Заменять знак зубом, цветком, гантелью, самолётом или обычной буквой T.', 'Использовать разные цвета для точки и продуктового названия в одной композиции.'])
c.save()

def luminance(h):
    v=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v]
    return sum(x*y for x,y in zip(v,[.2126,.7152,.0722]))
def contrast(a,b):
    x,y=sorted([luminance(a),luminance(b)]); return (y+.05)/(x+.05)

c=Chapter('03-color-and-themes','03. Палитра, темы и читаемость')
c.p('Акценты рассчитаны для двух тем. Цвета в таблице — точные значения sRGB/HEX. Для светлой и тёмной темы берут соответствующие готовые ресурсы и токены.')
c.table(['Продукт','Акцент / светлая','Акцент / тёмная','Текст светлой кнопки','UI-текст / светлая'],[[k.title(),v['accentLight'],v['accentDark'],v['onAccentLight'],v['uiTextLight']] for k,v in tokens['products'].items()])
c.h('Роли цвета')
c.table(['Роль','CSS-токен','Правило'],[['Основной знак','--tk-mark','Только #000000 или #FFFFFF'],['Точка и продуктовая подпись','--tk-accent','Один цвет для обеих частей'],['Основное действие','--tk-accent + --tk-on-accent','Проверенная пара фона и текста'],['Мелкие ссылки и текстовые акценты','--tk-accent-text','У Travel на светлом фоне #806300'],['Холст','--tk-canvas','#F4F3EF / #151719'],['Поверхность','--tk-surface','#FFFFFF / #22262B'],['Основной текст','--tk-text','#22262B / #F4F3EF']])
c.p('В тёмной теме текст на всех акцентных кнопках — #151719. В светлой теме текст кнопки Travel — #151719, у остальных продуктов — #FFFFFF. Не переносите белый текст с кнопки Fitness на жёлтую кнопку Travel.')
c.p('Жёлтый #D4A600 сохраняется в логотипе Travel. Для мелкого интерфейсного текста на светлом фоне используется #806300. Это разные роли, а не разные варианты фирменного логотипа.')
c.h('Расчётные пары')
c.p('Ниже приведён расчёт относительной яркости для непрозрачных цветов sRGB. Для обычного мелкого UI-текста в этом руководстве принят порог 4,5:1. Числа относятся только к указанным парам; прозрачность, другой фон и состояния проверяются отдельно.')
contrast_rows=[]
for k,v in tokens['products'].items():
    contrast_rows.append([k.title(),f"{contrast(v['accentLight'],v['onAccentLight']):.2f}",f"{contrast(v['uiTextLight'],'#FFFFFF'):.2f}",f"{contrast(v['uiTextLight'],'#F4F3EF'):.2f}",f"{contrast(v['uiTextDark'],'#151719'):.2f}"])
c.table(['Продукт','Светлая кнопка','UI-текст / белый','UI-текст / paper','UI-текст / тёмный'],contrast_rows)
c.p('У Spa и Fitness мелкий акцентный текст на paper #F4F3EF не достигает принятого порога 4,5:1: соответственно 4,13:1 и 4,48:1. На этом фоне используйте основной нейтральный текст; цветную ссылку располагайте на белой поверхности. У Beauty запас на paper небольшой: не снижайте непрозрачность текста. Ярко-жёлтый акцент Travel не используется для мелкого текста на белом.')
c.h('Семантика и состояния')
c.li(['Фирменный красный Fitness обозначает продукт, а ошибка обозначается отдельным семантическим токеном, сообщением и при необходимости иконкой.', 'Жёлтый Travel не является автоматическим цветом предупреждения.', 'Акцент допустим для основного действия, выбранного пункта и фокуса. Большие рабочие поверхности, таблицы и расписания остаются нейтральными.', 'Hover, pressed, disabled, ошибки, успех, графики и календарные категории не имеют полной палитры в этом пакете. Их значения задаются и проверяются в библиотеке компонентов; случайные оттенки не объявляются фирменными.', 'Для графиков и выбора продукта используйте подписи, маркеры или паттерны вместе с цветом.'])
c.save()

c=Chapter('04-type-ui-and-content','04. Типографика, интерфейс и тексты')
c.h('Шрифты')
c.p('Основной шрифт — Inter. В комплекте есть статические начертания Regular 400, SemiBold 600 и Bold 700, исходный variable TTF и OFL.txt. Для статических файлов использована оптическая ось opsz 24. Не подключайте variable и статические файлы одновременно под одним именем без явной схемы начертаний.')
c.table(['Роль','Размер / интерлиньяж, px','Начертание'],[['Крупный заголовок','48 / 52','700'],['H1','30 / 36','700'],['H2','24 / 30','600'],['H3','18 / 24','600'],['Основной текст','14 / 21','400'],['Подпись','12 / 16','400']])
c.p('Логотипы используют контуры Inter Bold с фиксированными интервалами. Для таблиц, сумм и счётчиков включают tabular-nums. Для ID и кода допускается JetBrains Mono, если он уже подключён в продукте; иначе системный monospace. JetBrains Mono в комплект не включён.')
c.h('Общие параметры UI')
c.table(['Параметр','Правило'],[['Ритм','Отступы кратны 4 px'],['Радиусы','4 / 6 / 8 / 12 / 16 px'],['Движение','150 / 250 / 400 ms; учитывать prefers-reduced-motion'],['Пиктограммы','Lucide, currentColor, линия 1.5 px'],['Размеры пиктограмм','16 / 20 / 24 / 32 px'],['Область нажатия','Рекомендуется 44 × 44 px для touch; минимум 32 × 32 px для компактного desktop']])
c.p('Рекомендуемый подход к композиции: ясная иерархия, свободные поля, минимум теней. Цвет выделяет действие и продукт, а не всю страницу. Декоративный изгиб и точка уместны на обложке; их не помещают за таблицами и формами.')
c.h('Иконки и доступные названия')
c.p('Карта иконок и React registry находятся в 03_icons/ui. Контекстные Stethoscope, Sparkles, Waves, Dumbbell и Plane помогают обозначить сферу, но не заменяют фирменный знак. Кнопкам только с иконкой задают понятное доступное имя. Если изображение дублирует видимый текст, его alt оставляют пустым; самостоятельному логотипу дают название бренда или продукта.')
c.h('Рекомендации для текстов')
c.p('Этот раздел задаёт редакционную рекомендацию для внедрения, а не новую визуальную концепцию. Пишите спокойно, конкретно и доброжелательно. Называйте действие и следующий шаг. Избегайте обещаний, которые продукт не выполняет, и декоративных восклицаний.')
c.table(['Контекст','Пример'],[['Кнопка','Сохранить запись'],['Успех','Запись сохранена'],['Ошибка','Не удалось сохранить запись. Попробуйте ещё раз.'],['Пустой список','Записей пока нет. Создайте первую запись.']])
c.save()

c=Chapter('05-developer-handoff','05. Подключение и внедрение')
c.p('Пакет содержит ресурсы и базовые токены, а не готовую библиотеку всех компонентов. Пример ниже показывает схему подключения. Пути заменяются на пути ресурсов в конкретном приложении.')
c.h('Тема и продукт')
c.code('''<html lang="ru" data-theme="light" data-product="fitness">
  <head>
    <link rel="stylesheet" href="/brand/taktera.tokens.css">
  </head>
  <body>
    <a href="/" aria-label="Taktera Fitness — главная">
      <img src="/brand/fitness-light.svg" width="200"
           alt="" style="display:block;max-width:100%;height:auto">
    </a>
    <button class="tk-primary tk-focus">Сохранить запись</button>
  </body>
</html>''','html')
c.p('data-theme и data-product рекомендуется ставить на один корневой элемент. Допустимые продукты: platform, clinic, beauty, spa, fitness, travel. При переключении темы меняются и токены, и файл логотипа light/dark: CSS-токены не перекрашивают содержимое SVG, подключённого через img. Размер и охранное поле логотипа задаёт макет.')
c.h('Локальные шрифты')
c.code('''@font-face {
  font-family: Inter;
  src: url("/brand/fonts/Inter-Regular.ttf") format("truetype");
  font-style: normal; font-weight: 400; font-display: swap;
}
@font-face {
  font-family: Inter;
  src: url("/brand/fonts/Inter-SemiBold.ttf") format("truetype");
  font-style: normal; font-weight: 600; font-display: swap;
}
@font-face {
  font-family: Inter;
  src: url("/brand/fonts/Inter-Bold.ttf") format("truetype");
  font-style: normal; font-weight: 700; font-display: swap;
}
body { font-family: Inter, Arial, sans-serif; }
.amount { font-variant-numeric: tabular-nums; }''','css')
c.h('Контракт токенов')
c.p('04_tokens/taktera.tokens.json содержит палитру, геометрию и параметры UI. CSS содержит переменные и небольшие вспомогательные классы. .tk-primary задаёт цвета, но не все размеры, состояния и поведение кнопки. .tk-focus задаёт видимый focus-visible. .tk-brand-mark, .tk-brand-dot и .tk-product-name задают цвет соответствующих частей для компонентов, которые поддерживают такое подключение.')
c.p('В inline SVG используйте stroke="var(--tk-mark)" для основного контура и fill="var(--tk-accent)" для точки. Не применяйте один общий fill или CSS-фильтр ко всему продуктовому логотипу: это уничтожит разделение чёрно-белого знака и цветных элементов. Подпись берётся из готовых контуров.')
c.h('Порядок внедрения')
c.li(['Скопировать ресурсы и сохранить лицензию Inter. Подключить токены и шрифт в одном общем месте.', 'Добавить тему и продукт на общий корневой элемент. Проверить логотип и кнопки во всех 12 сочетаниях продукта и темы.', 'Заменить логотипы, favicon и app icons. ICO использовать там, где требуется именно этот формат.', 'Обновить письма, PDF-документы, Open Graph, установщик и стартовые экраны.', 'Проверить формы, таблицы, состояния, фокус, адаптивность и доступные названия.', 'Удалять старые ресурсы только после проверки оставшихся ссылок. Выпускать с возможностью возврата предыдущего набора.'])
c.p('07_migration/IMPLEMENTATION-MAP.md содержит предполагаемые точки замены из прежней документации. Эти пути не подтверждены проверкой текущего репозитория. Перед изменением кода разработчик должен сопоставить их с фактической структурой проекта.')
c.h('Письма и внешние сервисы')
c.p('Для почтовых шаблонов используйте PNG с указанным размером и текстовым alt. Для SVG сначала проверьте поддержку целевой среды. Прозрачный белый логотип должен находиться на явно заданной тёмной подложке. Ресурсы для production размещают по доступным адресам; локальные пути из пакета не вставляют в отправляемые письма.')
c.save()

c=Chapter('06-designer-and-print-handoff','06. Передача дизайнеру и подготовка носителей')
c.h('Сборка макета')
c.li(['Импортируйте нужный SVG из 02_logos. Сохраните пропорции и охранное поле.', 'Создайте стили цвета из 04_tokens. Разделите фирменный акцент, текст на акценте и семантические статусы.', 'Подключите Inter из 05_typography. Логотипы оставляйте в контурах.', 'Для светлого и тёмного макета используйте соответствующие версии, включая акцент продукта.', 'Перед передачей укажите продукт, тему, размер носителя, формат и версию 3.2.'])
c.h('Готовые шаблоны')
c.table(['Файл в 06_templates','Содержание','Что требуется перед выпуском'],[['business-card-front.svg / png','Лицевая сторона визитки','Контакты, оборот, финальный формат и параметры печати'],['email-header.svg / png','Шапка письма Clinic','Проверка почтового шаблона и доступного URL'],['opengraph-1200x630.svg / png','Корпоративная карточка 1200 × 630','При необходимости — заголовок и контент конкретной страницы']])
c.p('SVG являются редактируемыми исходниками, PNG — растровыми экспортами. Это базовые шаблоны, а не полный набор заполненных носителей для каждого направления. Изменение подписи продукта выполняют заменой готовой композиции, а не перекрашиванием всего логотипа.')
c.h('Печать')
c.p('HEX в комплекте задаёт экранные цвета sRGB. Универсальные CMYK и Pantone не закреплены. Перед тиражом типография или дизайнер выполняет преобразование под конкретный ICC-профиль, материал и способ печати; результат проверяют цветопробой. Это особенно важно для жёлтого Travel и насыщенного красного Fitness.')
c.p('Размер вылетов, безопасные поля реза, цветовой профиль и требования к PDF согласуют с типографией. Существующие SVG/PNG и PDF брендбука не объявляются готовыми тиражными файлами. Для одноцветного воспроизведения используется чёрная или белая композиция без полутоновой имитации продуктового цвета.')
c.h('Новые направления')
c.p('Для нового направления сохраняют форму, положение точки и типографику. Новый цвет проверяют рядом со всей текущей семьёй в обеих темах и в реальном интерфейсе. После согласования одновременно добавляют логотипы, app icons, токены, правила текста на акценте и запись в документации. Не назначайте цвет только по свободному оттенку на палитре.')
c.save()

c=Chapter('07-assets-and-maintenance','07. Каталог ресурсов и сопровождение')
c.table(['Каталог','Содержимое'],[['01_brandbook','14-страничный PDF и общий обзор продуктовой семьи'],['02_logos/master','Корпоративные композиции и отдельный знак; SVG и прозрачные PNG'],['02_logos/products','6 продуктов, 2 темы, английские и русские композиции и знаки'],['03_icons/app','Иконки приложений: SVG, PNG и ICO'],['03_icons/ui','Карта Lucide и React registry'],['04_tokens','CSS и JSON'],['05_typography','Inter и OFL'],['06_templates','Визитка, письмо Clinic, Open Graph'],['07_migration','Карта предполагаемых мест внедрения'],['08_reference','Выбранный растровый образец и архив прежней документации'],['09_source','Скрипты сборки и проверки'],['10_documentation','Полное руководство по разделам, каталог и проверка контраста']])
c.h('Имена файлов')
c.table(['Шаблон имени','Пример / назначение'],[['{product}-{theme}.svg','fitness-light.svg — полная композиция для светлого фона'],['{product}-mark-{theme}.svg','travel-mark-dark.svg — знак и точка для тёмного фона'],['{product}-{theme}-{size}.png','travel-dark-512.png — app icon 512 × 512'],['{product}-{theme}.ico','clinic-light.ico — иконка Windows/favicon'],['taktera-{theme}.svg','Корпоративный логотип'],['mark-mono-{theme}.svg','Монохромный знак']])
c.p('Для app icons доступны размеры 16, 24, 32, 48, 64, 128, 256, 512, 1024 px. Логотипы PNG прозрачные, app icons имеют собственную подложку. Полный машиночитаемый каталог ресурсов находится в ASSET-CATALOG.csv; контрольные суммы всех файлов — в PACKAGE-MANIFEST.json в корне.')
c.h('Обновления')
c.p('В версии 3.2 закреплена красная палитра Fitness и жёлтая Travel. Редакция 3.2 добавляет русские логотипы и метки в app icons без изменения геометрии знака и палитры. При последующих изменениях обновляйте JSON/CSS, экспорты, брендбук и CHANGELOG вместе. Старый комплект храните отдельно с его номером версии.')
c.p('В 09_source включены скрипты генерации, визуального экспорта, дополнения документации и проверки. Они отражают среду сборки автора и содержат локальные пути. Перед запуском на другом компьютере пути и зависимости настраиваются; сборка не является переносимой командой «в один клик». Генератор брендбука перезаписывает часть файлов, поэтому полную документацию собирают после него.')
c.save()

c=Chapter('08-release-checklist','08. Проверка перед выпуском и границы комплекта')
c.h('Дизайн и ресурсы')
c.li(['[ ] Выбран актуальный мастер из 02_logos, а не изображение из 08_reference.', '[ ] Основной знак чёрный или белый; точка и название продукта одного цвета.', '[ ] Fitness красный, Travel жёлтый; тема ресурса соответствует фону.', '[ ] Сохранены пропорции, охранное поле и минимальный размер.', '[ ] Логотипы не пересобраны обычным текстом; шрифтовая лицензия сохранена.'])
c.h('Интерфейс')
c.li(['[ ] Проверены 6 продуктов в светлой и тёмной темах.', '[ ] На жёлтой кнопке Travel тёмный текст; мелкие светлые UI-ссылки Travel используют #806300.', '[ ] Мелкий акцентный текст Spa и Fitness не размещён на paper; проверены фактические фон и непрозрачность текста.', '[ ] Ошибка и предупреждение имеют текст или иконку; их смысл не зависит от цвета бренда.', '[ ] Проверены hover, pressed, disabled, focus, loading и сообщения об ошибках.', '[ ] Есть управление с клавиатуры, видимый фокус и доступные названия.', '[ ] Проверены ширины 360 / 390 / 768 / 1215 / 1280 / 1920 px и увеличение текста.', '[ ] Логотипы корректны в письмах, документах, приложении и установщике.'])
c.h('Передача и выпуск')
c.li(['[ ] Используется единая версия 3.2 в документации, токенах и ресурсах.', '[ ] Проверены ссылки и отсутствие старых используемых файлов Nexus.', '[ ] Печатные материалы получили отдельную подготовку под требования типографии.', '[ ] Проверена сборка самого приложения; сохранена возможность отката.'])
c.h('Что проверено в комплекте')
c.p('Отчёт VALIDATION.json фиксирует проверки самого набора: наличие локальных ссылок, SVG-контуры букв, прозрачность PNG, загрузку HTML-ресурсов и шрифта, вёрстку 14 страниц брендбука и PDF. DOCUMENTATION-VALIDATION.json отдельно фиксирует ссылки и отображение полного руководства. COLOR-CONTRAST.json содержит расчётные пары цветов. Эти результаты не заменяют проверку конкретного приложения.')
c.h('Что ещё относится к работе команды внедрения')
c.p('Полная библиотека состояний компонентов, палитра статусов, графики, готовые макеты всех экранов, макет Figma, production-код, заполненные печатные носители и проверка товарного знака не входят в выполненную работу. Для них в руководстве указаны правила и точки проверки, но готовность этих материалов не заявляется.')
c.save()


c=Chapter('09-localization-and-app-labels','09. Русские подписи и метки приложений')
c.p('Русская полная композиция: знак + точка + taktera + русское название направления. Знак и taktera чёрные или белые; точка и направление имеют один продуктовый цвет. Английская краткая семья сохраняется.')
c.table(['ID продукта','Русская подпись','Метка'],[[k,'taktera '+v,tokens['localization']['appCodes'][k]] for k,v in tokens['localization']['ru'].items()])
c.p('Русские SVG и PNG: 02_logos/products/ru. Минимальная рекомендуемая ширина полной русской композиции — 280 px, в печати — 55 мм. В интерфейсе подписи локализуются; product ID и адреса ресурсов не переводятся.')
c.h('Иконки приложений')
c.p('Под точкой размещена цветная метка PL, CL, BE, SP, FI или TR. Центр по x=95, базовая линия y=89 в области 128 × 128; Inter Bold 20, буквы в контурах. Цвет совпадает с точкой. Метки латинские и одинаковые для обеих локалей.')
c.p('PNG 32–1024 px содержат метку. На 16/24 px и соответствующих слоях ICO используется микро-версия без букв. В 32/48 px метка не считается надёжным самостоятельным различием; от 64 px служит дополнительной подсказкой. В меню выбора полные названия обязательны при любом размере. Жёлтая метка Travel на светлом фоне имеет невысокий контраст и не заменяет название.')
c.p('В отдельно устанавливаемых приложениях задайте локализованные имена ярлыков: Taktera Клиника, Taktera Фитнес и т. д. Макеты проверены в растровых размерах; отдельно проверьте launcher-маски, ярлыки ОС и системное масштабирование в целевой среде.')
c.save()

# Inventory of distributable visual resources, excluding historical reference.
assets=[]
for folder in ['02_logos','03_icons/app','06_templates']:
    for p in sorted((ROOT/folder).rglob('*')):
        if p.is_file() and p.suffix.lower() in ['.svg','.png','.ico']:
            assets.append([p.relative_to(ROOT).as_posix(),p.suffix[1:],p.stat().st_size,'transparent logo' if folder=='02_logos' else 'app icon' if folder=='03_icons/app' else 'template'])
with (DOC/'ASSET-CATALOG.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['path','format','bytes','purpose']);w.writerows(assets)
pairs=[]
for k,v in tokens['products'].items():
    for label,fg,bg in [('light button',v['onAccentLight'],v['accentLight']),('dark button',v['onAccentDark'],v['accentDark']),('light UI white',v['uiTextLight'],'#FFFFFF'),('light UI paper',v['uiTextLight'],'#F4F3EF'),('dark UI canvas',v['uiTextDark'],'#151719'),('dark UI surface',v['uiTextDark'],'#22262B')]:
        r=contrast(fg,bg);pairs.append(dict(product=k,role=label,foreground=fg,background=bg,ratio=round(r,3),meetsInternalTextThreshold=r>=4.5))
(DOC/'COLOR-CONTRAST.json').write_text(json.dumps({'method':'sRGB relative luminance; opaque colors; internal normal-text threshold 4.5:1','pairs':pairs},ensure_ascii=False,indent=2),encoding='utf-8')

nav=''.join(f'<a href="#{c.slug}">{html.escape(c.title)}</a>' for c in chapters)
body=''.join(f'<section id="{c.slug}">'+''.join(c.ht)+f'<p class="source-link"><a href="10_documentation/{c.slug}.md">Скачать этот раздел · Markdown</a></p></section>' for c in chapters)
family=''.join(f'<div class="brand"><img src="02_logos/products/ru/svg/{k}-ru-light.svg" alt="Taktera {k}"/><span>{v["accentLight"]}</span></div>' for k,v in tokens['products'].items())
page='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Taktera — полная документация 3.2</title><style>
@font-face{font-family:Inter;src:url('05_typography/Inter-Regular.ttf')}@font-face{font-family:Inter;src:url('05_typography/Inter-SemiBold.ttf');font-weight:600}@font-face{font-family:Inter;src:url('05_typography/Inter-Bold.ttf');font-weight:700}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:#F4F3EF;color:#22262B;font:15px/1.65 Inter,Arial,sans-serif}a{color:#50556B;text-underline-offset:3px}a:focus-visible{outline:2px solid #50556B;outline-offset:4px}header{background:#151719;color:#fff;padding:58px max(28px,calc((100vw - 1280px)/2));}header img{width:195px}header .meta{font-size:12px;color:#B9BEC5;margin:22px 0 10px}h1{font-size:44px;line-height:1.13;letter-spacing:-.035em;margin:0 0 18px;max-width:800px}header p{max-width:760px;color:#D9DCDF}header .actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:25px}.actions a{background:#fff;color:#22262B;padding:11px 18px;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600}.actions a.secondary{background:#30343B;color:#fff}.layout{display:grid;grid-template-columns:245px minmax(0,1fr);gap:40px;max-width:1280px;margin:36px auto;padding:0 24px}aside{align-self:start;position:sticky;top:24px;font-size:12px}aside b{display:block;margin-bottom:15px}aside a{display:block;margin-bottom:13px;text-decoration:none}main{min-width:0}.family{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:28px}.brand{background:#fff;border:1px solid #E4E3DF;border-radius:12px;padding:22px 18px;min-width:0}.brand img{width:100%;height:38px;object-fit:contain;object-position:left}.brand span{display:block;font-size:11px;color:#62676E;margin-top:13px}section{background:#fff;border-radius:14px;padding:34px 38px;margin-bottom:22px}h2{font-size:26px;line-height:1.25;margin:0 0 22px;letter-spacing:-.025em}h3{font-size:18px;line-height:1.4;margin:29px 0 12px}p{margin:0 0 16px}li{margin-bottom:9px}ul{padding-left:21px}.table-wrap{overflow-x:auto;margin-bottom:20px}table{width:100%;border-collapse:collapse;font-size:12px;line-height:1.55}th,td{padding:12px 10px;text-align:left;vertical-align:top;border-bottom:1px solid #E3E4E6;overflow-wrap:anywhere}th{font-weight:600;background:#F4F3EF}pre{background:#151719;color:#F4F3EF;border-radius:10px;padding:20px;overflow:auto;font-size:12px;line-height:1.6}.source-link{margin-top:24px;font-size:12px}.downloads{display:flex;flex-wrap:wrap;gap:16px;font-size:12px;margin:22px 0}footer{max-width:1280px;margin:30px auto;padding:0 24px 30px;color:#62676E;font-size:12px}@media(max-width:850px){.layout{grid-template-columns:1fr;gap:20px}aside{position:static;display:grid;grid-template-columns:1fr 1fr;gap:4px 20px}aside b{grid-column:1/-1}.family{grid-template-columns:repeat(2,1fr)}section{padding:25px 20px}h1{font-size:33px}h2{font-size:24px}header{padding:35px 24px}}@media print{header{background:#fff;color:#22262B;padding:10px}header p,header .meta{color:#22262B}header img,aside,.actions,.source-link{display:none!important}.layout{display:block;margin:0;padding:0}body{background:#fff;font-size:11px}section{padding:12px 0;break-before:page}h2,h3{break-after:avoid}tr,.brand{break-inside:avoid}pre{white-space:pre-wrap;color:#22262B;background:#F4F3EF}footer{padding:0}}
</style></head><body><header><img src="02_logos/master/svg/taktera-dark.svg" alt="Taktera"><div class="meta">ЕДИНЫЙ КОМПЛЕКТ · V3.2 · 18 ОКТЯБРЯ 2026</div><h1>Брендбук RU / EN и документация</h1><p>Одна форма знака. Чёрная или белая T. Цветные точка и название направления. Русские подписи и метки приложений. Fitness — красный, Travel — жёлтый.</p><div class="actions"><a href="Taktera-brandbook-v3.2.html">Визуальный брендбук</a><a href="01_brandbook/Taktera-brandbook-v3.2.pdf">Брендбук PDF · 14 страниц</a><a class="secondary" href="10_documentation/FULL-DOCUMENTATION.md">Всё руководство · Markdown</a></div></header><div class="layout"><aside><b>Содержание</b>'''+nav+'''<div class="downloads"><a href="10_documentation/ASSET-CATALOG.csv">Каталог ресурсов CSV</a><a href="04_tokens/taktera.tokens.json">Токены JSON</a><a href="04_tokens/taktera.tokens.css">Токены CSS</a><a href="VALIDATION.json">Проверка комплекта</a></div></aside><main><div class="family">'''+family+'</div>'+body+'''</main></div><footer>Taktera · 3.2 · Офлайн-комплект. Рабочие ресурсы — в каталогах 02–06. Исторические материалы — в 08_reference.</footer></body></html>'''
(ROOT/'START-HERE.html').write_text(page,encoding='utf-8')
(DOC/'FULL-DOCUMENTATION.md').write_text('# Taktera · Полная документация 3.2\n\n18 октября 2026. Все главы доступны отдельно в этом каталоге.\n\n'+'\n\n---\n\n'.join('\n'.join(c.md) for c in chapters),encoding='utf-8')
(ROOT/'README.md').write_text('''# Taktera Brand Package · 3.2

Полный актуальный комплект · 18 октября 2026.

Начните с [START-HERE.html](START-HERE.html): единое офлайн-руководство с навигацией, палитрой, правилами, примерами подключения и ссылками на ресурсы.

- [Визуальный брендбук](Taktera-brandbook-v3.2.html)
- [Брендбук PDF, 14 страниц](01_brandbook/Taktera-brandbook-v3.2.pdf)
- [Полная документация Markdown](10_documentation/FULL-DOCUMENTATION.md)
- [Каталог графических ресурсов CSV](10_documentation/ASSET-CATALOG.csv)
- [CSS](04_tokens/taktera.tokens.css) и [JSON](04_tokens/taktera.tokens.json)

## Главное

Основной знак — чёрный или белый. Точка и строчное название продукта — одного акцентного цвета. Fitness — красный #D52B35 / #FF6B75; Travel — жёлтый #D4A600 / #FFD43B. Светлая кнопка Travel имеет тёмный текст; для мелкого UI-текста на светлом фоне используется #806300.

Источник формы — последний выбранный макет exec-2c59ddad. SVG — оптическая реконструкция, буквы переведены в контуры. Суффиксы light/dark обозначают тему фона, для которой подготовлен ресурс.

## Для команды

Дизайнеру: главы 1–4 и 6, каталоги 02_logos, 05_typography, 06_templates. Разработчику: главы 3–5 и 8, токены и карта внедрения. Руководителю: принятые решения и чек-лист выпуска. Каталог 08_reference — только источник и история.

Редакция 3.2 добавляет русские подписи и метки приложений, сохраняя палитру и геометрию. Пакет не меняет код приложения. Печатная подготовка и проверка товарного знака остаются отдельными работами. Подробные границы комплекта приведены в главе 8.

PACKAGE-MANIFEST.json содержит SHA256 файлов. VALIDATION.json — проверку брендбука и ресурсов; DOCUMENTATION-VALIDATION.json — проверку полного HTML-руководства. ZIP необходимо распаковать целиком, сохранив структуру папок.
''',encoding='utf-8')
changelog=ROOT/'CHANGELOG.md'
old=changelog.read_text(encoding='utf-8')
if 'Полная документация' not in old:
    changelog.write_text(old+'\n## Полная документация · 18.10.2026\n- Добавлены единый START-HERE.html и 9 подробных разделов Markdown.\n- Добавлены примеры подключения, передача дизайнеру, каталог ресурсов и чек-лист выпуска.\n- Уточнены роли цвета Travel и ограничение мелкого зелёного текста Spa на фоне paper.\n- Добавлен расчёт контраста COLOR-CONTRAST.json; палитра и геометрия не изменены.\n',encoding='utf-8')
(ROOT/'09_source/README.md').write_text('''# Исходники сборки

Скрипты отражают среду сборки автора и содержат абсолютные пути. Перед повторным запуском настройте ROOT/OLD/REF, путь QA, исполняемые файлы и зависимости под вашу систему. Это документация воспроизводимости, а не переносимая сборка без настройки.

Порядок:
1. build_revision.py — редакция 3.2 на основе сохранённого пакета 3.1 и его скриптов. Требует настройки BASE и путей к исходной редакции; создаёт векторы и HTML.
2. render_brandbook.cjs — PNG и PDF, браузерная проверка вёрстки брендбука.
3. complete_documentation.py — полное руководство, START-HERE.html, каталог и контраст.
4. check_documentation.cjs — проверка ссылок и отображения полного руководства.
5. check_package.py — проверки ресурсов, манифест и итоговый ZIP.

Зависимости: Python, fontTools 4.61.1, Pillow, pypdf; Node, sharp, Playwright и Chromium. Inter и исходный выбранный растр входят в пакет. Исторический исходник v2.2 сохранён как текст в 08_reference. После изменения графики PDF и PNG пересоздаются, затем повторяется визуальная проверка. При изменении только документации повторный экспорт графики не нужен.
''',encoding='utf-8')
shutil.copy2(__file__,ROOT/'09_source/complete_documentation.py')
print(json.dumps({'chapters':len(chapters),'assets':len(assets),'contrastPairs':len(pairs),'entry':str(ROOT/'START-HERE.html')},ensure_ascii=False))
