// Данные о клиниках Бишкека
const CLINICS_DATA = {
    state: [
        {
          name: "Центр семейной медицины №6",
          coordinates: [42.839125, 74.614220],
          address: "ул. Жукеева-Пудовкина, 75",
          type: "state"
      },
      {
          name: "Центр семейной медицины №4",
          coordinates: [42.882851, 74.617665],
          address: "микрорайон Восток-5, 40",
          type: "state"
      },
      {
          name: "Центр семейной медицины №7",
          coordinates: [42.871167, 74.596168],
          address: "ул. Тоголок Молдо, 3/1",
          type: "state"
      },
      {
          name: "Центр семейной медицины №3",
          coordinates: [42.882252, 74.598934],
          address: "ул. Якова Логвиненко, 30/1",
          type: "state"
      },
      {
          name: "Центр семейной медицины №2",
          coordinates: [42.852697, 74.582113],
          address: "3-я линия, 25/1",
          type: "state"
      }
      ],
      private: [
        {
          name: "Медицинский центр \"Авиценна\"",
          coordinates: [42.845544, 74.577201],
          address: "ул. Анарбека Бакаева, 106",
          type: "private"
      },
      {
          name: "Amanat Hospital",
          coordinates: [42.877741, 74.584659],
          address: "ул. Турусбекова, 88/1",
          type: "private"
      },
      {
          name: "Медицинский центр \"Mediland\"",
          coordinates: [42.848207, 74.587998],
          address: "ул. Айни, 20",
          type: "private"
      },
      {
          name: "Клиника \"Он Клиник\"",
          coordinates: [42.869805, 74.612576],
          address: "ул. Усенбаева, 44",
          type: "private"
      },
      {
          name: "Медицинский центр \"ЮРФА\"",
          coordinates: [42.872851, 74.593864],
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