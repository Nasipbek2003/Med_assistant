// Инициализация карты
let myMap;
let searchControl;

function init() {
    // Создаем карту с центром в Бишкеке
    myMap = new ymaps.Map('map', {
        center: [42.8746, 74.5698], // Координаты Бишкека
        zoom: 12,
        controls: ['zoomControl', 'fullscreenControl']
    });

    // Создаем поисковый элемент управления
    searchControl = new ymaps.control.SearchControl({
        options: {
            float: 'right',
            floatIndex: 100,
            noPlacemark: true
        }
    });

    // Добавляем поисковый элемент на карту
    myMap.controls.add(searchControl);

    // Функция поиска частных клиник в Бишкеке
    function searchPrivateClinics() {
        // Очищаем предыдущие результаты
        myMap.geoObjects.removeAll();

        // Создаем поисковый запрос для частных клиник в Бишкеке
        const searchQuery = 'частная клиника Бишкек';
        
        // Выполняем поиск
        ymaps.geocode(searchQuery, {
            results: 50
        }).then(function (res) {
            // Получаем первый результат поиска
            const firstGeoObject = res.geoObjects.get(0);
            
            if (firstGeoObject) {
                // Центрируем карту на результатах поиска
                const bounds = firstGeoObject.properties.get('boundedBy');
                myMap.setBounds(bounds, {
                    checkZoomRange: true
                });

                // Добавляем метки для каждой найденной клиники
                res.geoObjects.each(function (geoObject) {
                    const coords = geoObject.geometry.getCoordinates();
                    const name = geoObject.properties.get('name');
                    const address = geoObject.properties.get('metaDataProperty.GeocoderMetaData.text');

                    // Создаем метку
                    const placemark = new ymaps.Placemark(coords, {
                        balloonContent: `
                            <h3>${name}</h3>
                            <p>${address}</p>
                        `
                    }, {
                        preset: 'islands#blueMedicalIcon'
                    });

                    // Добавляем метку на карту
                    myMap.geoObjects.add(placemark);
                });
            }
        });
    }

    // Добавляем кнопку поиска на карту
    const searchButton = new ymaps.control.Button({
        data: {
            content: 'Частные клиники в Бишкеке',
            title: 'Поиск частных клиник в Бишкеке'
        },
        options: {
            selectOnClick: false,
            position: {
                top: 10,
                left: 10
            }
        }
    });

    // Обработчик нажатия на кнопку
    searchButton.events.add('click', searchPrivateClinics);

    // Добавляем кнопку на карту
    myMap.controls.add(searchButton);
}

// Запускаем инициализацию карты после загрузки API
ymaps.ready(init); 