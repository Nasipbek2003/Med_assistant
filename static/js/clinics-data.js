// Данные о клиниках Бишкека
const CLINICS_DATA = {
    state: [
      {
        name: "Центр семейной медицины №6",
        coordinates: [42.8745, 74.5691],
        address: "ул. Жукеева-Пудовкина, 75",
        type: "state"
    },
    {
        name: "Центр семейной медицины №4",
        coordinates: [42.8740, 74.6050],
        address: "микрорайон Восток-5, 40",
        type: "state"
    },
    {
        name: "Центр семейной медицины №7",
        coordinates: [42.8792, 74.5915],
        address: "ул. Тоголок Молдо, 3/1",
        type: "state"
    },
    {
        name: "Центр семейной медицины №3",
        coordinates: [42.8728, 74.5823],
        address: "ул. Якова Логвиненко, 30/1",
        type: "state"
    },
    {
        name: "Центр семейной медицины №2",
        coordinates: [42.8705, 74.5800],
        address: "3-я линия, 25/1",
        type: "state"
    }
    ],
    private: [
      {
        name: "Медицинский центр \"Авиценна\"",
        coordinates: [42.8720, 74.5900],
        address: "ул. Анарбека Бакаева, 106",
        type: "private"
    },
    {
        name: "Amanat Hospital",
        coordinates: [42.8785, 74.5828],
        address: "ул. Турусбекова, 88/1",
        type: "private"
    },
    {
        name: "Медицинский центр \"Mediland\"",
        coordinates: [42.8743, 74.6002],
        address: "ул. Айни, 20",
        type: "private"
    },
    {
        name: "Клиника \"Он Клиник\"",
        coordinates: [42.8760, 74.5835],
        address: "ул. Усенбаева, 44",
        type: "private"
    },
    {
        name: "Медицинский центр \"ЮРФА\"",
        coordinates: [42.8790, 74.5905],
        address: "ул. Токтогула, 135",
        type: "private"
    }
    ]
};

// Функция для получения всех клиник
function getAllClinics() {
    return [...CLINICS_DATA.state, ...CLINICS_DATA.private];
}

// Функция для получения клиник по типу
function getClinicsByType(type) {
    return CLINICS_DATA[type] || [];
} 